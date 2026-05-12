"""Metrics calculation and Monte Carlo simulation module."""

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats

from .backtest import BacktestResult, compute_buy_and_hold

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkComparison:
    """Comparison with benchmarks."""
    strategy_return: float
    buy_hold_return: float
    excess_return: float
    strategy_sharpe: float
    buy_hold_sharpe: float
    strategy_max_dd: float
    buy_hold_max_dd: float


@dataclass
class MonteCarloResult:
    """Monte Carlo simulation result."""
    strategy_return: float
    random_mean: float
    random_std: float
    random_median: float
    random_5th: float
    random_95th: float
    percentile_rank: float
    p_value: float
    is_significant: bool


@dataclass
class CorrelationResult:
    """Gap vs return correlation result."""
    pearson_corr: float
    pearson_pvalue: float
    spearman_corr: float
    spearman_pvalue: float
    n_observations: int


def compute_benchmark_comparison(
    df: pd.DataFrame,
    result: BacktestResult,
) -> BenchmarkComparison:
    """
    Compare strategy performance with buy-and-hold.

    Args:
        df: DataFrame with price data.
        result: Backtest result.

    Returns:
        BenchmarkComparison with metrics.
    """
    bh_equity = compute_buy_and_hold(df, result.config.initial_capital)
    bh_return = bh_equity.iloc[-1] / result.config.initial_capital - 1

    bh_returns = df["close_adj"].pct_change().dropna()
    bh_annual_return = (1 + bh_return) ** (252 / len(df)) - 1
    bh_volatility = bh_returns.std() * np.sqrt(252)
    bh_sharpe = bh_annual_return / bh_volatility if bh_volatility > 0 else 0.0

    bh_cumulative = (1 + bh_returns).cumprod()
    bh_running_max = bh_cumulative.cummax()
    bh_drawdown = (bh_cumulative - bh_running_max) / bh_running_max
    bh_max_dd = bh_drawdown.min()

    return BenchmarkComparison(
        strategy_return=result.total_return,
        buy_hold_return=bh_return,
        excess_return=result.total_return - bh_return,
        strategy_sharpe=result.sharpe,
        buy_hold_sharpe=bh_sharpe,
        strategy_max_dd=result.max_drawdown,
        buy_hold_max_dd=bh_max_dd,
    )


