# Forex SMC Engine — A2/A3 external backtest results

**Status:** completed external PyneCore run; not approved for live/prop use  
**GitHub Actions runs:** [#15](https://github.com/mixmarcos59-sketch/Forex-SMC-Engine/actions/runs/41325510258) (base cost scenario) and [#16](https://github.com/mixmarcos59-sketch/Forex-SMC-Engine/actions/runs/41326529665) (zero-commission sensitivity)  
**Run conclusions:** both success  
**Artifact:** `forex-smc-a2-a3-eurusd-m5-2022-present`

## Test setup

- Instrument: EURUSD
- Chart timeframe: M5; context timeframe: H4
- Source: Dukascopy BID and ASK historical candles
- Feed: midpoint OHLC calculated from paired BID and ASK bars
- Matched M5 rows: 359,948; no unmatched BID/ASK rows
- Actual first/last bar timestamps: 2022-01-02 22:00 UTC to 2026-10-30 20:55 UTC
- Initial capital: USD 10,000
- Commission assumption: 0.01% per fill
- Slippage assumption: 2 ticks
- PyneCore bar magnifier and tick/fill recalculation disabled to match Pine strategy defaults

The spread file reports a close-spread mean of 0.4783 pips, median 0.30 pips, 90th percentile 0.60 pips and 95th percentile 1.00 pip. The backtest uses midpoint OHLC plus fixed slippage/commission; it does **not** replay the variable BID/ASK spread on every fill.

## HTF implementation correction

The initial PyneCore ports attempted to history-index the direct return from `ta.ema()`. In PyneCore this return is a scalar, not an indexable historical series. The external runner raised `TypeError: 'float' object is not subscriptable` in its H4 security process. Runs before the fix that showed zero trades are therefore invalid as performance tests.

The port now stores the EMA in a `Series[float]` variable before applying `[1]` and passing it to `request.security()`. Run #15 completed all six strategy/diagnostic jobs with no such error in the logs. This fixes the external port's H4 data path; it does not compile the Pine source in TradingView.

## Results

All amounts below are USD on a USD 10,000 initial-equity simulation. Win rate is wins divided by total closed trades. The diagnostic strategies use the baseline small notional sizing; A3 uses the risk-based quantity calculation.

| Variant | Closed trades | Win rate | Profit factor | Net P&L | Max drawdown |
|---|---:|---:|---:|---:|---:|
| A2 baseline (score 50 + H4 gate) | 1,556 | 32.39% | 0.746 | -$46.45 (-0.46%) | $48.13 (0.48%) |
| A3 candidate (score 50 + H4 gate, nominal 1% stop risk) | 1,646 | 31.77% | 0.730 | -$9,910.97 (-99.11%) | $9,913.82 (99.14%) |
| BOS + H4 gate only (diagnostic) | 2,775 | 31.50% | 0.753 | -$74.51 (-0.75%) | $75.28 (0.75%) |
| Score 50 without hard H4 gate (diagnostic; H4 still contributes to score) | 1,710 | 33.16% | 0.753 | -$47.18 (-0.47%) | $47.18 (0.47%) |
| Score 35 without hard H4 gate (diagnostic; H4 still contributes to score) | 5,500 | 30.64% | 0.686 | -$143.54 (-1.44%) | $143.67 (1.44%) |
| Raw BOS, no filters (diagnostic only) | 12,237 | 29.35% | 0.624 | -$287.11 (-2.87%) | $287.28 (2.87%) |

A3 paid USD 9,071.21 in commissions under the configured 0.01%-per-fill assumption. Its nominal risk sizing uses stop-price distance and does not add expected commission/slippage to the quantity calculation; the realized loss at a stop can therefore exceed the nominal risk percentage.

## Zero-commission sensitivity

A second complete run used the same data, initial capital, H4 feed, and 2-tick slippage, but set the separate commission to 0. This is an additional scenario, not a full variable-spread replay.

| Variant | Closed trades | Win rate | Profit factor | Net P&L | Max drawdown |
|---|---:|---:|---:|---:|---:|
| A2, zero commission | 1,556 | 32.39% | 0.904 | -$15.61 (-0.16%) | $22.16 (0.22%) |
| A3, zero commission, nominal 1% stop risk | 1,663 | 31.99% | 0.930 | -$6,190.40 (-61.90%) | $9,055.10 (71.39% of peak equity) |

The zero-commission A3 result is materially less bad than the base-cost result, but it is still deeply negative. The system's negative outcome therefore cannot be explained by the separate commission assumption alone.

### Broker-cost context

ActivTrades' Help Center currently states that it does not charge a separate commission on most products, including Forex, and that spread is the transaction cost. Its spread guidance says major FX spreads start at an average of 0.5 pips and vary with market conditions. These statements may not apply to every entity/account/instrument; confirm the exact contract in the user's platform:
- [ActivTrades — commissions](https://help.activtrades.com/hc/activtrades-help-center/articles/1760105545-deposits-what-trading-commissions-do-you-charge)
- [ActivTrades — spreads](https://help.activtrades.com/hc/activtrades-help-center/articles/1760341130-trading-conditions-what-spreads-do-you-offer)

The zero-commission scenario keeps 2 ticks of slippage on each fill. For the EURUSD feed's 0.00001 tick size this is 0.2 pip per fill, or approximately 0.4 pip round turn. That is a rough proxy near the measured Dukascopy close-spread mean of 0.4783 pips, **not** an exact ActivTrades spread model: the feed is Dukascopy midpoint data, the spread is variable, and a fixed slippage value cannot reproduce spread widening or the broker's precise execution.

## Interpretation

1. **No tested variant is profitable in this run.** Every reported profit factor is below 1 and every net P&L is negative under the stated cost assumptions.
2. Lowering the score threshold to 35 substantially increases trade count but worsens the profit factor versus score 50. It is not a justified fix.
3. The raw BOS-only diagnostic is materially weaker and is included only to show why filters are necessary; it is not a candidate strategy.
4. A2's small dollar loss is not evidence of controlled 1% stop risk. Its source uses 1% of equity as notional exposure, not 1% risk at the stop.
5. A3's risk sizing makes the negative expectancy economically visible. It is not suitable for deployment in its current form.

## Validation boundary and next action

This is a reproducible **external hand-written PyneCore port** test, not a Pine-to-Pyne compile and not a TradingView Strategy Tester result. The data feed is midpoint OHLC with fixed costs, and the commission/slippage assumptions have not been calibrated to the user's broker/prop account.

**Decision:** keep the original, A1 and A2 files preserved; keep A3 as an unapproved research candidate. Do not deploy this system or treat the score as a win probability. The next work should address the entry/exit logic and verify execution costs against the actual broker, then compare the external trade list with TradingView before considering any live/prop use.
