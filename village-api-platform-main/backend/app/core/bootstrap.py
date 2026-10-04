"""Bootstrap the super admin account from environment variables.

Set ADMIN_EMAIL and ADMIN_PASSWORD in the environment (e.g. .env) to promote
that account to an admin at startup.  If the account does not exist yet, it is
created; if it already exists, its existing password is left untouched and the
account is simply marked as an active admin.
"""

from __future__ import annotations

from sqlalchemy import select

from app.config import settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.database import async_session
from app.models.user import User

logger = get_logger("app.core.bootstrap")


async def seed_super_admin() -> None:
    """Ensure the ADMIN_EMAIL/ADMIN_PASSWORD account is an active admin."""
    email = (settings.ADMIN_EMAIL or "").strip().lower()
    password = settings.ADMIN_PASSWORD or ""

    if not email or not password:
        return

    async with async_session() as db:
        user = (
            await db.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()

        if user is None:
            db.add(
                User(
                    email=email,
                    hashed_password=hash_password(password),
                    full_name="Administrator",
                    business_name="Village API",
                    is_admin=True,
                    is_active=True,
                    status="active",
                    plan="unlimited",
                )
            )
            await db.commit()
            logger.info("Seeded super admin account for %s", email)
            return

        changed = False
        if not user.is_admin:
            user.is_admin = True
            changed = True
        if user.status != "active":
            user.status = "active"
            changed = True
        if not user.is_active:
            user.is_active = True
            changed = True
        if changed:
            await db.commit()
            logger.info("Promoted %s to super admin", email)
        else:
            logger.info("%s is already an active admin", email)