from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def main_menu() -> InlineKeyboardMarkup:
    """ساخت منوی اصلی ربات."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ عضویت رایگان VIP",
                    callback_data="join_vip",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👤 وضعیت حساب",
                    callback_data="status",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 بونس",
                    callback_data="bonus",
                )
            ],
            [
                InlineKeyboardButton(
                    text="☎️ پشتیبانی",
                    callback_data="support",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎩 ثبت‌نام در صرافی",
                    callback_data="register",
                )
            ],
        ]
    )


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 آمار ربات",
                    callback_data="admin:stats",
                ),
                InlineKeyboardButton(
                    text="🔄 چک لحظه‌ای VIPها",
                    callback_data="admin:refresh",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔎 جستجوی کاربر",
                    callback_data="admin:search",
                ),
                InlineKeyboardButton(
                    text="📣 پیام همگانی",
                    callback_data="admin:broadcast",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="➕ افزودن VIP",
                    callback_data="admin:add",
                ),
                InlineKeyboardButton(
                    text="➖ حذف VIP",
                    callback_data="admin:remove",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📥 خروجی Excel",
                    callback_data="admin:export",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👤 منوی کاربری",
                    callback_data="admin:user_menu",
                )
            ],
        ]
    )


def admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ بازگشت به پنل ادمین",
                    callback_data="admin:back",
                )
            ]
        ]
    )


def broadcast_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ ارسال",
                    callback_data="admin:broadcast:confirm",
                ),
                InlineKeyboardButton(
                    text="❌ لغو",
                    callback_data="admin:broadcast:cancel",
                ),
            ]
        ]
    )


def remove_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ اخراج و غیرفعال‌سازی",
                    callback_data="admin:remove:confirm",
                ),
                InlineKeyboardButton(
                    text="❌ لغو",
                    callback_data="admin:remove:cancel",
                ),
            ]
        ]
    )