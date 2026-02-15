"""
Authentication middleware — stub for Police Mode.
Full auth will be re-added when User model is ready.
"""

from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger


class AuthMiddleware:
    """Stub middleware — passes all updates through."""

    async def __call__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user:
            logger.debug(f"Update from user {update.effective_user.id}")
