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

The workflow downloads EURUSD M5 BID and ASK candles from Dukascopy for 2022-01-01 through 2026-11-01, aligns them, creates midpoint OHLC bars, builds H4 data from the same M5 series, and runs A2 and A3 with PyneCore.

The spread summary is included in the artifact. The initial run uses 2 ticks of slippage and 0.01% commission per fill, matching the A2 source's declared assumptions. These are test assumptions; they must be checked against the actual broker. The midpoint feed plus fixed slippage is an approximation, not a full variable-spread tick simulation.

## Start / rerun the workflow

1. Open the repository on GitHub.
2. Select the **Actions** tab.
3. Select **Forex SMC A2 and A3 external backtests**.
4. Tap **Run workflow** and choose branch `a2-audit-backtest`.
5. When it finishes, open the run's **Artifacts** section and download `forex-smc-a2-a3-eurusd-m5-2022-present`.

The workflow is manual-only now to avoid launching duplicate historical downloads on every code commit.

## Important validation boundary

PyneCore is an independent Pine-compatible runtime. The two Python files are hand-written ports of the trading logic; they are not compiled copies of the Pine source. A successful PyneCore run does not prove that the Pine files compile in TradingView. Final validation still requires:

1. Compile A3 in TradingView Pine Editor.
2. Run A3 in TradingView Strategy Tester on the matching symbol/timeframe/date range.
3. Compare the TradingView trade list with the external A3 trade list.
4. Reconcile any differences in HTF alignment, fills, spread, commission, slippage, symbol metadata and quantity steps.

No performance claim should be made until those comparisons are complete.
