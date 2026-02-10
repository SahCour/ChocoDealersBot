"""
Admin command handlers
Only accessible by users with ADMIN role
"""

from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select
from loguru import logger

from database.db import get_db
from database.models import User, UserRole, UserStatus
from bot.middleware.auth import require_role


# ============================================
# SQUARE SYNC
# ============================================

@require_role([UserRole.ADMIN])
async def sync_square_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sync with Square POS"""
    await update.message.reply_text("🔄 Syncing with Square POS...")

    try:
        from integrations.square_api import SquareIntegration

        square = SquareIntegration()
        result = await square.sync_inventory()

        await update.message.reply_text(
            f"✅ Sync completed!\n"
            f"Synced records: {result.get('synced', 0)}"
        )
    except Exception as e:
        logger.error(f"Square sync error: {e}")
        await update.message.reply_text(f"❌ Sync error: {str(e)}")


# ============================================
# GOOGLE SHEETS SYNC
# ============================================

@require_role([UserRole.ADMIN])
async def sync_sheets_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sync with Google Sheets"""
    await update.message.reply_text("🔄 Syncing with Google Sheets...")

    try:
        from integrations.google_sheets import GoogleSheetsIntegration

        sheets = GoogleSheetsIntegration()
        result = await sheets.sync_all()

        await update.message.reply_text(
            f"✅ Sync completed!\n"
            f"Updated sheets: {result.get('sheets_updated', 0)}"
        )
    except Exception as e:
        logger.error(f"Sheets sync error: {e}")
        await update.message.reply_text(f"❌ Sync error: {str(e)}")


@require_role([UserRole.ADMIN])
async def sync_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Full sync of all systems"""
    await update.message.reply_text("🔄 Full sync of all systems...")

    # Call both sync functions
    await sync_square_command(update, context)
    await sync_sheets_command(update, context)


# ============================================
# USER MANAGEMENT
# ============================================

@require_role([UserRole.ADMIN])
async def list_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all users"""
    async with get_db() as db:
        stmt = select(User).order_by(User.role, User.first_name)
        result = await db.execute(stmt)
        users = result.scalars().all()

        if not users:
            await update.message.reply_text("❌ No users found.")
            return

        from collections import defaultdict
        by_role = defaultdict(list)

        for user in users:
            by_role[user.role].append(user)

        response = "👥 **SYSTEM USERS**\n\n"

        for role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.STAFF]:
            if role in by_role:
                response += f"**{role.value}:**\n"
                for user in by_role[role]:
                    status_emoji = "✅" if user.status == UserStatus.ACTIVE else "❌"
                    response += f"{status_emoji} {user.first_name} (@{user.telegram_id})\n"
                response += "\n"

        response += f"_Total: {len(users)} users_"

    await update.message.reply_text(response, parse_mode="Markdown")


@require_role([UserRole.ADMIN])
async def add_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Add new user
    Usage: /add_user <telegram_id> <role>
    """
    args = context.args

    if len(args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/add_user <telegram_id> <role>`\n"
            "Roles: ADMIN, MANAGER, STAFF\n"
            "Example: `/add_user 123456789 STAFF`",
            parse_mode="Markdown"
        )
        return

    try:
        telegram_id = int(args[0])
        role_str = args[1].upper()
        role = UserRole[role_str]
    except (ValueError, KeyError):
        await update.message.reply_text(
            "❌ Invalid format.\n"
            "Telegram ID must be a number.\n"
            "Role must be one of: ADMIN, MANAGER, STAFF"
        )
        return

    async with get_db() as db:
        # Check if user exists
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            await update.message.reply_text(
                f"❌ User with ID {telegram_id} is already registered."
            )
            return

        # Create new user
        new_user = User(
            telegram_id=telegram_id,
            role=role,
            status=UserStatus.ACTIVE
        )
        db.add(new_user)
        await db.commit()

        await update.message.reply_text(
            f"✅ User added!\n"
            f"Telegram ID: {telegram_id}\n"
            f"Role: {role.value}"
        )
        logger.info(f"New user added: {telegram_id} with role {role.value}")


@require_role([UserRole.ADMIN])
async def change_role_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Change user role
    Usage: /change_role <telegram_id> <new_role>
    """
    args = context.args

    if len(args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/change_role <telegram_id> <new_role>`\n"
            "Example: `/change_role 123456789 MANAGER`",
            parse_mode="Markdown"
        )
        return

    try:
        telegram_id = int(args[0])
        role_str = args[1].upper()
        new_role = UserRole[role_str]
    except (ValueError, KeyError):
        await update.message.reply_text("❌ Invalid data format.")
        return

    async with get_db() as db:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            await update.message.reply_text(f"❌ User {telegram_id} not found.")
            return

        old_role = user.role
        user.role = new_role
        await db.commit()

        await update.message.reply_text(
            f"✅ Role changed!\n"
            f"User: {user.first_name} ({telegram_id})\n"
            f"Old role: {old_role.value}\n"
            f"New role: {new_role.value}"
        )
        logger.info(f"User {telegram_id} role changed from {old_role} to {new_role}")
