from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.config import DEFAULT_BASE_DAYS
from app.models.rate import RatesSnapshot
from app.repository.base_rates import BaseRatesRepository
from app.services.alpha_vantage import AlphaVantageClient, AlphaVantageError


class BaseRatesRefreshError(Exception):
    pass


@dataclass
class BaseRatesService:
    repository: BaseRatesRepository

    def load_snapshot(self) -> Optional[RatesSnapshot]:
        try:
            return self.repository.load_snapshot()
        except RuntimeError as exc:
            raise BaseRatesRefreshError(str(exc)) from exc

    def refresh_snapshot(self, client: AlphaVantageClient, outputsize: str = "compact", days: int = DEFAULT_BASE_DAYS) -> RatesSnapshot:
        try:
            snapshot = client.fetch_rates(days=days, outputsize=outputsize)
        except AlphaVantageError as exc:
            raise BaseRatesRefreshError(str(exc)) from exc

        try:
            self.repository.save_snapshot(snapshot)
        except RuntimeError as exc:
            raise BaseRatesRefreshError(str(exc)) from exc

        return snapshot
