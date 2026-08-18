from io import BytesIO
from typing import Any, Iterable

from openpyxl import Workbook


VIP_EXPORT_HEADERS = [
    "Telegram Username",
    "نام",
    "Telegram Numeric ID",
    "Ourbit UID",
    "وضعیت VIP",
    "موجودی USDT",
    "تاریخ عضویت",
    "آخرین بررسی",
    "آخرین هشدار",
    "تعداد هشدار",
]


def build_vip_excel(users: Iterable[Any]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "VIP Users"
    sheet.sheet_view.rightToLeft = True
    sheet.freeze_panes = "A2"
    sheet.append(VIP_EXPORT_HEADERS)

    for user in users:
        username = (
            f"@{user['username']}"
            if user["username"]
            else "-"
        )
        sheet.append(
            [
                username,
                user["first_name"] or "-",
                user["telegram_id"],
                user["ourbit_uid"],
                user["vip_status"],
                float(user["balance"] or 0),
                user["joined_at"] or "-",
                user["last_check"] or "-",
                user["last_warning"] or "-",
                int(user["warning_count"] or 0),
            ]
        )

    sheet.auto_filter.ref = sheet.dimensions
    widths = [24, 22, 22, 18, 14, 18, 22, 22, 22, 14]
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[
            sheet.cell(row=1, column=index).column_letter
        ].width = width

    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()
