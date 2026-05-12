"""Vectorized backtest engine."""

import logging
from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np
import pandas as pd

from .strategy import generate_signals, get_holding_period_return

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Backtest configuration."""
    gap_threshold: float = 0.01
    holding_period: Literal["T+0_intraday", "T+1_close", "T+3_close", "T+5_close"] = "T+0_intraday"
    trend_filter: Optional[Literal["none", "sma50", "sma200"]] = None
    direction: Literal["both", "long", "short"] = "both"
    slippage_bps: float = 5.0
    commission: float = 0.0
    initial_capital: float = 100000.0


@dataclass
class BacktestResult:
    """Backtest result container."""
    config: BacktestConfig
    trades: pd.DataFrame
    equity_curve: pd.Series
    total_return: float
    n_trades: int
    n_long: int
    n_short: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    sharpe: float
    max_drawdown: float
    calmar: float
    annual_return: float
    annual_volatility: float


def run_backtest(
    df: pd.DataFrame,
    config: BacktestConfig,
) -> BacktestResult:
    """
    Run vectorized backtest.

    Args:
        df: DataFrame with OHLC data and pre-computed indicators.
        config: Backtest configuration.

    Returns:
        BacktestResult with all metrics.
    """
    signals_df = generate_signals(
        df,
        gap_threshold=config.gap_threshold,
        direction=config.direction,
        trend_filter=config.trend_filter if config.trend_filter != "none" else None,
    )

    period_return = get_holding_period_return(signals_df, config.holding_period)
    position = signals_df["position"]

    slippage = config.slippage_bps / 10000 * 2
    commission = config.commission * 2

    trade_mask = position != 0
    gross_return = period_return * position
    net_return = gross_return.copy()
    net_return[trade_mask] = gross_return[trade_mask] - slippage - commission

    strategy_return = net_return.copy()
    strategy_return[~trade_mask] = 0

    cumulative = (1 + strategy_return).cumprod()
    equity_curve = cumulative * config.initial_capital

    trades_df = signals_df[trade_mask].copy()
    trades_df["gross_return"] = gross_return[trade_mask]
    trades_df["net_return"] = net_return[trade_mask]

    n_trades = len(trades_df)
    n_long = (trades_df["position"] == 1).sum()
    n_short = (trades_df["position"] == -1).sum()

    if n_trades > 0:
        wins = trades_df["net_return"] > 0
        win_rate = wins.sum() / n_trades

        avg_win = trades_df.loc[wins, "net_return"].mean() if wins.any() else 0.0
        avg_loss = trades_df.loc[~wins, "net_return"].mean() if (~wins).any() else 0.0

        total_profit = trades_df.loc[wins, "net_return"].sum() if wins.any() else 0.0
        total_loss = abs(trades_df.loc[~wins, "net_return"].sum()) if (~wins).any() else 0.0
        profit_factor = total_profit / total_loss if total_loss > 0 else np.inf
    else:
        win_rate = 0.0
        avg_win = 0.0
        avg_loss = 0.0
        profit_factor = 0.0

    total_return = cumulative.iloc[-1] - 1 if len(cumulative) > 0 else 0.0

    n_years = len(df) / 252
    annual_return = (1 + total_return) ** (1 / n_years) - 1 if n_years > 0 else 0.0

    daily_returns = strategy_return[trade_mask]
    annual_volatility = daily_returns.std() * np.sqrt(252) if len(daily_returns) > 1 else 0.0

    sharpe = annual_return / annual_volatility if annual_volatility > 0 else 0.0

    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()

    calmar = annual_return / abs(max_drawdown) if max_drawdown < 0 else 0.0

    return BacktestResult(
        config=config,
        trades=trades_df,
        equity_curve=equity_curve,
        total_return=total_return,
        n_trades=n_trades,
        n_long=n_long,
        n_short=n_short,
        win_rate=win_rate,
        avg_win=avg_win,
        avg_loss=avg_loss,
        profit_factor=profit_factor,
        sharpe=sharpe,
        max_drawdown=max_drawdown,
        calmar=calmar,
        annual_return=annual_return,
        annual_volatility=annual_volatility,
    )


def run_backtest_grid(
    df: pd.DataFrame,
    gap_thresholds: list[float],
    holding_periods: list[str],
    trend_filters: list[str],
    slippage_bps: float = 5.0,
) -> list[BacktestResult]:
    """
    Run backtest across parameter grid.

    Args:
        df: DataFrame with OHLC data.
        gap_thresholds: List of gap thresholds.
        holding_periods: List of holding periods.
        trend_filters: List of trend filters.
        slippage_bps: Slippage in basis points.

    Returns:
        List of BacktestResult for each configuration.
    """
    results = []
    total = len(gap_thresholds) * len(holding_periods) * len(trend_filters)
    count = 0

    for gap in gap_thresholds:
        for period in holding_periods:
            for trend in trend_filters:
                count += 1
                logger.info(f"Running backtest {count}/{total}: gap={gap:.2%}, period={period}, trend={trend}")

                config = BacktestConfig(
                    gap_threshold=gap,
                    holding_period=period,
                    trend_filter=trend if trend != "none" else None,
                    slippage_bps=slippage_bps,
                )
                result = run_backtest(df, config)
                results.append(result)

    return results


def compute_buy_and_hold(df: pd.DataFrame, initial_capital: float = 100000.0) -> pd.Series:
    """
    Compute buy-and-hold equity curve.

    Args:
        df: DataFrame with close_adj column.
        initial_capital: Starting capital.

    Returns:
        Equity curve series.
    """
    returns = df["close_adj"].pct_change().fillna(0)
    cumulative = (1 + returns).cumprod()
    return cumulative * initial_capital
