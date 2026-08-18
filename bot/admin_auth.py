from typing import Any, Dict, Optional

from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject, User

from config import ADMIN_IDS


def is_admin(
    user_id: Optional[int],
    admin_ids: Optional[frozenset[int]] = None,
) -> bool:
    if user_id is None:
        return False
    allowed = ADMIN_IDS if admin_ids is None else admin_ids
    return user_id in allowed


class AdminFilter(BaseFilter):
    async def __call__(
        self,
        event: TelegramObject,
        event_from_user: Optional[User] = None,
    ) -> bool | Dict[str, Any]:
        user_id = event_from_user.id if event_from_user else None
        return is_admin(user_id)
