import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable

from services.ourbit_api import OurbitAPI, ourbit


@dataclass(frozen=True)
class DateRange:
    start_time: int
    end_time: int
    start_label: str
    end_label: str


@dataclass
class TradingReport:
    spot_by_symbol: Dict[str, Decimal] = field(default_factory=dict)
    futures_by_symbol: Dict[str, Decimal] = field(default_factory=dict)
    effective_volume_usdt: Decimal = Decimal("0")
    commission_usdt: Decimal = Decimal("0")

    @property
    def futures_total_usdt(self) -> Decimal:
        return sum(
            self.futures_by_symbol.values(),
            Decimal("0"),
        )


def parse_date_range(value: str) -> DateRange:
    parts = value.split()
    if len(parts) != 2:
        raise ValueError("Expected two dates.")

    try:
        start = datetime.strptime(parts[0], "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        end_day = datetime.strptime(parts[1], "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    except ValueError as exc:
        raise ValueError("Dates must use YYYY-MM-DD.") from exc

    if end_day < start:
        raise ValueError("End date cannot be before start date.")

    end = end_day + timedelta(days=1) - timedelta(milliseconds=1)
    return DateRange(
        start_time=int(start.timestamp() * 1000),
        end_time=int(end.timestamp() * 1000),
        start_label=parts[0],
        end_label=parts[1],
    )


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value or 0))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _group_amounts(rows: Iterable[Dict[str, Any]]) -> Dict[str, Decimal]:
    grouped: Dict[str, Decimal] = {}
    for row in rows:
        symbol = str(row.get("symbol") or "USDT")
        grouped[symbol] = (
            grouped.get(symbol, Decimal("0"))
            + _decimal(row.get("totalAmount"))
        )
    return grouped


async def get_trading_report(
    uid: str,
    date_range: DateRange,
    api: OurbitAPI = ourbit,
) -> TradingReport:
    spot_rows, futures_rows, commission_rows = await asyncio.gather(
        api.get_trading_volume(
            uid,
            "spot",
            date_range.start_time,
            date_range.end_time,
        ),
        api.get_trading_volume(
            uid,
            "swap",
            date_range.start_time,
            date_range.end_time,
        ),
        api.get_commission_report(
            uid,
            date_range.start_time,
            date_range.end_time,
        ),
    )

    report = TradingReport(
        spot_by_symbol=_group_amounts(spot_rows),
        futures_by_symbol=_group_amounts(futures_rows),
    )
    for row in commission_rows:
        report.effective_volume_usdt += _decimal(
            row.get("tradingVol")
        )
        report.commission_usdt += _decimal(
            row.get("commissionAmount")
        )
    return report


def format_decimal(value: Decimal) -> str:
    formatted = format(value, "f")
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted or "0"
