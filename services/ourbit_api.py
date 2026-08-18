import hashlib
import hmac
import json
import time
from typing import Any, Dict, List, Optional

import aiohttp

from config import (
    OURBIT_API_KEY,
    OURBIT_BASE_URL,
    OURBIT_SECRET_KEY,
    UID_MAX_LENGTH,
    UID_MIN_LENGTH,
    logger,
)


def validate_uid(uid: str) -> bool:
    if not uid:
        return False
    if not uid.isdigit():
        return False
    return UID_MIN_LENGTH <= len(uid) <= UID_MAX_LENGTH


def encode_json_body(payload: Dict[str, Any]) -> str:
    """Stable JSON string used both for HMAC and the HTTP body."""
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    )


class OurbitAPI:
    """Ourbit API client with a shared aiohttp session."""

    def __init__(self) -> None:
        self.api_key: str = OURBIT_API_KEY
        self.secret_key: str = OURBIT_SECRET_KEY
        self.base_url: str = OURBIT_BASE_URL
        self._session: Optional[aiohttp.ClientSession] = None
        self._timeout = aiohttp.ClientTimeout(total=20)

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    def _generate_signature(self, timestamp: str, params: str) -> str:
        payload = f"{self.api_key}{timestamp}{params}"
        return hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

    async def _post(
        self,
        endpoint: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        timestamp = str(int(time.time() * 1000))
        body = encode_json_body(payload)
        signature = self._generate_signature(timestamp, body)

        headers = {
            "Content-Type": "application/json",
            "ApiKey": self.api_key,
            "Request-Time": timestamp,
            "Signature": signature,
            "Recv-Window": "10000",
        }

        session = await self.get_session()

        try:
            async with session.post(
                self.base_url + endpoint,
                data=body.encode("utf-8"),
                headers=headers,
            ) as response:
                if response.status != 200:
                    error_body = await response.text()
                    logger.error(
                        "Ourbit API error: status=%s body=%s",
                        response.status,
                        error_body[:300],
                    )
                    raise RuntimeError(
                        f"Ourbit Error: {response.status}"
                    )
                return await response.json()

        except aiohttp.ClientError:
            logger.exception("Ourbit network error")
            raise

    async def get_balance(self, uid: str) -> Optional[float]:
        result = await self._fetch_assets(uid)
        if result["status"] != "ok":
            return None
        return result["balance"]

    async def _fetch_assets(self, uid: str) -> Dict[str, Any]:
        try:
            data = await self._post(
                "/api/v1/private/agent/assets",
                {"uids": [str(uid)]},
            )
        except Exception:
            logger.exception("Get assets error for uid=%s", uid)
            return {"status": "error", "balance": None}

        if data.get("success") is not True:
            return {"status": "error", "balance": None}

        users = data.get("data") or []
        if not isinstance(users, list) or not users:
            return {"status": "not_found", "balance": None}

        try:
            return {
                "status": "ok",
                "balance": float(users[0]["totalBalanceUsdt"]),
            }
        except (KeyError, TypeError, ValueError, IndexError):
            logger.exception("Unexpected Ourbit payload for uid=%s", uid)
            return {"status": "error", "balance": None}

    async def validate_user(self, uid: str) -> Dict[str, Any]:
        result = await self._fetch_assets(uid)

        if result["status"] == "not_found":
            return {
                "success": False,
                "message": "Referral Not Found",
            }

        if result["status"] != "ok":
            return {
                "success": False,
                "message": "Balance Error",
            }

        return {
            "success": True,
            "balance": result["balance"],
        }

    async def _get_agent_rows(
        self,
        endpoint: str,
        payload: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        data = await self._post(endpoint, payload)
        if data.get("success") is not True:
            raise RuntimeError(
                f"Ourbit agent API failed with code={data.get('code')}"
            )

        rows = data.get("data") or []
        if not isinstance(rows, list):
            raise RuntimeError("Unexpected Ourbit agent API response.")
        return [
            row
            for row in rows
            if isinstance(row, dict)
        ]

    async def get_trading_volume(
        self,
        uid: str,
        market_type: str,
        start_time: int,
        end_time: int,
    ) -> List[Dict[str, Any]]:
        if market_type not in {"spot", "swap"}:
            raise ValueError("market_type must be 'spot' or 'swap'.")

        return await self._get_agent_rows(
            "/api/v1/private/agent/subordinates/tradeVolume",
            {
                "uids": [str(uid)],
                "type": market_type,
                "startTime": start_time,
                "endTime": end_time,
            },
        )

    async def get_commission_report(
        self,
        uid: str,
        start_time: int,
        end_time: int,
    ) -> List[Dict[str, Any]]:
        return await self._get_agent_rows(
            "/api/v1/private/agent/subordinates/commission",
            {
                "uids": [str(uid)],
                "startTime": start_time,
                "endTime": end_time,
            },
        )


ourbit = OurbitAPI()
