import asyncio
from typing import Awaitable, Callable, Optional, TypeVar

from aiogram.exceptions import (
    TelegramNetworkError,
    TelegramRetryAfter,
)

from config import logger

T = TypeVar("T")


async def with_telegram_retry(
    operation: Callable[[], Awaitable[T]],
    attempts: int = 4,
) -> T:
    """Retry Telegram calls on FloodWait and short network errors."""
    last_error: Optional[Exception] = None

    for attempt in range(1, attempts + 1):
        try:
            return await operation()
        except TelegramRetryAfter as exc:
            last_error = exc
            wait_for = min(float(exc.retry_after) + 0.5, 60.0)
            logger.warning(
                "Telegram FloodWait: sleeping %.1fs "
                "(attempt %s/%s)",
                wait_for,
                attempt,
                attempts,
            )
            await asyncio.sleep(wait_for)
        except TelegramNetworkError as exc:
            last_error = exc
            wait_for = min(2 ** attempt, 16)
            logger.warning(
                "Telegram network error: %s. "
                "Retrying in %ss (attempt %s/%s)",
                exc,
                wait_for,
                attempt,
                attempts,
            )
            await asyncio.sleep(wait_for)

    assert last_error is not None
    raise last_error
