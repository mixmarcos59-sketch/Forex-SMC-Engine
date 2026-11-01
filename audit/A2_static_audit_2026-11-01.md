# Forex SMC Engine v0.1 — A2 audit (static, 2026-11-01)

## Scope and status

- Reviewed the complete uploaded file `Forex_SMC_Engine_v0_1_A2_corregido.pine` (445 lines).
- Compared its entry/exit and confluence changes against the repository's A1 file and preserved original.
- This is a **static source audit only**. The code has not been compiled in TradingView and no historical backtest has been run.
- The original and A1 files on `main` remain untouched.
- A2's key change is retained: `strategy.exit(..., loss=..., profit=...)` uses integer tick distances captured on the signal bar, with the displayed levels anchored to the actual average fill price.

## Findings

### Critical — sizing is not stop-risk sizing

The strategy declaration sets:

```pine
default_qty_type=strategy.percent_of_equity,
default_qty_value=1
```

This means order size is 1% of equity as position value/exposure. It does **not** mean the maximum loss at the stop is 1% of equity. The monetary risk varies with stop distance, symbol contract specifications, point value and account currency. A risk-based quantity calculation is required before the strategy can be described as risking a fixed percentage per trade.

### Critical — alertcondition calls do not create strategy alerts

The script ends with two `alertcondition()` calls. TradingView documents that these calls have no effect in strategies. Strategy alerts should use `alert()` calls and/or order-fill alerts, optionally with custom `alert_message` values. This does not prevent the strategy from compiling, but the two advertised LONG/SHORT alert conditions will not be selectable as normal indicator-style triggers.

### High — stop distance can be very large

For longs, the stop candidate is the lower of the last confirmed swing low and the ATR floor; shorts use the higher of the last swing high and ATR floor. This deliberately chooses the farther stop, but a stale or distant swing can create an unexpectedly large stop distance. Since quantity is currently not risk-normalized, the resulting monetary loss is not controlled. Add a documented maximum stop-distance rule or validate a separate risk-sizing design.

### High — external fill / chart levels need validation

A2 submits the entry and its relative-tick exit on the signal bar while `process_orders_on_close=false`. The order is expected to fill at the next available tick (normally next bar open), and the relative stop/target distances are then measured from the fill. This is a reasonable A2 design, but its same-bar activation and intrabar stop/target precedence must be checked against TradingView's broker emulator and against the selected external runner. A gap between signal close and fill also means the final stop is no longer at the original structural price; it is the fixed tick distance from the actual fill.

### Medium — execution costs need instrument-specific calibration

The header hard-codes 0.01% commission and 2 ticks of slippage. These values are not automatically representative of a retail Forex broker or a prop firm's account. Spread, commission, tick size, point value and contract/lot step must be specified for the instrument and broker. A BID-only external dataset without ASK/spread treatment can overstate results.

### Medium — score is a filter, not a probability

The confluence score is bounded at 75 and combines HTF bias, prior trend, FVG overlap and displacement. It is not calibrated from historical outcomes and must not be described as a win probability or an 75% chance of success.

### Medium — only the latest FVG of each direction is retained

The script stores one bullish and one bearish FVG at a time and deletes the prior box when a new gap of that direction appears. This is acceptable for a lightweight latest-zone filter, but it is not a historical collection of all active FVGs. The display toggle only controls drawing; it does not disable FVG calculations.

## Positive checks

- HTF values use the prior completed HTF bar (`close[1]` and `ta.ema(...)[1]`) with `lookahead_on`, which is the standard confirmed-HTF pattern and avoids using the still-forming HTF bar.
- `trendBeforeBreak` is captured before `marketTrend` is updated, so the score does not award the prior-trend points merely because the current BOS just changed the trend.
- A2's tick distances are stored as integers and are clamped to at least one tick.
- The FVG created on the current bar is excluded from the FVG confluence term, preventing same-bar creation from also counting as a prior-zone retest.
- The original and A1 files are not overwritten.

## Required work before declaring A2 ready

1. Establish risk-based sizing from stop distance and actual instrument metadata; do not label current sizing as 1% risk.
2. Replace or remove ineffective strategy `alertcondition()` calls and define the intended strategy alert mechanism.
3. Decide and test a maximum structural stop distance.
4. Verify relative-tick exit timing, next-bar fills, reversals and same-bar stop/target collisions in the chosen backtest engine.
5. Obtain reproducible EURUSD M5 OHLCV data and matching H4 context data; document source, timezone, bid/ask side, date range and missing bars.
6. Compare external trade list with TradingView Strategy Tester before trusting performance metrics.
7. Only then tune parameters; keep an untouched baseline run for comparison.

## Backtest route decision

PineForge was investigated but is **not selected for this project**. Its runtime is open source, but its Pine-to-C++ compiler has a separate source license that explicitly excludes proprietary-firm/funded-trader allocated capital from the Personal Trading permission and treats that capital as investment capital. Do not assume the compiler's free personal-use permission covers a funded challenge/account.

Preferred research route: PyneCore's Apache-2.0 Python runtime, with a hand-written PyneCore port of the strategy (not the paid Pine-to-Pyne compiler). It supports Pine-style strategy orders, `strategy.exit(profit=..., loss=...)`, and multi-timeframe `request.security()`. The port is a separate implementation and must be compared with TradingView; it is not a proof that the original Pine source compiles.

## Baseline test proposal

- Instrument: EURUSD
- Chart timeframe: M5
- HTF: H4
- Initial history: 2022-01-01 through the latest complete available day
- Feed: Dukascopy historical candles; explicitly record bid/ask treatment and timezone.
- Execution: next-bar market entry, 2-tick baseline slippage only as an initial comparison, and separately calibrated commission/spread sensitivity.
- Report: closed trades, net P&L, profit factor, win rate, max drawdown, average win/loss, exposure, long/short split, and full trade list. No optimization until a baseline is reproducible.



## A3 correction candidate (not yet compiled)

A separate candidate was added at `candidate/Forex_SMC_Engine_v0_1_A3_riesgo_alertas.pine`. It does not overwrite A2.

Changes in A3:
- Replaces 1%-of-equity notional sizing with a position quantity calculated from the rounded stop distance, `strategy.equity`, and a configurable `riskPct` (default 1.0%).
- Converts per-unit stop risk into the strategy account currency with `strategy.convert_to_account()`.
- Rounds quantity down to a configurable broker quantity step; defaults are 1,000 base units minimum and 1,000-unit steps (0.01 standard FX lot). These defaults must be checked against the actual broker/prop symbol contract.
- Adds a maximum stop distance of 5 ATR; signals with a larger stop are skipped instead of allowing an unbounded structural stop.
- Removes `alertcondition()` from the strategy and uses `alert()` for signal events plus `alert_message` for order-fill alerts.
- Sets margin_long / margin_short to 1% (100:1) as a backtest capacity assumption. This is not a claim about the user's broker; it must be changed to match the actual account leverage.

The position-risk calculation is based on the same tick distance that is passed to `strategy.exit(loss=..., profit=...)`, so the planned stop risk per unit is internally consistent. Actual realized loss can still exceed the planned amount because of gaps, slippage, commissions, and spread. The max-stop threshold, risk percentage, quantity step, and margin assumption are parameters to validate—not optimized performance claims.

The A3 Pine file and its PyneCore port are still **uncompiled/unexecuted** until the GitHub Actions run completes and the original Pine source is checked in TradingView. The PyneCore port is a hand-written parallel implementation, not a compiler proof for the Pine file.
