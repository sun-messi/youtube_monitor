"""Visualization module for backtest results."""

import logging
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from .backtest import BacktestResult, compute_buy_and_hold
from .metrics import (
    MonteCarloResult,
    compute_bucketed_returns,
    compute_rolling_sharpe,
    compute_yearly_monthly_returns,
)

logger = logging.getLogger(__name__)

plt.rcParams["font.family"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def plot_gap_vs_return(
    df: pd.DataFrame,
    holding_period: str = "T+0_intraday",
    output_path: Optional[str] = None,
) -> plt.Figure:
    """
    Scatter plot of gap percentage vs subsequent return.

    Args:
        df: DataFrame with gap_pct and return columns.
        holding_period: Which return to plot.
        output_path: Path to save figure.

    Returns:
        Matplotlib figure.
    """
    returns_col = {
        "T+0_intraday": "intraday_return",
        "T+1_close": "return_t1",
        "T+3_close": "return_t3",
        "T+5_close": "return_t5",
    }[holding_period]

    period_label = {
        "T+0_intraday": "Intraday Return",
        "T+1_close": "T+1 Return",
        "T+3_close": "T+3 Return",
        "T+5_close": "T+5 Return",
    }[holding_period]

    valid = df[["gap_pct", returns_col]].dropna()
    x = valid["gap_pct"] * 100
    y = valid[returns_col] * 100

    fig, ax = plt.subplots(figsize=(10, 8))

    ax.scatter(x, y, alpha=0.3, s=10, c="steelblue")

    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    ax.axvline(x=0, color="gray", linestyle="--", alpha=0.5)

    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    x_line = np.linspace(x.min(), x.max(), 100)
    ax.plot(x_line, p(x_line), "r-", linewidth=2, label=f"Fit: y={z[0]:.3f}x+{z[1]:.3f}")

    ax.plot(x_line, x_line, "g--", alpha=0.5, label="y=x Reference")

    ax.set_xlabel("Opening Gap (%)", fontsize=12)
    ax.set_ylabel(f"{period_label} (%)", fontsize=12)
    ax.set_title(f"TSLA Opening Gap vs {period_label}", fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved: {output_path}")

    return fig


def plot_cumulative_returns(
    df: pd.DataFrame,
    result: BacktestResult,
    mc_result: Optional[MonteCarloResult] = None,
    output_path: Optional[str] = None,
) -> plt.Figure:
    """
    Plot cumulative returns: strategy vs buy-and-hold vs random.

    Args:
        df: DataFrame with price data.
        result: Backtest result.
        mc_result: Monte Carlo result (optional).
        output_path: Path to save figure.

    Returns:
        Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    strategy_curve = result.equity_curve / result.config.initial_capital
    ax.plot(strategy_curve.index, strategy_curve.values, label="Gap Strategy", linewidth=2, color="blue")

    bh_curve = compute_buy_and_hold(df, result.config.initial_capital) / result.config.initial_capital
    ax.plot(bh_curve.index, bh_curve.values, label="Buy & Hold", linewidth=2, color="orange")

    if mc_result:
        ax.axhline(y=1 + mc_result.random_median, color="green", linestyle="--",
                   alpha=0.7, label=f"Random Median ({mc_result.random_median:+.2%})")
        ax.fill_between(
            strategy_curve.index,
            1 + mc_result.random_5th,
            1 + mc_result.random_95th,
            alpha=0.2,
            color="green",
            label="Random 5-95 Percentile"
        )

    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Cumulative Value", fontsize=12)
    ax.set_title("TSLA Gap Strategy Cumulative Returns", fontsize=14)
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    ax.set_yscale("log")

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved: {output_path}")

    return fig


def plot_bucketed_returns(
    df: pd.DataFrame,
    holding_period: str = "T+0_intraday",
    output_path: Optional[str] = None,
) -> plt.Figure:
    """
    Bar chart of average returns by gap bucket.

    Args:
        df: DataFrame with gap_pct and return columns.
        holding_period: Which return to analyze.
        output_path: Path to save figure.

    Returns:
        Matplotlib figure.
    """
    bucket_df = compute_bucketed_returns(df, holding_period)

    fig, ax = plt.subplots(figsize=(12, 6))

    colors = ["red" if r < 0 else "green" for r in bucket_df["mean_return"]]
    bars = ax.bar(bucket_df["bucket"], bucket_df["mean_return"] * 100, color=colors, alpha=0.7)

    for bar, count in zip(bars, bucket_df["count"]):
        height = bar.get_height()
        ax.annotate(f"n={count}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center", va="bottom", fontsize=9)

    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax.set_xlabel("Gap Range", fontsize=12)
    ax.set_ylabel("Avg Return (%)", fontsize=12)
    ax.set_title("TSLA Average Return by Gap Size", fontsize=14)
    ax.grid(True, alpha=0.3, axis="y")
    plt.xticks(rotation=45)

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved: {output_path}")

    return fig


def plot_rolling_sharpe(
    result: BacktestResult,
    window_days: int = 252,
    output_path: Optional[str] = None,
) -> plt.Figure:
    """
    Plot rolling 12-month Sharpe ratio.

    Args:
        result: Backtest result.
        window_days: Rolling window.
        output_path: Path to save figure.

    Returns:
        Matplotlib figure.
    """
    rolling_sharpe = compute_rolling_sharpe(result.equity_curve, window_days)

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(rolling_sharpe.index, rolling_sharpe.values, linewidth=1.5, color="purple")
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax.axhline(y=1, color="green", linestyle="--", alpha=0.5, label="Sharpe=1")
    ax.axhline(y=-1, color="red", linestyle="--", alpha=0.5, label="Sharpe=-1")

    ax.fill_between(rolling_sharpe.index, 0, rolling_sharpe.values,
                    where=rolling_sharpe > 0, alpha=0.3, color="green")
    ax.fill_between(rolling_sharpe.index, 0, rolling_sharpe.values,
                    where=rolling_sharpe < 0, alpha=0.3, color="red")

    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Rolling 12M Sharpe", fontsize=12)
    ax.set_title("TSLA Gap Strategy Rolling Sharpe Ratio", fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved: {output_path}")

    return fig


def plot_drawdown(
    df: pd.DataFrame,
    result: BacktestResult,
    output_path: Optional[str] = None,
) -> plt.Figure:
    """
    Plot drawdown curves for strategy and benchmark.

    Args:
        df: DataFrame with price data.
        result: Backtest result.
        output_path: Path to save figure.

    Returns:
        Matplotlib figure.
    """
    strategy_cum = result.equity_curve / result.equity_curve.iloc[0]
    strategy_max = strategy_cum.cummax()
    strategy_dd = (strategy_cum - strategy_max) / strategy_max * 100

    bh_cum = compute_buy_and_hold(df, result.config.initial_capital)
    bh_cum = bh_cum / bh_cum.iloc[0]
    bh_max = bh_cum.cummax()
    bh_dd = (bh_cum - bh_max) / bh_max * 100

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.fill_between(strategy_dd.index, strategy_dd.values, 0, alpha=0.5, color="blue", label="Gap Strategy DD")
    ax.fill_between(bh_dd.index, bh_dd.values, 0, alpha=0.3, color="orange", label="Buy & Hold DD")

    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Drawdown (%)", fontsize=12)
    ax.set_title("TSLA Drawdown Comparison", fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved: {output_path}")

    return fig


def plot_yearly_heatmap(
    result: BacktestResult,
    output_path: Optional[str] = None,
) -> plt.Figure:
    """
    Plot yearly/monthly performance heatmap.

    Args:
        result: Backtest result.
        output_path: Path to save figure.

    Returns:
        Matplotlib figure.
    """
    heatmap_data = compute_yearly_monthly_returns(result.equity_curve)

    fig, ax = plt.subplots(figsize=(14, 8))

    sns.heatmap(
        heatmap_data * 100,
        annot=True,
        fmt=".1f",
        cmap="RdYlGn",
        center=0,
        ax=ax,
        cbar_kws={"label": "Monthly Return (%)"},
    )

    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Year", fontsize=12)
    ax.set_title("TSLA Gap Strategy Monthly Returns Heatmap", fontsize=14)

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved: {output_path}")

    return fig


def generate_all_plots(
    df: pd.DataFrame,
    result: BacktestResult,
    mc_result: Optional[MonteCarloResult] = None,
    output_dir: str = "reports/figures",
) -> None:
    """
    Generate all plots and save to output directory.

    Args:
        df: DataFrame with price data.
        result: Backtest result.
        mc_result: Monte Carlo result.
        output_dir: Output directory.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    plot_gap_vs_return(df, result.config.holding_period, f"{output_dir}/01_gap_vs_return.png")
    plot_cumulative_returns(df, result, mc_result, f"{output_dir}/02_cumulative_returns.png")
    plot_bucketed_returns(df, result.config.holding_period, f"{output_dir}/03_bucketed_returns.png")
    plot_rolling_sharpe(result, output_path=f"{output_dir}/04_rolling_sharpe.png")
    plot_drawdown(df, result, f"{output_dir}/05_drawdown.png")
    plot_yearly_heatmap(result, f"{output_dir}/06_yearly_heatmap.png")

    plt.close("all")
    logger.info(f"All plots saved to {output_dir}")
