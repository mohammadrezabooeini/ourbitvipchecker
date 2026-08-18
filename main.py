import asyncio

from aiogram import Bot, Dispatcher

from bot.admin_handlers import admin_router
from bot.handlers import router
from bot.middlewares import UserTrackingMiddleware
from config import BOT_TOKEN, logger
from database.database import db
from services.channel import check_bot_permissions
from services.checker import start_scheduler, stop_scheduler
from services.ourbit_api import ourbit


async def main() -> None:
    await db.init()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.update.outer_middleware(UserTrackingMiddleware())
    dp.include_router(admin_router)
    dp.include_router(router)

    has_permissions = await check_bot_permissions(bot)
    if not has_permissions:
        logger.error(
            "Bot is missing required channel permissions "
            "(admin + invite users + restrict members). "
            "VIP invite/kick will fail until this is fixed."
        )
    else:
        logger.info("Channel permissions verified.")

    start_scheduler(bot)
    logger.info("Bot started.")

    try:
        await dp.start_polling(
            bot,
            allowed_updates=[
                "message",
                "callback_query",
                "chat_member",
            ],
        )
    finally:
        stop_scheduler()
        await ourbit.close()
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
