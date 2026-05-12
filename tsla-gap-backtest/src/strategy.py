"""Strategy signal generation module."""

import logging
from typing import Literal, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_gap(df: pd.DataFrame) -> pd.Series:
    """
    Compute gap percentage.

    Args:
        df: DataFrame with open_adj and prev_close columns.

    Returns:
        Series of gap percentages. First day is NaN.
    """
    if "gap_pct" in df.columns:
        return df["gap_pct"]
    return (df["open_adj"] - df["prev_close"]) / df["prev_close"]


def generate_signals(
    df: pd.DataFrame,
    gap_threshold: float = 0.01,
    direction: Literal["both", "long", "short"] = "both",
    trend_filter: Optional[Literal["none", "sma50", "sma200"]] = None,
    volume_filter: bool = False,
) -> pd.DataFrame:
    """
    Generate trading signals based on gap percentage.

    Args:
        df: DataFrame with gap_pct and indicator columns.
        gap_threshold: Minimum gap size to trigger signal (e.g., 0.01 = 1%).
        direction: "both" for long+short, "long" for gap-up only, "short" for gap-down only.
        trend_filter: Apply trend filter ("none", "sma50", "sma200").
        volume_filter: If True, only trade when volume > 20-day average.

    Returns:
        DataFrame with position column: +1 (long), -1 (short), 0 (no trade).
    """
    result = df.copy()
    gap_pct = compute_gap(df)

    long_signal = gap_pct > gap_threshold
    short_signal = gap_pct < -gap_threshold

    if trend_filter == "sma50":
        long_signal = long_signal & (df["close_adj"].shift(1) > df["sma50"].shift(1))
        short_signal = short_signal & (df["close_adj"].shift(1) < df["sma50"].shift(1))
    elif trend_filter == "sma200":
        long_signal = long_signal & (df["close_adj"].shift(1) > df["sma200"].shift(1))
        short_signal = short_signal & (df["close_adj"].shift(1) < df["sma200"].shift(1))

    if volume_filter:
        vol_condition = df["volume"].shift(1) > df["volume_sma20"].shift(1)
        long_signal = long_signal & vol_condition
        short_signal = short_signal & vol_condition

    position = pd.Series(0, index=df.index, dtype=int)

    if direction in ["both", "long"]:
        position = position.where(~long_signal, 1)
    if direction in ["both", "short"]:
        position = position.where(~short_signal, -1)

    result["position"] = position
    result["signal_type"] = np.where(
        position == 1, "long",
        np.where(position == -1, "short", "none")
    )

    n_long = (position == 1).sum()
    n_short = (position == -1).sum()
    logger.info(f"Generated signals: {n_long} long, {n_short} short (threshold={gap_threshold:.2%}, filter={trend_filter})")

    return result


def get_holding_period_return(
    df: pd.DataFrame,
    holding_period: Literal["T+0_intraday", "T+1_close", "T+3_close", "T+5_close"],
) -> pd.Series:
    """
    Get the return series for a given holding period.

    Args:
        df: DataFrame with return columns.
        holding_period: Holding period type.

    Returns:
        Series of returns for the holding period.
    """
    return_map = {
        "T+0_intraday": "intraday_return",
        "T+1_close": "return_t1",
        "T+3_close": "return_t3",
        "T+5_close": "return_t5",
    }
    return df[return_map[holding_period]]
