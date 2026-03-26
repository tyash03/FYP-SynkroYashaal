"""Native in-app direct messages between team members"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from pydantic import BaseModel
from datetime import datetime, timezone

from app.database import get_db
from app.models.user import User
from app.models.direct_message import DirectMessage
from app.models.integration import Integration, IntegrationPlatform
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dm", tags=["Direct Messages"])


class SendDmRequest(BaseModel):
    recipient_id: str
    content: str


@router.get("/users")
async def list_team_members(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all team members the current user can DM."""
    result = await db.execute(
        select(User).where(
            User.team_id == current_user.team_id,
            User.id != current_user.id,
            User.is_active == True,
        )
    )
    members = result.scalars().all()
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role.value,
            "avatar_url": u.avatar_url,
        }
        for u in members
    ]


@router.get("/conversations")
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List DM conversations (one per other user), most recent first."""
    result = await db.execute(
        select(DirectMessage).where(
            or_(
                DirectMessage.sender_id == current_user.id,
                DirectMessage.recipient_id == current_user.id,
            )
        ).order_by(DirectMessage.created_at.desc())
    )
    messages = result.scalars().all()

    # Collect unique conversation partners
    seen: dict = {}
    for m in messages:
        other_id = m.recipient_id if m.sender_id == current_user.id else m.sender_id
        if other_id not in seen:
            seen[other_id] = m

    # Fetch partner user details
    conversations = []
    for other_id, last_msg in seen.items():
        user_result = await db.execute(select(User).where(User.id == other_id))
        other = user_result.scalars().first()
        if not other:
            continue
        conversations.append({
            "user_id": other.id,
            "full_name": other.full_name,
            "email": other.email,
            "avatar_url": other.avatar_url,
            "last_message": last_msg.content,
            "last_timestamp": last_msg.created_at.isoformat() + "Z",
            "is_sent": last_msg.sender_id == current_user.id,
        })

    return conversations


@router.get("/{user_id}")
async def get_conversation(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages between current user and another user."""
    # Verify the other user exists and is in the same team
    result = await db.execute(select(User).where(User.id == user_id))
    other = result.scalars().first()
    if not other or other.team_id != current_user.team_id:
        raise HTTPException(status_code=404, detail="User not found")

    msgs_result = await db.execute(
        select(DirectMessage).where(
            or_(
                and_(DirectMessage.sender_id == current_user.id, DirectMessage.recipient_id == user_id),
                and_(DirectMessage.sender_id == user_id, DirectMessage.recipient_id == current_user.id),
            )
        ).order_by(DirectMessage.created_at.asc())
    )
    messages = msgs_result.scalars().all()

    # Mark unread messages as read
    now = datetime.utcnow()
    for m in messages:
        if m.recipient_id == current_user.id and m.read_at is None:
            m.read_at = now
    await db.commit()

    return {
        "user": {
            "id": other.id,
            "full_name": other.full_name,
            "email": other.email,
            "avatar_url": other.avatar_url,
        },
        "messages": [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "content": m.content,
                "created_at": m.created_at.isoformat() + "Z",
                "is_sent": m.sender_id == current_user.id,
            }
            for m in messages
        ],
    }


