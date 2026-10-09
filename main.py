# Entry point for the project.
from datetime import date
from urllib.parse import urlparse

from flask import Flask, abort, redirect, render_template, request, url_for

import portfolio
import prices

app = Flask(__name__)


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


def build_rows() -> list[dict]:
    rows = []
    for holding in portfolio.load():
        row = dict(holding)
        row["buy_value"] = holding["shares"] * holding["buy_price"]
        try:
            current_price, _ = prices.get_current(holding["ticker"])
        except prices.PriceError:
            row["current_value"] = None
        else:
            row["current_value"] = holding["shares"] * current_price
            row["gain"] = row["current_value"] - row["buy_value"]
            row["gain_pct"] = row["gain"] / row["buy_value"] * 100
        rows.append(row)
    return rows


def render_index(error: str | None = None, form: dict | None = None):
    return render_template(
        "index.html",
        rows=build_rows(),
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


@app.post("/delete/<holding_id>")
def delete(holding_id: str):
    portfolio.remove(holding_id)
    return redirect(url_for("index"))


if __name__ == "__main__":
    # Port 5001 because macOS often uses 5000 for AirPlay.
    app.run(host="127.0.0.1", port=5001, debug=False)
