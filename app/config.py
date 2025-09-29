from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass(frozen=True)
class AppPaths:
    root: Path
    data_dir: Path
    base_rates_file: Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = ROOT_DIR / "data"
DEFAULT_BASE_RATES_FILE = DEFAULT_DATA_DIR / "usd_cny_base.json"
DEFAULT_BASE_DAYS = int(os.getenv("DEFAULT_BASE_DAYS", "30"))


def resolve_base_rates_path() -> Path:
    custom_path = os.getenv("BASE_RATES_PATH")
    if custom_path:
        return Path(custom_path).expanduser().resolve()
    return DEFAULT_BASE_RATES_FILE


APP_PATHS = AppPaths(
    root=ROOT_DIR,
    data_dir=DEFAULT_DATA_DIR,
    base_rates_file=resolve_base_rates_path(),
)


def load_env_defaults() -> Dict[str, str]:
    """读取项目根目录下 .env 文件中的默认值。"""
    env_defaults: Dict[str, str] = {}
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            env_defaults[key.strip()] = value.strip().strip('"').strip("'")
    return env_defaults
