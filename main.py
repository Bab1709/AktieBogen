# Entry point for the project.
import re
from datetime import date
from urllib.parse import urlparse

from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

import portfolio
import prices

app = Flask(__name__)

# Remembers whether amounts are shown in each stock's own currency or in DKK.
DISPLAY_COOKIE = "display_currency"
# The periods the chart page offers, in the order they are shown.
CHART_PERIODS = {"1mo": "1 md.", "6mo": "6 mdr.", "1y": "1 år", "5y": "5 år", "max": "Maks"}
# The characters Yahoo Finance uses in ticker symbols.
TICKER_PATTERN = re.compile(r"[A-Z0-9.\-=^]{1,20}")


@app.template_filter("amount")
def format_amount(value: float) -> str:
    """Format a number the Danish way: 1.234,56."""
    text = f"{value:,.2f}"
    return text.replace(",", " ").replace(".", ",").replace(" ", ".")


@app.template_filter("quantity")
def format_quantity(value: float) -> str:
    """Format a share count without trailing zeros: 10 or 2,5."""
    return f"{value:.4f}".rstrip("0").rstrip(".").replace(".", ",")


@app.before_request
def reject_foreign_posts():
    # Stop other websites open in the browser from posting to this local app.
    origin = request.headers.get("Origin")
    if request.method == "POST" and origin and urlparse(origin).netloc != request.host:
        abort(403)


def parse_number(text: str) -> float:
    """Parse a positive number, accepting both comma and dot as decimal mark."""
    value = float(text.strip().replace(",", "."))
    if not 0 < value < float("inf"):
        raise ValueError(text)
    return value


def build_rows(in_dkk: bool) -> tuple[list[dict], float, int]:
    """Return the table rows, the total value in DKK and how many holdings the total is missing."""
    rows = []
    total_dkk = 0.0
    missing = 0
    for holding in portfolio.load():
        row = dict(holding)
        try:
            rate = prices.get_rate_to_dkk(holding["currency"])
        except prices.PriceError:
            rate = None
        # A holding without an exchange rate stays in its own currency.
        scale = rate if in_dkk and rate is not None else 1
        if scale is rate:
            row["currency"] = "DKK"
        row["buy_price"] = holding["buy_price"] * scale
        row["buy_value"] = holding["shares"] * row["buy_price"]
        try:
            current_price, _ = prices.get_current(holding["ticker"])
        except prices.PriceError:
            row["current_value"] = None
            missing += 1
        else:
            row["current_value"] = holding["shares"] * current_price * scale
            row["gain"] = row["current_value"] - row["buy_value"]
            row["gain_pct"] = row["gain"] / row["buy_value"] * 100
            if rate is None:
                missing += 1
            else:
                total_dkk += holding["shares"] * current_price * rate
        try:
            buy_date = date.fromisoformat(holding["buy_date"])
            row["dividends"] = holding["shares"] * prices.get_dividends_since(holding["ticker"], buy_date) * scale
        except prices.PriceError:
            row["dividends"] = None
        rows.append(row)
    return rows, total_dkk, missing


def render_index(error: str | None = None, form: dict | None = None):
    in_dkk = request.cookies.get(DISPLAY_COOKIE) == "dkk"
    rows, total_dkk, missing = build_rows(in_dkk)
    return render_template(
        "index.html",
        rows=rows,
        total_dkk=total_dkk,
        missing=missing,
        in_dkk=in_dkk,
        error=error,
        form=form or {},
        today=date.today().isoformat(),
    )


@app.get("/")
def index():
    return render_index()


@app.post("/add")
def add():
    form = request.form
    ticker = form.get("ticker", "").strip().upper()
    if not ticker:
        return render_index("Skriv et ticker-symbol.", form), 400
    try:
        shares = parse_number(form.get("shares", ""))
    except ValueError:
        return render_index("Antal skal være et tal større end 0.", form), 400
    try:
        buy_date = date.fromisoformat(form.get("buy_date", ""))
    except ValueError:
        return render_index("Vælg en gyldig købsdato.", form), 400
    if buy_date > date.today():
        return render_index("Købsdatoen kan ikke ligge i fremtiden.", form), 400

    try:
        # Also confirms that the ticker exists before anything is saved.
        _, currency = prices.get_current(ticker)
        if form.get("buy_price", "").strip():
            buy_price = parse_number(form["buy_price"])
        else:
            buy_price = prices.get_close_on(ticker, buy_date)
    except ValueError:
        return render_index("Købskurs skal være et tal større end 0.", form), 400
    except prices.PriceError as exc:
        return render_index(str(exc), form), 400

    portfolio.add(ticker, shares, buy_date.isoformat(), buy_price, currency)
    return redirect(url_for("index"))


@app.get("/search")
def search():
    try:
        return jsonify(prices.search(request.args.get("q", "")[:50]))
    except prices.PriceError as exc:
        return jsonify(error=str(exc)), 502


@app.get("/stock/<ticker>")
def stock(ticker: str):
    ticker = ticker.upper()
    if not TICKER_PATTERN.fullmatch(ticker):
        abort(404)
    period = request.args.get("period")
    if period not in CHART_PERIODS:
        period = "1y"
    context = dict(ticker=ticker, name=prices.get_name(ticker), period=period, periods=CHART_PERIODS)
    try:
        price, currency = prices.get_current(ticker)
        points = prices.get_history(ticker, period)
    except prices.PriceError as exc:
        return render_template("stock.html", error=str(exc), **context), 404
    change = points[-1][1] - points[0][1]
    return render_template(
        "stock.html",
        price=price,
        currency=currency,
        points=points,
        change=change,
        change_pct=change / points[0][1] * 100,
        **context,
    )


@app.post("/display")
def display():
    choice = "dkk" if request.form.get("currency") == "dkk" else "native"
    response = redirect(url_for("index"))
    response.set_cookie(DISPLAY_COOKIE, choice, max_age=365 * 24 * 60 * 60, samesite="Lax")
    return response


@app.post("/delete/<holding_id>")
def delete(holding_id: str):
    portfolio.remove(holding_id)
    return redirect(url_for("index"))


if __name__ == "__main__":
    # Port 5001 because macOS often uses 5000 for AirPlay.
    app.run(host="127.0.0.1", port=5001, debug=False)
