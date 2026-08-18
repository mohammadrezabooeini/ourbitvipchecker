from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from config import logger
from database.database import db


class UserTrackingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[
            [TelegramObject, Dict[str, Any]],
            Awaitable[Any],
        ],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        if user is not None and not user.is_bot:
            try:
                await db.track_bot_user(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                )
            except Exception:
                logger.warning(
                    "Could not track Telegram user interaction.",
                    exc_info=True,
                )

        return await handler(event, data)
