"""Data fetching, caching, and validation module."""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_tsla(
    start: str = "2010-06-29",
    end: str = "2026-05-12",
    cache_file: Optional[str] = None,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Fetch TSLA daily OHLCV data from Yahoo Finance.

    Args:
        start: Start date in YYYY-MM-DD format.
        end: End date in YYYY-MM-DD format.
        cache_file: Path to parquet cache file.
        force_refresh: Force re-download even if cache exists.

    Returns:
        DataFrame with adjusted OHLC data.
    """
    if cache_file and not force_refresh:
        cache_path = Path(cache_file)
        if cache_path.exists():
            logger.info(f"Loading cached data from {cache_file}")
            df = pd.read_parquet(cache_file)
            if df.index.min().strftime("%Y-%m-%d") <= start and df.index.max().strftime("%Y-%m-%d") >= end:
                mask = (df.index >= start) & (df.index <= end)
                return df.loc[mask].copy()
            logger.info("Cache date range insufficient, re-downloading...")

    logger.info(f"Downloading TSLA data from {start} to {end}")
    ticker = yf.Ticker("TSLA")
    df = ticker.history(start=start, end=end, auto_adjust=False)

    if df.empty:
        raise ValueError("No data returned from Yahoo Finance")

    df = _process_data(df)
    _validate_data(df)

    if cache_file:
        cache_path = Path(cache_file)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_file)
        logger.info(f"Cached data to {cache_file}")

    return df


def _process_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process raw data: adjust for splits/dividends.

    Uses Adj Close / Close ratio to adjust Open, High, Low.
    """
    df = df.copy()

    df.columns = df.columns.str.lower().str.replace(" ", "_")

    if "adj_close" not in df.columns and "adj close" in df.columns:
        df = df.rename(columns={"adj close": "adj_close"})

    adj_factor = df["adj_close"] / df["close"]
    df["open_adj"] = df["open"] * adj_factor
    df["high_adj"] = df["high"] * adj_factor
    df["low_adj"] = df["low"] * adj_factor
    df["close_adj"] = df["adj_close"]

    df["prev_close"] = df["close_adj"].shift(1)
    df["gap_pct"] = (df["open_adj"] - df["prev_close"]) / df["prev_close"]
    df["intraday_return"] = (df["close_adj"] - df["open_adj"]) / df["open_adj"]

    df["return_t1"] = df["close_adj"].shift(-1) / df["open_adj"] - 1
    df["return_t3"] = df["close_adj"].shift(-3) / df["open_adj"] - 1
    df["return_t5"] = df["close_adj"].shift(-5) / df["open_adj"] - 1

    df["sma50"] = df["close_adj"].rolling(window=50).mean()
    df["sma200"] = df["close_adj"].rolling(window=200).mean()
    df["volume_sma20"] = df["volume"].rolling(window=20).mean()

    return df


def _validate_data(df: pd.DataFrame) -> None:
    """
    Validate data quality.

    Checks for:
    - Missing dates (warns only)
    - Zero volume days
    - Extreme price jumps (>50% single day)
    """
    if df["volume"].eq(0).any():
        zero_vol_dates = df[df["volume"] == 0].index.tolist()
        logger.warning(f"Found {len(zero_vol_dates)} zero volume days: {zero_vol_dates[:5]}...")

    daily_return = df["close_adj"].pct_change().abs()
    extreme_days = daily_return[daily_return > 0.5]
    if len(extreme_days) > 0:
        logger.warning(f"Found {len(extreme_days)} days with >50% price change")
        for date, ret in extreme_days.items():
            logger.warning(f"  {date.strftime('%Y-%m-%d')}: {ret:+.2%}")

    date_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq="B")
    missing_dates = date_range.difference(df.index)
    if len(missing_dates) > 0:
        logger.info(f"Note: {len(missing_dates)} business days not in data (holidays/weekends)")

    null_counts = df[["open_adj", "high_adj", "low_adj", "close_adj", "volume"]].isnull().sum()
    if null_counts.any():
        logger.warning(f"Null values found:\n{null_counts[null_counts > 0]}")

    logger.info(f"Data validation complete: {len(df)} trading days from {df.index.min().strftime('%Y-%m-%d')} to {df.index.max().strftime('%Y-%m-%d')}")


def get_split_dates() -> dict:
    """Return known TSLA stock split dates and ratios."""
    return {
        "2020-08-31": 5,  # 5:1 split
        "2022-08-25": 3,  # 3:1 split
    }
