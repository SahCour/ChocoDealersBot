from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger


class AuthMiddleware:
    async def __call__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user:
            logger.debug(f"Update from user {update.effective_user.id}")