@router.post("/send")
async def send_message(
    body: SendDmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a direct message to a team member."""
    result = await db.execute(select(User).where(User.id == body.recipient_id))
    recipient = result.scalars().first()
    if not recipient or recipient.team_id != current_user.team_id:
        raise HTTPException(status_code=404, detail="Recipient not found")

    msg = DirectMessage(
        sender_id=current_user.id,
        recipient_id=body.recipient_id,
        content=body.content.strip(),
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    return {
        "id": msg.id,
        "sender_id": msg.sender_id,
        "recipient_id": msg.recipient_id,
        "content": msg.content,
        "created_at": msg.created_at.isoformat() + "Z",
        "is_sent": True,
    }


@router.post("/sync-slack")
async def sync_from_slack(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pull the last 24 h of Slack DMs into Synkro using the user's Slack user token.

    Requires the user to have connected Slack via OAuth with user_scope=im:history.
    Matches the Slack DM partner to a Synkro user by email.
    """
    from app.services.slack_service import SlackService
    from app.utils.security import decrypt_value

    # 1. Find the user's Slack integration
    result = await db.execute(
        select(Integration).where(
            Integration.user_id == current_user.id,
            Integration.platform == IntegrationPlatform.SLACK,
            Integration.is_active == True,
        )
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=400, detail="Slack not connected. Go to Settings to connect.")

    metadata = integration.platform_metadata or {}
    encrypted_user_token = metadata.get("user_access_token")
    if not encrypted_user_token:
        raise HTTPException(
            status_code=400,
            detail="Slack user token not available. Please re-connect Slack via Settings to grant DM read access."
        )

    try:
        user_token = decrypt_value(encrypted_user_token)
    except Exception:
        user_token = encrypted_user_token  # fallback if not encrypted

    # 2. Fetch DM channels using the user token
    svc = SlackService(token=user_token)
    try:
        im_channels = await svc.list_im_channels()
    except Exception as exc:
        await svc.aclose()
        raise HTTPException(status_code=502, detail=f"Failed to fetch Slack DMs: {exc}")

    # 3. Build a map of slack_user_id → Synkro User (for the user's team)
    team_users_result = await db.execute(
        select(User).where(User.team_id == current_user.team_id, User.is_active == True)
    )
    team_users = team_users_result.scalars().all()

    # Resolve Slack user emails to Synkro users
    slack_user_to_synkro: dict = {}
    for channel in im_channels:
        slack_uid = channel.get("user")
        if not slack_uid or slack_uid == "USLACKBOT":
            continue
        try:
            slack_user_info = await svc.get_user_info(slack_uid)
            profile = slack_user_info.get("profile", {})
            email = profile.get("email", "").lower()
            matched = next((u for u in team_users if u.email.lower() == email), None)
            if matched:
                slack_user_to_synkro[slack_uid] = matched
        except Exception as exc:
            logger.warning("Could not resolve Slack user %s: %s", slack_uid, exc)

    # 4. For each matched DM channel, fetch messages from the last 24 h
    import time
    oldest_ts = str(time.time() - 86400)  # 24 hours ago

    synced_count = 0
    for channel in im_channels:
        slack_uid = channel.get("user")
        partner = slack_user_to_synkro.get(slack_uid)
        if not partner:
            continue
        channel_id = channel.get("id")
        try:
            messages = await svc.get_channel_messages(channel_id, limit=100, oldest=oldest_ts)
        except Exception as exc:
            logger.warning("Could not fetch messages for channel %s: %s", channel_id, exc)
            continue

        for slack_msg in messages:
            # Skip bot messages and subtypes
            if slack_msg.get("bot_id") or slack_msg.get("subtype"):
                continue
            slack_sender_id = slack_msg.get("user", "")
            ts = slack_msg.get("ts", "")
            text = slack_msg.get("text", "").strip()
            if not text or not ts:
                continue

            # Determine Synkro sender/recipient
            # The authed_user_id in integration is the current_user's Slack ID
            my_slack_id = metadata.get("authed_user_id", "")
            if slack_sender_id == my_slack_id:
                sender_id = current_user.id
                recipient_id = partner.id
            else:
                # Message was sent by the other person
                sender_id = partner.id
                recipient_id = current_user.id

            # Dedup: use Slack ts as external marker — store in content prefix check
            # Use ts as a unique key by checking if a message with same timestamp exists
            dedup_result = await db.execute(
                select(DirectMessage).where(
                    or_(
                        and_(DirectMessage.sender_id == sender_id, DirectMessage.recipient_id == recipient_id),
                        and_(DirectMessage.sender_id == recipient_id, DirectMessage.recipient_id == sender_id),
                    ),
                    DirectMessage.slack_ts == ts,
                )
            )
            if dedup_result.scalar_one_or_none():
                continue

            msg_time = datetime.utcfromtimestamp(float(ts))
            dm = DirectMessage(
                sender_id=sender_id,
                recipient_id=recipient_id,
                content=text,
                created_at=msg_time,
                slack_ts=ts,
            )
            db.add(dm)
            synced_count += 1

    await db.commit()
    await svc.aclose()

    return {"synced": synced_count, "message": f"Synced {synced_count} new Slack messages."}
