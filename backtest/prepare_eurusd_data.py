#!/usr/bin/env python3
"""Align Dukascopy BID/ASK bars, create midpoint OHLCV, and summarize spread."""
from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path

BID = Path("data/EURUSD_5m_bid.csv")
ASK = Path("data/EURUSD_5m_ask.csv")
MID = Path("data/EURUSD_5m_mid.csv")
SUMMARY = Path("data/EURUSD_spread_summary.json")
PIP = 0.0001
TICK = 0.00001


def load(path: Path) -> dict[int, dict[str, float]]:
    rows: dict[int, dict[str, float]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"timestamp", "open", "high", "low", "close"}
        if not required.issubset(reader.fieldnames or set()):
            raise ValueError(f"{path}: missing required columns {required}")
        for row in reader:
            ts = int(float(row["timestamp"]))
            rows[ts] = {
                key: float(row[key])
                for key in ("open", "high", "low", "close")
            }
            rows[ts]["volume"] = float(row.get("volume") or 0.0)
    return rows


def percentile(values: list[float], p: float) -> float:
    if not values:
        return math.nan
    ordered = sorted(values)
    idx = (len(ordered) - 1) * p
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (idx - lo)


def main() -> None:
    bid = load(BID)
    ask = load(ASK)
    common = sorted(set(bid) & set(ask))
    if not common:
        raise SystemExit("BID and ASK files have no matching timestamps")

    spreads = [(ask[t]["close"] - bid[t]["close"]) / PIP for t in common]
    with MID.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for ts in common:
            b, a = bid[ts], ask[ts]
            writer.writerow([
                ts,
                (b["open"] + a["open"]) / 2,
                (b["high"] + a["high"]) / 2,
                (b["low"] + a["low"]) / 2,
                (b["close"] + a["close"]) / 2,
                (b["volume"] + a["volume"]) / 2,
            ])

    summary = {
        "source": "Dukascopy public historical feed via dukascopy-node",
        "price_series": "midpoint OHLC = (BID OHLC + ASK OHLC) / 2",
        "timestamps": "Unix milliseconds, UTC",
        "bid_rows": len(bid),
        "ask_rows": len(ask),
        "matched_rows": len(common),
        "bid_only_rows": len(set(bid) - set(ask)),
        "ask_only_rows": len(set(ask) - set(bid)),
        "spread_unit": "pips (EURUSD pip = 0.0001)",
        "spread_close_pips": {
            "mean": statistics.fmean(spreads),
            "median": statistics.median(spreads),
            "p90": percentile(spreads, 0.90),
            "p95": percentile(spreads, 0.95),
            "maximum": max(spreads),
        },
        "spread_close_ticks": {
            "median": statistics.median(spreads) * PIP / TICK,
            "p90": percentile(spreads, 0.90) * PIP / TICK,
        },
        "first_timestamp_ms": common[0],
        "last_timestamp_ms": common[-1],
        "mid_rows": len(common),
    }
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
