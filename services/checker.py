from datetime import datetime
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import (
    CHECK_INTERVAL_DAYS,
    MIN_BALANCE,
    WARNING_LIMIT,
    logger,
)
from constants import messages as msg
from database.database import db
from services.channel import remove_user, revoke_invite_link
from services.ourbit_api import ourbit
from services.telegram_retry import with_telegram_retry
from services.vip_rules import (
    is_insufficient_balance,
    is_warning_balance,
    needs_recheck,
)

scheduler = AsyncIOScheduler()


async def _safe_send(bot: Bot, telegram_id: int, text: str) -> None:
    try:
        await with_telegram_retry(
            lambda: bot.send_message(telegram_id, text)
        )
    except (TelegramBadRequest, TelegramForbiddenError) as exc:
        logger.warning(
            "Failed to send message to %s: %s",
            telegram_id,
            exc,
        )
    except Exception:
        logger.exception(
            "Unexpected send error to %s",
            telegram_id,
        )


async def weekly_check(bot: Bot) -> None:
    """
    Recheck active VIP users.

    - Skip users checked within CHECK_INTERVAL_DAYS.
    - Kick only after a successful channel removal (or if already gone).
    - Join and kick both use balance < MIN_BALANCE.
    """
    logger.info("Weekly checker started.")

    try:
        users = await db.get_all_active_users()
    except Exception:
        logger.exception("Failed to fetch active users")
        return

    if not users:
        logger.info("No active users found. Checker finished.")
        return

    total = len(users)
    processed = 0
    warned = 0
    kicked = 0
    skipped = 0

    for user in users:
        telegram_id: int = user["telegram_id"]
        uid: str = user["ourbit_uid"]

        try:
            if not needs_recheck(user["last_check"], CHECK_INTERVAL_DAYS):
                skipped += 1
                continue

            balance: Optional[float] = await ourbit.get_balance(uid)

            if balance is None:
                logger.warning(
                    "Could not fetch balance for telegram_id=%s uid=%s. Skipping.",
                    telegram_id,
                    uid,
                )
                continue

            await db.update_balance(telegram_id, balance)
            processed += 1

            if is_insufficient_balance(balance, MIN_BALANCE):
                invite_link = user["invite_link"]
                if invite_link:
                    revoked = await revoke_invite_link(bot, invite_link)
                    if not revoked:
                        logger.error(
                            "Invite revocation failed for telegram_id=%s; "
                            "leaving user active.",
                            telegram_id,
                        )
                        continue

                removed = await remove_user(bot, telegram_id)
                if not removed:
                    logger.error(
                        "Kick failed for telegram_id=%s; leaving user active.",
                        telegram_id,
                    )
                    continue

                await db.update_invite_link(telegram_id, None)
                await db.deactivate_user(telegram_id)
                kicked += 1
                logger.info(
                    "User kicked: telegram_id=%s balance=%s < %s",
                    telegram_id,
                    balance,
                    MIN_BALANCE,
                )
                await _safe_send(
                    bot,
                    telegram_id,
                    msg.KICK_MSG.format(
                        balance=balance,
                        min_balance=MIN_BALANCE,
                    ),
                )
                continue

            if is_warning_balance(balance, MIN_BALANCE, WARNING_LIMIT):
                await db.add_warning(telegram_id)
                warned += 1
                logger.warning(
                    "Warning sent: telegram_id=%s balance=%s limit=%s",
                    telegram_id,
                    balance,
                    WARNING_LIMIT,
                )
                await _safe_send(
                    bot,
                    telegram_id,
                    msg.WARNING_MSG.format(
                        balance=balance,
                        min_balance=MIN_BALANCE,
                    ),
                )
            elif user["warning_count"] and user["warning_count"] > 0:
                await db.reset_warnings(telegram_id)
                logger.info(
                    "Warnings reset for telegram_id=%s (balance=%s > %s)",
                    telegram_id,
                    balance,
                    WARNING_LIMIT,
                )

        except Exception:
            logger.exception(
                "Checker error for telegram_id=%s. Continuing.",
                telegram_id,
            )
            continue

    logger.info(
        "Weekly checker finished. Total=%s Processed=%s "
        "Skipped=%s Warned=%s Kicked=%s.",
        total,
        processed,
        skipped,
        warned,
        kicked,
    )


def start_scheduler(bot: Bot) -> None:
    scheduler.add_job(
        weekly_check,
        "interval",
        days=CHECK_INTERVAL_DAYS,
        args=[bot],
        id="weekly_checker",
        replace_existing=True,
        next_run_time=datetime.now(),
    )
    scheduler.start()
    logger.info(
        "Scheduler started. Interval: every %s day(s). First run is immediate.",
        CHECK_INTERVAL_DAYS,
    )


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
