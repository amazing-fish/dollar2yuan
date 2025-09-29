from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass(frozen=True)
class RateBar:
    date: str
    open_price: float
    close_price: float
    high_price: float
    low_price: float
    amplitude: float

    @classmethod
    def from_api(cls, date_str: str, values: dict) -> "RateBar":
        try:
            open_price = float(values["1. open"])
            high_price = float(values["2. high"])
            low_price = float(values["3. low"])
            close_price = float(values["4. close"])
        except (KeyError, ValueError) as exc:
            raise ValueError("API 返回的数据结构异常。") from exc

        amplitude = 0.0
        if low_price:
            amplitude = ((high_price - low_price) / low_price) * 100

        return cls(
            date=date_str.replace("-", ""),
            open_price=open_price,
            close_price=close_price,
            high_price=high_price,
            low_price=low_price,
            amplitude=round(amplitude, 2),
        )

    def to_storage_dict(self) -> dict:
        return {
            "d": self.date,
            "o": f"{self.open_price:.4f}",
            "c": f"{self.close_price:.4f}",
            "h": f"{self.high_price:.4f}",
            "l": f"{self.low_price:.4f}",
            "am": f"{self.amplitude:.2f}",
        }

    @classmethod
    def from_storage_dict(cls, payload: dict) -> "RateBar":
        try:
            return cls(
                date=str(payload["d"]),
                open_price=float(payload["o"]),
                close_price=float(payload["c"]),
                high_price=float(payload["h"]),
                low_price=float(payload["l"]),
                amplitude=float(payload["am"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("基础数据格式不正确。") from exc


@dataclass
class RatesSnapshot:
    source: str
    fetched_at: datetime
    bars: List[RateBar]

    @classmethod
    def from_api_response(cls, payload: dict, days: int) -> "RatesSnapshot":
        time_series = payload.get("Time Series FX (Daily)")
        if not time_series:
            raise ValueError("API 未返回有效的日度汇率数据。")

        sorted_dates = sorted(time_series.keys())[-max(int(days), 1):]
        bars = [RateBar.from_api(date_str, time_series[date_str]) for date_str in sorted_dates]

        fetched_at_str = payload.get("fetched_at") or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            fetched_at = datetime.strptime(fetched_at_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            fetched_at = datetime.utcnow()

        return cls(
            source=payload.get("source", "alpha_vantage.FX_DAILY"),
            fetched_at=fetched_at,
            bars=bars,
        )

    @classmethod
    def from_storage(cls, payload: dict) -> "RatesSnapshot":
        result = payload.get("result") if payload else None
        if not result:
            raise ValueError("基础数据缺少 result 字段。")

        bars_payload = result.get("dtList") or []
        bars = [RateBar.from_storage_dict(item) for item in bars_payload]

        fetched_at_value = result.get("fetched_at")
        try:
            fetched_at = datetime.strptime(fetched_at_value, "%Y-%m-%dT%H:%M:%SZ") if fetched_at_value else datetime.utcnow()
        except ValueError:
            fetched_at = datetime.utcnow()

        return cls(
            source=result.get("source", "alpha_vantage.FX_DAILY"),
            fetched_at=fetched_at,
            bars=bars,
        )

    def to_storage(self) -> dict:
        return {
            "success": "1",
            "result": {
                "source": self.source,
                "fetched_at": self.fetched_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "dtList": [bar.to_storage_dict() for bar in self.bars],
            },
        }

    def to_chart_payload(self) -> dict:
        return {
            "dates": [bar.date for bar in self.bars],
            "open": [bar.open_price for bar in self.bars],
            "close": [bar.close_price for bar in self.bars],
            "high": [bar.high_price for bar in self.bars],
            "low": [bar.low_price for bar in self.bars],
            "amplitude": [bar.amplitude for bar in self.bars],
        }

    def is_empty(self) -> bool:
        return not self.bars
