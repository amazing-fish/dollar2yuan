from __future__ import annotations

from app.repository.base_rates import JsonBaseRatesRepository
from app.services.base_rates_service import BaseRatesService
from app.ui.tk_app import RatesApp


def create_app() -> RatesApp:
    repository = JsonBaseRatesRepository()
    base_service = BaseRatesService(repository=repository)
    return RatesApp(base_service)


def main() -> None:
    app = create_app()
    app.run()


if __name__ == "__main__":
    main()
