"""Stock prices from Yahoo Finance via yfinance."""

import time
from datetime import date, timedelta

import yfinance as yf

CACHE_SECONDS = 300
_current_cache = {}
# Dividends change a few times a year at most, so they are cached much longer.
DIVIDEND_CACHE_SECONDS = 6 * 60 * 60
_dividend_cache = {}
# Some exchanges quote prices in hundredths of the currency, e.g. pence in London.
MINOR_UNITS = {"GBp": ("GBP", 100), "GBX": ("GBP", 100), "ILA": ("ILS", 100), "ZAc": ("ZAR", 100)}


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


def get_rate_to_dkk(currency: str) -> float:
    """Return how many Danish kroner one unit of `currency` is worth right now."""
    currency, divisor = MINOR_UNITS.get(currency, (currency, 1))
    if currency == "DKK":
        return 1 / divisor
    try:
        rate, _ = get_current(f"{currency}DKK=X")
    except PriceError as exc:
        raise PriceError(f"Kunne ikke hente valutakurs for {currency}.") from exc
    return rate / divisor


def get_dividends_since(ticker: str, day: date) -> float:
    """Return the dividends per share for someone who bought on `day`, 0 if none."""
    cached = _dividend_cache.get(ticker)
    if cached and time.monotonic() - cached[0] < DIVIDEND_CACHE_SECONDS:
        payouts = cached[1]
    else:
        try:
            history = yf.Ticker(ticker).history(period="max", auto_adjust=False, actions=True)
        except Exception as exc:
            raise PriceError(f"Kunne ikke hente udbytte for {ticker}.") from exc
        if len(history) == 0 or "Dividends" not in history:
            raise PriceError(f"Intet udbytte fundet for {ticker}.")
        dividends = history["Dividends"].dropna()
        dividends = dividends[dividends > 0]
        payouts = [(when.date(), float(amount)) for when, amount in dividends.items()]
        _dividend_cache[ticker] = (time.monotonic(), payouts)
    # Shares bought on the ex-dividend date itself do not get that dividend.
    return sum(amount for ex_date, amount in payouts if ex_date > day)
