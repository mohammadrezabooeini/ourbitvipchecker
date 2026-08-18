import unittest
from decimal import Decimal

from services.trading_report import (
    format_decimal,
    get_trading_report,
    parse_date_range,
)


class FakeTradingAPI:
    async def get_trading_volume(
        self,
        uid,
        market_type,
        start_time,
        end_time,
    ):
        if market_type == "spot":
            return [
                {"symbol": "BTC-USDT", "totalAmount": "2.5"},
                {"symbol": "BTC-USDT", "totalAmount": "1.5"},
                {"symbol": "ETH-USDT", "totalAmount": "3"},
            ]
        return [
            {"symbol": "USDT", "totalAmount": "100.25"},
            {"symbol": "USDT", "totalAmount": "9.75"},
        ]

    async def get_commission_report(
        self,
        uid,
        start_time,
        end_time,
    ):
        return [
            {
                "tradingVol": "110",
                "commissionAmount": "1.25",
            }
        ]


class DateRangeTest(unittest.TestCase):
    def test_date_range_includes_complete_end_day(self):
        date_range = parse_date_range("2026-08-01 2026-08-02")
        self.assertEqual(date_range.start_label, "2026-08-01")
        self.assertEqual(date_range.end_label, "2026-08-02")
        self.assertEqual(
            date_range.end_time - date_range.start_time,
            (2 * 24 * 60 * 60 * 1000) - 1,
        )

    def test_invalid_date_range_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_date_range("2026-08-03 2026-08-01")
        with self.assertRaises(ValueError):
            parse_date_range("1405-01-01")


class TradingReportTest(unittest.IsolatedAsyncioTestCase):
    async def test_spot_futures_and_commission_are_aggregated(self):
        report = await get_trading_report(
            uid="12345678",
            date_range=parse_date_range(
                "2026-08-01 2026-08-02"
            ),
            api=FakeTradingAPI(),
        )

        self.assertEqual(
            report.spot_by_symbol["BTC-USDT"],
            Decimal("4.0"),
        )
        self.assertEqual(
            report.spot_by_symbol["ETH-USDT"],
            Decimal("3"),
        )
        self.assertEqual(
            report.futures_total_usdt,
            Decimal("110.00"),
        )
        self.assertEqual(
            report.effective_volume_usdt,
            Decimal("110"),
        )
        self.assertEqual(
            report.commission_usdt,
            Decimal("1.25"),
        )
        self.assertEqual(format_decimal(Decimal("110.00")), "110")


if __name__ == "__main__":
    unittest.main()
