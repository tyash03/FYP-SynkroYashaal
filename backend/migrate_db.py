"""
Database migration script for role hierarchy update.
Run this once to:
1. Add new role values to the UserRole enum
2. Add password reset columns to users table
3. Delete all existing users (fresh start)

Usage:
    cd backend
    source venv/bin/activate
    python migrate_db.py
"""
import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings


async def migrate():
    engine = create_async_engine(settings.database_url_async, echo=False)

    db_url = settings.DATABASE_URL

    if "postgresql" in db_url:
        print("[*] PostgreSQL detected - running migrations...")

        # Step 1: Add new enum values (must be in their own transaction)
        new_roles = [
            'admin',
            'project_manager',
            'team_lead',
            'senior_developer',
            'developer',
            'intern'
        ]

        async with engine.begin() as conn:
            for role in new_roles:
                try:
                    await conn.execute(text(
                        f"ALTER TYPE userrole ADD VALUE IF NOT EXISTS '{role}'"
                    ))
                    print(f"    [OK] Added role: {role}")
                except Exception as e:
                    print(f"    [!] Role '{role}': {e}")

        print("    [OK] Enum values committed")

        # Step 2: Add password reset columns and delete users (new transaction)
        async with engine.begin() as conn:
            try:
                await conn.execute(text(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
                    "password_reset_token VARCHAR(255)"
                ))
                print("    [OK] Added column: password_reset_token")
            except Exception as e:
                print(f"    [!] password_reset_token: {e}")

            try:
                await conn.execute(text(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
                    "password_reset_expires TIMESTAMP"
                ))
                print("    [OK] Added column: password_reset_expires")
            except Exception as e:
                print(f"    [!] password_reset_expires: {e}")

            # Count and delete all users
            result = await conn.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            print(f"\n    [*] Found {count} existing user(s) - deleting all...")

            await conn.execute(text("DELETE FROM users"))
            print(f"    [OK] Deleted {count} users")

            # Clean up orphaned teams (no members)
            await conn.execute(text(
                "DELETE FROM teams WHERE id NOT IN "
                "(SELECT DISTINCT team_id FROM users WHERE team_id IS NOT NULL)"
            ))
            print("    [OK] Cleaned up orphaned teams")

        # Step 3: Update default role (new transaction after enum commit)
        async with engine.begin() as conn:
            try:
                await conn.execute(text(
                    "ALTER TABLE users ALTER COLUMN role SET DEFAULT 'developer'"
                ))
                print("    [OK] Updated default role to 'developer'")
            except Exception as e:
                print(f"    [!] Default role update (non-critical): {e}")

        print("\n[*] Migration complete!")
        print("[*] You can now restart the backend and create fresh users.")

    elif "sqlite" in db_url:
        print("[*] SQLite detected - adding columns and cleaning users...")

        async with engine.begin() as conn:
            try:
                await conn.execute(text(
                    "ALTER TABLE users ADD COLUMN password_reset_token TEXT"
                ))
                print("    [OK] Added column: password_reset_token")
            except Exception as e:
                print(f"    [!] password_reset_token: {e}")

            try:
                await conn.execute(text(
                    "ALTER TABLE users ADD COLUMN password_reset_expires DATETIME"
                ))
                print("    [OK] Added column: password_reset_expires")
            except Exception as e:
                print(f"    [!] password_reset_expires: {e}")

            result = await conn.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            print(f"\n    [*] Found {count} existing user(s) - deleting all...")
            await conn.execute(text("DELETE FROM users"))
            print(f"    [OK] Deleted {count} users")

        print("\n[*] Migration complete!")

    else:
        print(f"[!] Unknown database type in URL: {db_url}")

    await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("Synkro Database Migration: Role Hierarchy Update")
    print("=" * 60)
    asyncio.run(migrate())
