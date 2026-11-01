# Forex SMC Engine — A2 audit and A3 research candidate

## Protected files

The original and A1 files on `main` have not been changed. All work described here is on the separate branch:

`a2-audit-backtest`

## Files

| Path | Purpose |
|---|---|
| `original/Forex_SMC_Engine_v0_1.pine` | Preserved original on main |
| `Forex_SMC_Engine_v0_1_A1_corregido.pine` | Earlier A1 correction on main |
| `baseline/Forex_SMC_Engine_v0_1_A2_corregido.pine` | Uploaded A2 source preserved unchanged for comparison |
| `candidate/Forex_SMC_Engine_v0_1_A3_riesgo_alertas.pine` | A3 candidate: risk-based sizing, stop-distance cap and strategy alerts |
| `backtest/forex_smc_engine_a2_pyne.py` | Hand-written PyneCore port of A2 logic for external baseline testing |
| `backtest/forex_smc_engine_a3_pyne.py` | Hand-written PyneCore port of A3 risk-sized logic |
| `backtest/prepare_eurusd_data.py` | Aligns BID/ASK data, creates midpoint bars and records spread statistics |
| `audit/A2_static_audit_2026-11-01.md` | Static audit, findings, A3 notes and validation requirements |
| `.github/workflows/forex-smc-a2-backtest.yml` | Manual GitHub Actions workflow for external tests |

## What A3 changes

- Calculates order quantity from account equity, risk percentage, stop ticks, tick size and point value.
- Converts per-unit stop risk into the account currency.
- Rounds quantity down to a configurable broker volume step.
- Skips trades when the stop is farther than the configured maximum ATR distance.
- Uses `alert()` for signal alerts and `alert_message` for strategy order-fill alerts. `alertcondition()` has no effect as a strategy alert trigger.
- Assumes 1% margin (100:1) in the strategy properties. Change this to the actual broker/prop account margin setting.
- Defaults to 1% risk, 1,000-unit minimum and 1,000-unit quantity step. These are test defaults, not broker-confirmed settings.

## External test

The workflow initially obtains EURUSD M5 BID and ASK candles from Dukascopy for 2022-01-01 through 2026-11-01, aligns them, creates midpoint OHLC bars, and uses H4 context data. Later diagnostic runs reuse the verified data artifact instead of downloading the history again.

The spread summary is included in the artifact. The runner disables PyneCore's bar magnifier and tick/fill recalculation to match Pine's default strategy settings. The test uses 2 ticks of slippage and 0.01% commission per fill. These are provisional assumptions and are not calibrated to a specific broker. Midpoint OHLC plus fixed slippage is an approximation, not full variable-spread tick replay.

## Latest completed run

Runs [#15](https://github.com/mixmarcos59-sketch/Forex-SMC-Engine/actions/runs/41325510258) and [#16](https://github.com/mixmarcos59-sketch/Forex-SMC-Engine/actions/runs/41326529665) completed successfully after fixing the PyneCore H4 EMA series handling. Run #16 adds A2/A3 zero-commission variants. Results and limitations are documented in [audit/A2_A3_backtest_results_2026-11-01.md](audit/A2_A3_backtest_results_2026-11-01.md).

The important outcome is negative even without separate commission: A3 with nominal 1% stop risk loses 61.90% and has a 0.930 profit factor. The test is not a complete variable-spread model, but it shows that removing commission does not make the current strategy profitable. Lowering the score threshold to 35 increases trade count and worsens profit factor. Do not use the current candidate on a live or prop account.
 
## Trigger / rerun the workflow

The workflow runs automatically when `backtest/run-trigger.txt` is updated on branch `a2-audit-backtest`. It also supports manual `workflow_dispatch`, but you do not need to press anything in GitHub for the normal research trigger.

## Important validation boundary

PyneCore is an independent Pine-compatible runtime. The two Python files are hand-written ports of the trading logic; they are not compiled copies of the Pine source. A successful PyneCore run does not prove that the Pine files compile in TradingView. Final validation still requires:

1. Compile A3 in TradingView Pine Editor.
2. Run A3 in TradingView Strategy Tester on the matching symbol/timeframe/date range.
3. Compare the TradingView trade list with the external A3 trade list.
4. Reconcile any differences in HTF alignment, fills, spread, commission, slippage, symbol metadata and quantity steps.

No performance claim should be made until those comparisons are complete.
