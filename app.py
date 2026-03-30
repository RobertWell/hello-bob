#!/usr/bin/env python3
"""Stock dashboard entrypoint.

Supports two execution modes:
- `streamlit run app.py` renders the Streamlit dashboard used on this machine.
- `python app.py` starts the lightweight HTTP server for direct local access.
"""

from __future__ import annotations

import json
import mimetypes
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from streamlit.runtime.scriptrunner import get_script_run_ctx
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

import pandas as pd
import streamlit as st

from config import STOCK_UNIVERSE
from data_collector import get_historical_data, init_database
from indicators import add_indicators
from trend_tracker import analyze_momentum, analyze_trend_direction

ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
DEFAULT_SYMBOL = "2330"
DEFAULT_DAYS = 90
MAX_DAYS = 365

init_database()


def _normalize_history_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        raise ValueError("No stock data available")

    frame = df.copy()
    date_column = "Date" if "Date" in frame.columns else "date"
    if date_column not in frame.columns:
        raise ValueError("Missing date column in stock data")

    frame[date_column] = pd.to_datetime(frame[date_column])
    frame = frame.rename(columns={date_column: "date"})
    frame = frame.sort_values("date")
    frame = frame.set_index("date")

    for column in ["open", "high", "low", "close", "volume"]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame = frame.dropna(subset=["close"])
    if frame.empty:
        raise ValueError("No valid close-price data available")

    return add_indicators(frame)


def _build_stock_payload(symbol: str, days: int) -> Dict[str, Any]:
    if symbol not in STOCK_UNIVERSE:
        raise ValueError(f"Unknown symbol: {symbol}")

    frame = _normalize_history_frame(get_historical_data(symbol, days))
    latest = frame.iloc[-1]
    previous_close = frame["close"].iloc[-2] if len(frame) > 1 else latest["close"]
    change_amount = latest["close"] - previous_close
    change_pct = (change_amount / previous_close * 100) if previous_close else 0.0
    window_start = frame["close"].iloc[max(len(frame) - 20, 0)]
    period_change_pct = ((latest["close"] - window_start) / window_start * 100) if window_start else 0.0
    trend_window = max(1, min(20, len(frame) - 1))

    trend = analyze_trend_direction(frame, window=trend_window)
    momentum = analyze_momentum(frame)

    series = []
    for idx, row in frame.tail(days).iterrows():
        series.append(
            {
                "date": idx.strftime("%Y-%m-%d"),
                "close": round(float(row["close"]), 2),
                "sma20": round(float(row["sma_20"]), 2) if pd.notna(row.get("sma_20")) else None,
                "ema20": round(float(row["ema_20"]), 2) if pd.notna(row.get("ema_20")) else None,
                "volume": int(row["volume"]) if pd.notna(row.get("volume")) else None,
            }
        )

    return {
        "symbol": symbol,
        "name": STOCK_UNIVERSE[symbol],
        "days": days,
        "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "summary": {
            "latest_close": round(float(latest["close"]), 2),
            "change_amount": round(float(change_amount), 2),
            "change_pct": round(float(change_pct), 2),
            "period_change_pct": round(float(period_change_pct), 2),
            "volume": int(latest["volume"]) if pd.notna(latest.get("volume")) else None,
            "rsi_14": round(float(latest["rsi_14"]), 2) if pd.notna(latest.get("rsi_14")) else None,
            "trend_direction": trend.get("direction"),
            "momentum": momentum.get("macd_status"),
        },
        "series": series,
    }


@st.cache_data(ttl=900, show_spinner=False)
def _load_stock_payload(symbol: str, days: int) -> Dict[str, Any]:
    return _build_stock_payload(symbol, days)


