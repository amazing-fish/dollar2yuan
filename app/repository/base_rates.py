from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from app.config import APP_PATHS
from app.models.rate import RatesSnapshot


class BaseRatesRepository(ABC):
    @abstractmethod
    def load_snapshot(self) -> Optional[RatesSnapshot]:
        raise NotImplementedError

    @abstractmethod
    def save_snapshot(self, snapshot: RatesSnapshot) -> None:
        raise NotImplementedError


class JsonBaseRatesRepository(BaseRatesRepository):
    def __init__(self, file_path: Path | None = None) -> None:
        self._file_path = file_path or APP_PATHS.base_rates_file

    def load_snapshot(self) -> Optional[RatesSnapshot]:
        path = self._file_path
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"基础数据读取失败：{exc}") from exc

        if not payload:
            return None

        try:
            return RatesSnapshot.from_storage(payload)
        except ValueError as exc:
            raise RuntimeError(f"基础数据格式不正确：{exc}") from exc

    def save_snapshot(self, snapshot: RatesSnapshot) -> None:
        path = self._file_path
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("w", encoding="utf-8") as fh:
                json.dump(snapshot.to_storage(), fh, ensure_ascii=False, indent=2)
        except OSError as exc:
            raise RuntimeError(f"基础数据写入失败：{exc}") from exc
