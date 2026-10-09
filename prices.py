"""Stock prices from Yahoo Finance via yfinance."""

import time
from datetime import date, timedelta

import yfinance as yf

CACHE_SECONDS = 300
_current_cache = {}


class PriceError(Exception):
    """Raised when no price can be found for a ticker."""


def get_close_on(ticker: str, day: date) -> float:
    """Return the closing price on `day`, or on the last trading day before it."""
    # Look back a few days so weekends and holidays still give a price.
    try:
        history = yf.Ticker(ticker).history(
            start=day - timedelta(days=10),
            end=day + timedelta(days=1),
            auto_adjust=False,
        )
    except Exception as exc:
        raise PriceError(f"Kunne ikke hente kurser for {ticker}.") from exc
    closes = history["Close"].dropna() if "Close" in history else []
    if len(closes) == 0:
        raise PriceError(f"Ingen kurs fundet for {ticker} på eller før {day.isoformat()}.")
    return float(closes.iloc[-1])


def get_current(ticker: str) -> tuple[float, str]:
    """Return the latest price and its currency, cached for a few minutes."""
    cached = _current_cache.get(ticker)
    if cached and time.monotonic() - cached[0] < CACHE_SECONDS:
        return cached[1], cached[2]
    try:
        info = yf.Ticker(ticker).fast_info
        price = info["lastPrice"]
        currency = info["currency"]
    except Exception as exc:
        raise PriceError(f"Kunne ikke hente kurs for {ticker}.") from exc
    if price is None or price != price or not currency:
        raise PriceError(f"Ingen kurs fundet for {ticker}.")
    _current_cache[ticker] = (time.monotonic(), float(price), currency)
    return float(price), currency
