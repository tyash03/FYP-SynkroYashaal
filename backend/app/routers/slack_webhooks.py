"""
Slack Events API webhook receiver.

Security
--------
Every incoming request is verified against the Slack signing secret using
HMAC-SHA256 before any processing occurs (see SlackService.verify_signature).

Event deduplication
-------------------
Slack may deliver the same event more than once (at-least-once delivery).
We guard against duplicate processing by checking whether a Message row with
the same external_id already exists before inserting.

url_verification challenge
--------------------------
During Slack app setup, Slack sends a one-time challenge that must be echoed
back immediately.  This is handled before signature verification to keep
setup frictionless (the challenge itself is not a security risk).

Async processing
----------------
Message intent classification and task creation are dispatched to Celery
so the webhook endpoint returns within Slack's 3-second timeout window.
"""

import logging
import time
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Integration, IntegrationPlatform, Message
from app.models.direct_message import DirectMessage
from app.models.user import User
from app.services.slack_service import SlackService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/webhooks/slack", tags=["Webhooks"])


@router.post(
    "/events",
    summary="Slack Events API endpoint",
    description=(
        "Receives Slack Events API payloads. Verifies the Slack signing secret, "
        "handles url_verification challenges, and dispatches message events to "
        "the background intent classifier."
    ),
)
async def slack_events(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Primary Slack Events API handler.

    Flow:
    1. Read raw body (needed for signature verification).
    2. Respond immediately to ``url_verification`` challenge (Slack setup).
    3. Verify HMAC-SHA256 signature against ``SLACK_SIGNING_SECRET``.
    4. Ignore bot messages and non-message event types.
    5. Look up the Integration record for the workspace (``team_id``).
    6. Deduplicate using ``Message.external_id``.
    7. Persist the Message row.
    8. Enqueue Celery task for intent classification (non-blocking).
    """
    # ── 1. Read raw body before any parsing ──────────────────────────────────
    body_bytes: bytes = await request.body()

    # ── 2. url_verification challenge (Slack app setup) ──────────────────────
    # Handle BEFORE signature check — challenge arrives before the secret is
    # configured in some app setups.  The challenge itself is harmless.
    try:
        payload: dict = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body is not valid JSON",
        )

    if payload.get("type") == "url_verification":
        logger.info("Slack url_verification challenge received")
        return {"challenge": payload.get("challenge")}

    logger.info("Slack event received: type=%s team=%s event_type=%s",
                payload.get("type"), payload.get("team_id"), payload.get("event", {}).get("type"))

    # ── 3. Signature verification ─────────────────────────────────────────────
    if not SlackService.verify_signature(dict(request.headers), body_bytes):
        logger.warning(
            "Slack webhook: rejected request with invalid signature "
            "(remote=%s)",
            request.client.host if request.client else "unknown",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Slack signature",
        )

    # ── 4. Route on event type ────────────────────────────────────────────────
    event: dict = payload.get("event", {})
    event_type: str = event.get("type", "")

    # Only process user-authored messages (skip bot posts, message edits, etc.)
    if event_type != "message" or event.get("bot_id") or event.get("subtype"):
        # Acknowledge receipt — Slack will retry if we don't return 200
        return {"ok": True}

    team_id: str = payload.get("team_id", "")
    if not team_id:
        logger.warning("Slack event payload missing team_id")
        return {"ok": True}

    # ── 5. Resolve workspace → Integration record ─────────────────────────────
    # Fetch all active Slack integrations and filter by team_id in Python
    # (avoids db-specific JSON functions like SQLite's json_extract vs Postgres's ->)
    result = await db.execute(
        select(Integration).where(
            Integration.platform == IntegrationPlatform.SLACK,
            Integration.is_active == True,
        )
    )
    all_integrations = result.scalars().all()
    integration = next(
        (i for i in all_integrations
         if (i.platform_metadata or {}).get("team_id") == team_id),
        None,
    )

    if not integration:
        logger.warning(
            "Slack event received for unknown/inactive team_id=%s", team_id
        )
        return {"ok": True}

    # ── 5b. For DM channels, route to the Synkro user who owns the channel ─────
    # Strategy 1: match by authed_user_id stored in metadata (most reliable)
    # Strategy 2: fall back to channel_id ownership from existing messages
    channel_id_evt = event.get("channel")
    channel_type_evt = event.get("channel_type")
    slack_sender_id: str = event.get("user", "")

    if channel_type_evt == "im" and len(all_integrations) > 1:
        # Try matching by the Slack user ID of whoever authorized the integration
        if slack_sender_id:
            matched = next(
                (
                    i for i in all_integrations
                    if (i.platform_metadata or {}).get("authed_user_id") == slack_sender_id
                ),
                None,
            )
            if matched:
                integration = matched
                logger.debug(
                    "DM event routed via authed_user_id=%s to user=%s",
                    slack_sender_id,
                    integration.user_id,
                )
        # Fall back: check which Synkro user has existing messages in this channel
        if not matched and channel_id_evt:
            channel_owner_result = await db.execute(
                select(Message.user_id).where(
                    Message.channel_id == channel_id_evt,
                    Message.platform == "slack",
                ).limit(1)
            )
            owner_user_id = channel_owner_result.scalar_one_or_none()
            if owner_user_id:
                matched = next(
                    (i for i in all_integrations if i.user_id == owner_user_id),
                    None,
                )
                if matched:
                    integration = matched

    # ── 6. Deduplication ──────────────────────────────────────────────────────
    # Use client_msg_id (stable) or event ts as the external identifier
    external_id: str = event.get("client_msg_id") or event.get("ts") or ""

    if external_id:
        dup_check = await db.execute(
            select(Message.id).where(
                Message.external_id == external_id,
                Message.platform == "slack",
            )
        )
        if dup_check.scalar_one_or_none():
            logger.debug(
                "Slack event deduplicated — external_id=%s already processed",
                external_id,
            )
            return {"ok": True}

    # ── 7. Persist message ────────────────────────────────────────────────────
    ts_float: float = float(event.get("ts") or time.time())

    # Resolve Slack user ID to display name
    slack_user_id: str = event.get("user", "")
    sender_display_name: str = slack_user_id
    if slack_user_id:
        try:
            slack_svc = SlackService.from_integration(integration)
            user_info = await slack_svc.get_user_info(slack_user_id)
            profile = user_info.get("profile", {})
            sender_display_name = (
                profile.get("display_name")
                or profile.get("real_name")
                or slack_user_id
            )
            await slack_svc.aclose()
        except Exception as exc:
            logger.warning("Could not resolve Slack user %s: %s", slack_user_id, exc)

    msg = Message(
        external_id=external_id or None,
        platform="slack",
        sender_email=None,
        sender_name=sender_display_name,
        content=event.get("text", ""),
        timestamp=datetime.utcfromtimestamp(ts_float),
        thread_id=event.get("thread_ts"),
        channel_id=event.get("channel"),
        channel_type=event.get("channel_type"),
        user_id=integration.user_id,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    logger.info(
        "Slack message persisted: id=%s team=%s user=%s ts=%s",
        msg.id,
        team_id,
        event.get("user"),
        event.get("ts"),
    )

    # ── 7b. For DM channels: also create a DirectMessage record ──────────────
    # This syncs user-to-user Slack DMs into Synkro's native DM system in
    # real-time when the Events API delivers message.im events.
    # Requires: user tokens with im:history (user_scope in OAuth), and each
    # user's authed_user_id stored in their Integration metadata.
    if channel_type_evt == "im" and slack_sender_id:
        # Find the Synkro user whose Slack ID matches the sender
        sender_integration = next(
            (i for i in all_integrations
             if (i.platform_metadata or {}).get("authed_user_id") == slack_sender_id),
            None,
        )
        # Find the Synkro user who owns this integration (the recipient)
        # They are the one whose user token triggered delivery of this event
        # (i.e. the integration record we resolved earlier)
        if sender_integration and sender_integration.id != integration.id:
            sender_synkro_id = sender_integration.user_id
            recipient_synkro_id = integration.user_id
        elif sender_integration and sender_integration.id == integration.id:
            # Sender IS the integration owner — other party is not tracked
            sender_synkro_id = integration.user_id
            recipient_synkro_id = None
        else:
            # Try: sender is unknown in Synkro; recipient is integration owner
            sender_synkro_id = None
            recipient_synkro_id = integration.user_id

        if sender_synkro_id and recipient_synkro_id:
            # Dedup by slack_ts
            slack_ts_val = event.get("ts", "")
            dup_dm = await db.execute(
                select(DirectMessage).where(DirectMessage.slack_ts == slack_ts_val)
            )
            if not dup_dm.scalar_one_or_none():
                dm = DirectMessage(
                    sender_id=sender_synkro_id,
                    recipient_id=recipient_synkro_id,
                    content=event.get("text", ""),
                    created_at=datetime.utcfromtimestamp(ts_float),
                    slack_ts=slack_ts_val,
                )
                db.add(dm)
                await db.commit()
                logger.info(
                    "DirectMessage created from Slack DM: sender=%s recipient=%s ts=%s",
                    sender_synkro_id,
                    recipient_synkro_id,
                    slack_ts_val,
                )

    # ── 8. Enqueue background intent classification ───────────────────────────
    # Celery task runs outside the request cycle — webhook returns immediately
    try:
        from app.tasks.meeting_tasks import process_message_for_intent
        process_message_for_intent.delay(msg.id)
        logger.debug("Intent classification enqueued for message %s", msg.id)
    except Exception as exc:
        # Celery may not be running in dev — log but don't fail the webhook
        logger.error(
            "Failed to enqueue intent classification for message %s: %s",
            msg.id,
            exc,
        )

    return {"ok": True}