def run_monte_carlo(
    df: pd.DataFrame,
    result: BacktestResult,
    n_simulations: int = 1000,
    random_seed: Optional[int] = 42,
) -> MonteCarloResult:
    """
    Compare strategy with random entry signals via Monte Carlo.

    Args:
        df: DataFrame with price data.
        result: Backtest result.
        n_simulations: Number of random simulations.
        random_seed: Random seed for reproducibility.

    Returns:
        MonteCarloResult with percentile rank and p-value.
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    n_trades = result.n_trades
    if n_trades == 0:
        return MonteCarloResult(
            strategy_return=result.total_return,
            random_mean=0.0,
            random_std=0.0,
            random_median=0.0,
            random_5th=0.0,
            random_95th=0.0,
            percentile_rank=50.0,
            p_value=1.0,
            is_significant=False,
        )

    returns_col = {
        "T+0_intraday": "intraday_return",
        "T+1_close": "return_t1",
        "T+3_close": "return_t3",
        "T+5_close": "return_t5",
    }[result.config.holding_period]

    valid_mask = df[returns_col].notna()
    valid_indices = df.index[valid_mask].tolist()
    valid_returns = df.loc[valid_mask, returns_col].values

    random_returns = []
    for _ in range(n_simulations):
        random_idx = np.random.choice(len(valid_returns), size=n_trades, replace=False)
        random_directions = np.random.choice([1, -1], size=n_trades)
        sim_returns = valid_returns[random_idx] * random_directions

        slippage = result.config.slippage_bps / 10000 * 2
        sim_returns = sim_returns - slippage

        sim_total = np.prod(1 + sim_returns) - 1
        random_returns.append(sim_total)

    random_returns = np.array(random_returns)

    percentile_rank = (random_returns < result.total_return).sum() / n_simulations * 100
    p_value = 1 - percentile_rank / 100

    return MonteCarloResult(
        strategy_return=result.total_return,
        random_mean=random_returns.mean(),
        random_std=random_returns.std(),
        random_median=np.median(random_returns),
        random_5th=np.percentile(random_returns, 5),
        random_95th=np.percentile(random_returns, 95),
        percentile_rank=percentile_rank,
        p_value=p_value,
        is_significant=p_value < 0.05,
    )


def compute_gap_return_correlation(
    df: pd.DataFrame,
    holding_period: str = "T+0_intraday",
) -> CorrelationResult:
    """
    Compute correlation between gap percentage and subsequent return.

    Args:
        df: DataFrame with gap_pct and return columns.
        holding_period: Which return to correlate with.

    Returns:
        CorrelationResult with Pearson and Spearman correlations.
    """
    returns_col = {
        "T+0_intraday": "intraday_return",
        "T+1_close": "return_t1",
        "T+3_close": "return_t3",
        "T+5_close": "return_t5",
    }[holding_period]

    valid = df[["gap_pct", returns_col]].dropna()
    gap = valid["gap_pct"]
    ret = valid[returns_col]

    pearson_r, pearson_p = stats.pearsonr(gap, ret)
    spearman_r, spearman_p = stats.spearmanr(gap, ret)

    return CorrelationResult(
        pearson_corr=pearson_r,
        pearson_pvalue=pearson_p,
        spearman_corr=spearman_r,
        spearman_pvalue=spearman_p,
        n_observations=len(valid),
    )


def compute_bucketed_returns(
    df: pd.DataFrame,
    holding_period: str = "T+0_intraday",
    buckets: Optional[list[float]] = None,
) -> pd.DataFrame:
    """
    Compute average returns bucketed by gap size.

    Args:
        df: DataFrame with gap_pct and return columns.
        holding_period: Which return to analyze.
        buckets: Bucket edges (default: -3%, -2%, -1%, 0%, 1%, 2%, 3%+).

    Returns:
        DataFrame with bucket statistics.
    """
    if buckets is None:
        buckets = [-np.inf, -0.03, -0.02, -0.01, 0, 0.01, 0.02, 0.03, np.inf]

    returns_col = {
        "T+0_intraday": "intraday_return",
        "T+1_close": "return_t1",
        "T+3_close": "return_t3",
        "T+5_close": "return_t5",
    }[holding_period]

    valid = df[["gap_pct", returns_col]].dropna()

    labels = []
    for i in range(len(buckets) - 1):
        if buckets[i] == -np.inf:
            labels.append(f"<{buckets[i+1]*100:.0f}%")
        elif buckets[i+1] == np.inf:
            labels.append(f">{buckets[i]*100:.0f}%")
        else:
            labels.append(f"{buckets[i]*100:.0f}%~{buckets[i+1]*100:.0f}%")

    valid["bucket"] = pd.cut(valid["gap_pct"], bins=buckets, labels=labels)

    stats_df = valid.groupby("bucket", observed=True).agg(
        count=(returns_col, "count"),
        mean_return=(returns_col, "mean"),
        median_return=(returns_col, "median"),
        std_return=(returns_col, "std"),
        win_rate=(returns_col, lambda x: (x > 0).mean()),
    ).reset_index()

    return stats_df


def compute_rolling_sharpe(
    equity_curve: pd.Series,
    window_days: int = 252,
) -> pd.Series:
    """
    Compute rolling Sharpe ratio.

    Args:
        equity_curve: Equity curve series.
        window_days: Rolling window in trading days (default 252 = 1 year).

    Returns:
        Rolling Sharpe ratio series.
    """
    returns = equity_curve.pct_change()
    rolling_mean = returns.rolling(window=window_days).mean()
    rolling_std = returns.rolling(window=window_days).std()
    rolling_sharpe = (rolling_mean * 252) / (rolling_std * np.sqrt(252))
    return rolling_sharpe


def compute_yearly_monthly_returns(
    equity_curve: pd.Series,
) -> pd.DataFrame:
    """
    Compute returns by year and month for heatmap.

    Args:
        equity_curve: Equity curve series.

    Returns:
        DataFrame with years as rows, months as columns.
    """
    returns = equity_curve.pct_change()
    returns.index = pd.to_datetime(returns.index)

    monthly = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)
    monthly_df = monthly.to_frame("return")
    monthly_df["year"] = monthly_df.index.year
    monthly_df["month"] = monthly_df.index.month

    heatmap = monthly_df.pivot(index="year", columns="month", values="return")
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    heatmap.columns = [month_names[c-1] for c in heatmap.columns]

    return heatmap
