"""
Migration: Fix gmail_message_id uniqueness to be per-user.

Previously gmail_message_id was globally unique, so only one user could ever
store a given email. Now it's unique per (user_id, gmail_message_id) so every
user can sync their own Gmail independently.

Steps:
  1. Clear all existing emails (they may be stale from the shared-credential era)
  2. Drop old global unique constraint on gmail_message_id
  3. Drop the old ix_emails_gmail_id index (if exists)
  4. Add new composite unique constraint: (user_id, gmail_message_id)

Usage:
    cd backend
    source venv/bin/activate
    python migrate_email_constraint.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings


async def migrate():
    engine = create_async_engine(settings.database_url_async, echo=False)

    print("=" * 60)
    print("Synkro Migration: Per-user gmail_message_id uniqueness")
    print("=" * 60)

    async with engine.begin() as conn:
        # 1. Clear all emails (safe to re-sync after migration)
        result = await conn.execute(text("SELECT COUNT(*) FROM emails"))
        count = result.scalar()
        print(f"\n[*] Clearing {count} existing email(s)...")
        await conn.execute(text("DELETE FROM emails"))
        print("    [OK] Emails cleared")

        # 2. Drop old global unique constraint on gmail_message_id
        #    PostgreSQL auto-names it emails_gmail_message_id_key
        try:
            await conn.execute(text(
                "ALTER TABLE emails DROP CONSTRAINT IF EXISTS emails_gmail_message_id_key"
            ))
            print("    [OK] Dropped old global unique constraint (emails_gmail_message_id_key)")
        except Exception as e:
            print(f"    [~] emails_gmail_message_id_key not found or already dropped: {e}")

        # 3. Drop old single-column index if it exists
        try:
            await conn.execute(text("DROP INDEX IF EXISTS ix_emails_gmail_id"))
            print("    [OK] Dropped old index ix_emails_gmail_id")
        except Exception as e:
            print(f"    [~] ix_emails_gmail_id: {e}")

        # 4. Add composite unique constraint (user_id, gmail_message_id)
        try:
            await conn.execute(text(
                "ALTER TABLE emails ADD CONSTRAINT uq_emails_user_gmail_id "
                "UNIQUE (user_id, gmail_message_id)"
            ))
            print("    [OK] Added composite unique constraint uq_emails_user_gmail_id")
        except Exception as e:
            # Already exists — that's fine
            print(f"    [~] uq_emails_user_gmail_id already exists or error: {e}")

    print("\n[*] Migration complete!")
    print("[*] Each user can now sync their own Gmail independently.")
    print("[*] Go to the Emails page and click 'Sync Gmail' to re-sync your emails.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())