def render_streamlit_dashboard() -> None:
    st.set_page_config(
        page_title="Hello Bob Dashboard",
        page_icon=":chart_with_upwards_trend:",
        layout="wide",
    )

    st.title("Hello Bob")
    st.caption("Taiwan stock trend dashboard powered by Yahoo Finance data.")

    symbols = list(STOCK_UNIVERSE.keys())
    default_index = symbols.index(DEFAULT_SYMBOL) if DEFAULT_SYMBOL in STOCK_UNIVERSE else 0

    with st.sidebar:
        st.header("Controls")
        symbol = st.selectbox(
            "Symbol",
            options=symbols,
            index=default_index,
            format_func=lambda code: f"{code} · {STOCK_UNIVERSE[code]}",
        )
        days = st.slider("History window", min_value=30, max_value=MAX_DAYS, value=DEFAULT_DAYS, step=30)
        if st.button("Refresh data", use_container_width=True):
            _load_stock_payload.clear()
            st.rerun()

    try:
        with st.spinner("Loading market data..."):
            payload = _load_stock_payload(symbol, days)
    except Exception as exc:
        st.error(f"Dashboard failed to load data: {exc}")
        return

    summary = payload["summary"]
    series_df = pd.DataFrame(payload["series"])
    series_df["date"] = pd.to_datetime(series_df["date"])
    series_df = series_df.set_index("date")

    st.subheader(f"{payload['symbol']} · {payload['name']}")
    st.caption(f"Updated at {payload['updated_at']}")

    metric_cols = st.columns(5)
    metric_cols[0].metric("Latest Close", f"{summary['latest_close']:.2f}")
    metric_cols[1].metric("Daily Change", f"{summary['change_amount']:+.2f}", f"{summary['change_pct']:+.2f}%")
    metric_cols[2].metric("Window Return", f"{summary['period_change_pct']:+.2f}%")
    metric_cols[3].metric("RSI 14", "N/A" if summary["rsi_14"] is None else f"{summary['rsi_14']:.2f}")
    metric_cols[4].metric("Momentum", summary["momentum"] or "n/a")

    chart_cols = st.columns([2, 1])
    with chart_cols[0]:
        st.markdown("#### Price Trend")
        st.line_chart(series_df[["close", "sma20", "ema20"]], use_container_width=True)
    with chart_cols[1]:
        st.markdown("#### Trend Summary")
        st.write(f"Direction: `{summary['trend_direction']}`")
        st.write(f"Volume: `{summary['volume']}`")
        last_row = series_df.iloc[-1]
        st.write(f"SMA20: `{last_row['sma20']}`")
        st.write(f"EMA20: `{last_row['ema20']}`")

    st.markdown("#### Volume")
    st.bar_chart(series_df[["volume"]], use_container_width=True)

    with st.expander("Recent data"):
        recent = series_df.tail(20).reset_index()
        recent["date"] = recent["date"].dt.strftime("%Y-%m-%d")
        st.dataframe(recent, use_container_width=True, hide_index=True)


class StockDashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            return self._serve_file(TEMPLATES_DIR / "index.html", "text/html; charset=utf-8")
        if path == "/api/stocks":
            return self._handle_stock_list()
        if path.startswith("/api/stocks/"):
            symbol = path.rsplit("/", 1)[-1]
            return self._handle_stock_detail(symbol, parse_qs(parsed.query))
        if path.startswith("/static/"):
            relative = path.removeprefix("/static/")
            return self._serve_static(relative)

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def _handle_stock_list(self) -> None:
        stocks = [{"symbol": symbol, "name": name} for symbol, name in STOCK_UNIVERSE.items()]
        self._send_json({"stocks": stocks, "default_symbol": DEFAULT_SYMBOL, "default_days": DEFAULT_DAYS})

    def _handle_stock_detail(self, symbol: str, query: Dict[str, list[str]]) -> None:
        raw_days = query.get("days", [str(DEFAULT_DAYS)])[0]
        try:
            days = int(raw_days)
        except ValueError:
            return self._send_json({"error": "days must be an integer"}, status=HTTPStatus.BAD_REQUEST)

        days = max(30, min(days, MAX_DAYS))
        try:
            payload = _build_stock_payload(symbol, days)
        except ValueError as exc:
            return self._send_json({"error": str(exc)}, status=HTTPStatus.NOT_FOUND)
        except Exception as exc:
            return self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        self._send_json(payload)

    def _serve_static(self, relative_path: str) -> None:
        target = (STATIC_DIR / relative_path).resolve()
        if STATIC_DIR not in target.parents and target != STATIC_DIR:
            return self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
        self._serve_file(target)

    def _serve_file(self, path: Path, content_type: str | None = None) -> None:
        if not path.exists() or not path.is_file():
            return self.send_error(HTTPStatus.NOT_FOUND, "Not found")

        mime = content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload: Dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def run_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), StockDashboardHandler)
    print(f"Serving stock dashboard on http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    if get_script_run_ctx() is not None:
        render_streamlit_dashboard()
    else:
        run_server()
