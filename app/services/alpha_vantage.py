from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

import requests

from app.models.rate import RatesSnapshot


class AlphaVantageError(Exception):
    """AlphaVantage API 异常。"""


@dataclass
class AlphaVantageClient:
    api_key: str
    base_url: str = "https://www.alphavantage.co/query"

    def fetch_rates(self, days: int, outputsize: str = "compact") -> RatesSnapshot:
        if not self.api_key:
            raise AlphaVantageError("请提供有效的 API Key。")

        try:
            days_int = max(int(days), 1)
        except (TypeError, ValueError) as exc:
            raise AlphaVantageError("天数需为正整数。") from exc

        size = (outputsize or "compact").strip().lower()
        if size not in {"compact", "full"}:
            size = "compact"

        params = {
            "function": "FX_DAILY",
            "from_symbol": "USD",
            "to_symbol": "CNY",
            "apikey": self.api_key,
            "outputsize": size,
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise AlphaVantageError("无法连接到汇率服务，请检查网络或稍后再试。") from exc

        try:
            data: Dict[str, Any] = response.json()
        except ValueError as exc:
            raise AlphaVantageError("API 返回的内容不是有效的 JSON。") from exc

        if "Error Message" in data:
            raise AlphaVantageError(data["Error Message"])

        if "Note" in data:
            raise AlphaVantageError(data["Note"])

        enriched_payload = {
            "source": "alpha_vantage.FX_DAILY",
            "fetched_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            **data,
        }
        return RatesSnapshot.from_api_response(enriched_payload, days_int)
