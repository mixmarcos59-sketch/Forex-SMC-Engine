"""
@pyne
"""
from pynecore import Persistent
from pynecore.lib import (
    bar_index,
    barmerge,
    barstate,
    close,
    high,
    low,
    math,
    open,
    request,
    script,
    strategy,
    syminfo,
    ta,
)


@script.strategy(
    "Forex SMC diagnostic — score 50 without HTF gate",
    overlay=True,
    pyramiding=0,
    initial_capital=10000,
    default_qty_type=strategy.percent_of_equity,
    default_qty_value=1,
    commission_type=strategy.commission.percent,
    commission_value=0.01,
    slippage=2,
    process_orders_on_close=False,
    calc_on_order_fills=False,
    calc_on_every_tick=False,
    calc_on_every_history_tick=False,
    use_bar_magnifier=False,
)
def main(
    swing_len: int = 4,
    atr_len: int = 14,
    htf: str = "240",
    use_htf: bool = True,
    ema_len: int = 50,
    min_score: int = 50,
    disp_mult: float = 0.8,
    rr: float = 2.0,
    stop_atr: float = 1.5,
):
    # Confirmed higher-timeframe values: same close[1] + lookahead_on
    # idiom as the Pine source. Supply a separate 240-minute data file.
    htf_close = request.security(
        syminfo.tickerid,
        htf,
        close[1],
        lookahead=barmerge.lookahead_on,
    )
    htf_ema = request.security(
        syminfo.tickerid,
        htf,
        ta.ema(close, ema_len)[1],
        lookahead=barmerge.lookahead_on,
    )
    htf_bull = htf_close > htf_ema
    htf_bear = htf_close < htf_ema

    atr = ta.atr(atr_len)

    pivot_high = ta.pivothigh(high, swing_len, swing_len)
    pivot_low = ta.pivotlow(low, swing_len, swing_len)

    last_high: Persistent[float] = float("nan")
    last_low: Persistent[float] = float("nan")
    high_broken: Persistent[bool] = False
    low_broken: Persistent[bool] = False
    market_trend: Persistent[int] = 0

    if pivot_high == pivot_high:
        last_high = pivot_high
        high_broken = False

    if pivot_low == pivot_low:
        last_low = pivot_low
        low_broken = False

    bull_break = (
        barstate.isconfirmed
        and last_high == last_high
        and not high_broken
        and close > last_high
        and close[1] <= last_high
    )
    bear_break = (
        barstate.isconfirmed
        and last_low == last_low
        and not low_broken
        and close < last_low
        and close[1] >= last_low
    )

    trend_before_break = market_trend

    if bull_break:
        high_broken = True
        market_trend = 1

    if bear_break:
        low_broken = True
        market_trend = -1

    bull_fvg = bar_index >= 2 and low > high[2]
    bear_fvg = bar_index >= 2 and high < low[2]

    bull_top: Persistent[float] = float("nan")
    bull_bottom: Persistent[float] = float("nan")
    bear_top: Persistent[float] = float("nan")
    bear_bottom: Persistent[float] = float("nan")

    if bull_fvg:
        bull_top = low
        bull_bottom = high[2]

    if bear_fvg:
        bear_top = low[2]
        bear_bottom = high

    if bull_bottom == bull_bottom and low <= bull_bottom:
        bull_top = float("nan")
        bull_bottom = float("nan")

    if bear_top == bear_top and high >= bear_top:
        bear_top = float("nan")
        bear_bottom = float("nan")

    in_bull_fvg = (
        bull_top == bull_top
        and low <= bull_top
        and close >= bull_bottom
    )
    in_bear_fvg = (
        bear_bottom == bear_bottom
        and high >= bear_bottom
        and close <= bear_top
    )

    body = math.abs(close - open)
    bull_displacement = close > open and body >= atr * disp_mult
    bear_displacement = close < open and body >= atr * disp_mult

    long_score = (
        (25 if htf_bull else 0)
        + (20 if trend_before_break == 1 else 0)
        + (15 if in_bull_fvg and not bull_fvg else 0)
        + (15 if bull_displacement else 0)
    )
    short_score = (
        (25 if htf_bear else 0)
        + (20 if trend_before_break == -1 else 0)
        + (15 if in_bear_fvg and not bear_fvg else 0)
        + (15 if bear_displacement else 0)
    )

    long_allowed = (not use_htf) or htf_bull
    short_allowed = (not use_htf) or htf_bear

    long_signal = barstate.isconfirmed and bull_break and long_score >= min_score
    short_signal = barstate.isconfirmed and bear_break and short_score >= min_score



    long_sl_ticks: Persistent[int] = -1
    long_tp_ticks: Persistent[int] = -1
    short_sl_ticks: Persistent[int] = -1
    short_tp_ticks: Persistent[int] = -1

    if long_signal and strategy.position_size <= 0:
        candidate_sl = (
            close - atr * stop_atr
            if last_low != last_low
            else math.min(last_low, close - atr * stop_atr)
        )
        risk_dist = close - candidate_sl
        long_sl_ticks = max(1, math.round(risk_dist / syminfo.mintick))
        long_tp_ticks = max(1, round(long_sl_ticks * rr))

        short_sl_ticks = -1
        short_tp_ticks = -1

        strategy.entry("LONG", strategy.long)
        strategy.exit(
            "LONG EXIT",
            from_entry="LONG",
            loss=long_sl_ticks,
            profit=long_tp_ticks,
        )

    if short_signal and strategy.position_size >= 0:
        candidate_sl = (
            close + atr * stop_atr
            if last_high != last_high
            else math.max(last_high, close + atr * stop_atr)
        )
        risk_dist = candidate_sl - close
        short_sl_ticks = max(1, math.round(risk_dist / syminfo.mintick))
        short_tp_ticks = max(1, round(short_sl_ticks * rr))

        long_sl_ticks = -1
        long_tp_ticks = -1

        strategy.entry("SHORT", strategy.short)
        strategy.exit(
            "SHORT EXIT",
            from_entry="SHORT",
            loss=short_sl_ticks,
            profit=short_tp_ticks,
        )
