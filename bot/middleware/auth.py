"""
Authentication and authorization middleware
Checks user permissions before executing commands
"""

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select
from typing import List, Callable
from loguru import logger

from database.db import get_db
from database.models import User, UserRole, UserStatus


def require_role(allowed_roles: List[UserRole]) -> Callable:
    """
    Decorator to require specific roles for a command

    Optimized to use user data from context (loaded by AuthMiddleware)
    to avoid redundant database queries (N+1 problem fix).

    Usage:
        @require_role([UserRole.ADMIN])
        async def admin_command(update, context):
            ...

        @require_role([UserRole.MANAGER, UserRole.ADMIN])
        async def manager_command(update, context):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id

            # Try to get user from context first (set by middleware)
            user = context.user_data.get("db_user")

            # Fallback to DB if middleware didn't run (shouldn't happen in production)
            if user is None:
                logger.warning(f"User {user_id} not in context, fetching from DB (middleware may not be running)")
                async with get_db() as db:
                    stmt = select(User).where(User.telegram_id == user_id)
                    result = await db.execute(stmt)
                    user = result.scalar_one_or_none()

            if not user:
                await update.message.reply_text(
                    "❌ You are not registered in the system.\n"
                    "Contact administrator for access."
                )
                logger.warning(f"Unauthorized access attempt by user {user_id}")
                return

            if user.status != UserStatus.ACTIVE:
                await update.message.reply_text(
                    "❌ Your account is blocked.\n"
                    "Contact administrator."
                )
                logger.warning(f"Inactive user {user_id} tried to use bot")
                return

            if user.role not in allowed_roles:
                await update.message.reply_text(
                    f"❌ Insufficient permissions.\n"
                    f"Required role: {', '.join([r.value for r in allowed_roles])}\n"
                    f"Your role: {user.role.value}"
                )
                logger.warning(
                    f"User {user_id} ({user.role.value}) tried to access "
                    f"command requiring {[r.value for r in allowed_roles]}"
                )
                return

            # Execute the command
            return await func(update, context, *args, **kwargs)

        return wrapper
    return decorator


class AuthMiddleware:
    """
    Middleware for authentication and authorization
    Can be used with application.add_middleware()
    """

    async def __call__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process update and check authentication"""
        if update.effective_user:
            user_id = update.effective_user.id

            async with get_db() as db:
                stmt = select(User).where(User.telegram_id == user_id)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()

                # Store user in context for later use
                context.user_data["db_user"] = user
                context.user_data["is_authenticated"] = user is not None
                context.user_data["is_active"] = user.status == UserStatus.ACTIVE if user else False


async def check_permission(user_id: int, required_role: UserRole) -> bool:
    """
    Check if user has required permission level
    Returns True if user has required role or higher
    """
    role_hierarchy = {
        UserRole.STAFF: 1,
        UserRole.MANAGER: 2,
        UserRole.ADMIN: 3
    }

    async with get_db() as db:
        stmt = select(User).where(User.telegram_id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or user.status != UserStatus.ACTIVE:
            return False

        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 99)

        return user_level >= required_level


async def is_admin(user_id: int) -> bool:
    """Quick check if user is admin"""
    return await check_permission(user_id, UserRole.ADMIN)


async def get_user_role(user_id: int) -> UserRole | None:
    """Get user's current role"""
    async with get_db() as db:
        stmt = select(User).where(User.telegram_id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        return user.role if user else None
