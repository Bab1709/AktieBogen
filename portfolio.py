"""Reads and writes the holdings in portfolio.json."""

import json
import os
import uuid
from pathlib import Path

PORTFOLIO_FILE = Path(__file__).parent / "portfolio.json"


def load() -> list[dict]:
    if not PORTFOLIO_FILE.exists():
        return []
    with open(PORTFOLIO_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save(holdings: list[dict]) -> None:
    # Write to a temporary file first so a crash cannot leave a half-written portfolio.
    tmp = PORTFOLIO_FILE.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(holdings, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PORTFOLIO_FILE)


def add(ticker: str, shares: float, buy_date: str, buy_price: float, currency: str) -> None:
    holdings = load()
    holdings.append(
        {
            "id": uuid.uuid4().hex,
            "ticker": ticker,
            "shares": shares,
            "buy_date": buy_date,
            "buy_price": buy_price,
            "currency": currency,
        }
    )
    _save(holdings)


def remove(holding_id: str) -> None:
    _save([h for h in load() if h["id"] != holding_id])
