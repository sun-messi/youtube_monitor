"""CLI entry point for TSLA gap trading backtest."""

import argparse
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from .backtest import BacktestConfig, BacktestResult, run_backtest, run_backtest_grid
from .data import fetch_tsla
from .metrics import (
    compute_benchmark_comparison,
    compute_gap_return_correlation,
    run_monte_carlo,
)
from .plots import generate_all_plots

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def generate_summary_md(
    df: pd.DataFrame,
    result: BacktestResult,
    benchmark: "BenchmarkComparison",
    mc_result: "MonteCarloResult",
    correlation: "CorrelationResult",
    grid_results: list[BacktestResult],
    output_path: str,
) -> None:
    """Generate summary markdown report."""
    from .metrics import BenchmarkComparison, MonteCarloResult, CorrelationResult

    content = f"""# TSLA 跳空交易策略回测报告

生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 数据概览

- 数据范围: {df.index.min().strftime("%Y-%m-%d")} ~ {df.index.max().strftime("%Y-%m-%d")}
- 总交易日: {len(df):,}
- 数据来源: Yahoo Finance

## 核心策略表现

### 基准配置

- 缺口阈值: {result.config.gap_threshold:.2%}
- 持有期: {result.config.holding_period}
- 趋势过滤: {result.config.trend_filter or "无"}
- 滑点: {result.config.slippage_bps} bps (双边)

### 关键指标

| 指标 | 策略 | 买入持有 |
|------|------|----------|
| 总收益 | {result.total_return:+.2%} | {benchmark.buy_hold_return:+.2%} |
| 年化收益 | {result.annual_return:+.2%} | - |
| 年化波动率 | {result.annual_volatility:.2%} | - |
| 夏普比率 | {result.sharpe:.4f} | {benchmark.buy_hold_sharpe:.4f} |
| 最大回撤 | {result.max_drawdown:.2%} | {benchmark.buy_hold_max_dd:.2%} |
| Calmar比率 | {result.calmar:.4f} | - |

### 交易统计

- 总交易次数: {result.n_trades}
- 做多次数: {result.n_long}
- 做空次数: {result.n_short}
- 胜率: {result.win_rate:.2%}
- 平均盈利: {result.avg_win:+.4f}
- 平均亏损: {result.avg_loss:+.4f}
- 盈亏比: {abs(result.avg_win / result.avg_loss) if result.avg_loss != 0 else 0:.4f}
- 利润因子: {result.profit_factor:.4f}

## 超额收益分析

- 策略总收益: {result.total_return:+.2%}
- 买入持有收益: {benchmark.buy_hold_return:+.2%}
- **超额收益: {benchmark.excess_return:+.2%}**

## 相关性分析

缺口幅度与{result.config.holding_period}收益的相关性:

| 相关系数 | 值 | p-value |
|----------|-----|---------|
| Pearson | {correlation.pearson_corr:.4f} | {correlation.pearson_pvalue:.4e} |
| Spearman | {correlation.spearman_corr:.4f} | {correlation.spearman_pvalue:.4e} |

观测数量: {correlation.n_observations:,}

## 蒙特卡洛分析

与 {mc_result.strategy_return:+.2%} 策略收益相比:

- 随机入场均值: {mc_result.random_mean:+.2%}
- 随机入场中位数: {mc_result.random_median:+.2%}
- 随机入场标准差: {mc_result.random_std:.2%}
- 5th 分位: {mc_result.random_5th:+.2%}
- 95th 分位: {mc_result.random_95th:+.2%}

**策略表现位于随机分布的第 {mc_result.percentile_rank:.1f} 分位**

p-value: {mc_result.p_value:.4f} {"(显著优于随机)" if mc_result.is_significant else "(与随机无显著差异)"}

## 参数网格回测结果

总配置数: {len(grid_results)}

### 最佳配置 (按夏普排序)

| 缺口阈值 | 持有期 | 趋势过滤 | 交易数 | 胜率 | 总收益 | 夏普 |
|----------|--------|----------|--------|------|--------|------|
"""
    sorted_results = sorted(grid_results, key=lambda x: x.sharpe, reverse=True)[:10]
    for r in sorted_results:
        content += f"| {r.config.gap_threshold:.1%} | {r.config.holding_period} | {r.config.trend_filter or '无'} | {r.n_trades} | {r.win_rate:.1%} | {r.total_return:+.1%} | {r.sharpe:.2f} |\n"

    content += f"""
## 结论

1. **缺口阈值**: {"较高阈值表现更好" if sorted_results[0].config.gap_threshold > 0.01 else "较低阈值表现更好"}
2. **持有期**: 最佳持有期为 {sorted_results[0].config.holding_period}
3. **趋势过滤**: {"有效提升表现" if sorted_results[0].config.trend_filter else "未显著改善"}
4. **整体评价**: {"策略显著优于随机入场" if mc_result.is_significant else "策略与随机入场无显著差异"}

## 图表

- `01_gap_vs_return.png`: 缺口与收益散点图
- `02_cumulative_returns.png`: 累计收益曲线
- `03_bucketed_returns.png`: 分桶平均收益
- `04_rolling_sharpe.png`: 滚动夏普比率
- `05_drawdown.png`: 回撤曲线
- `06_yearly_heatmap.png`: 逐年月度表现热力图
"""

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Summary saved to {output_path}")


def save_grid_results(results: list[BacktestResult], output_path: str) -> None:
    """Save grid results to CSV."""
    rows = []
    for r in results:
        rows.append({
            "gap_threshold": r.config.gap_threshold,
            "holding_period": r.config.holding_period,
            "trend_filter": r.config.trend_filter or "none",
            "n_trades": r.n_trades,
            "n_long": r.n_long,
            "n_short": r.n_short,
            "win_rate": r.win_rate,
            "avg_win": r.avg_win,
            "avg_loss": r.avg_loss,
            "profit_factor": r.profit_factor,
            "total_return": r.total_return,
            "annual_return": r.annual_return,
            "annual_volatility": r.annual_volatility,
            "sharpe": r.sharpe,
            "max_drawdown": r.max_drawdown,
            "calmar": r.calmar,
        })

    df = pd.DataFrame(rows)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Grid results saved to {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="TSLA Gap Trading Strategy Backtest",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--start", default="2010-06-29", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default="2026-05-12", help="End date (YYYY-MM-DD)")
    parser.add_argument("--gap-threshold", type=float, default=0.0, help="Gap threshold (e.g., 0.01 for 1%%)")
    parser.add_argument("--holding-period", default="T+0_intraday",
                        choices=["T+0_intraday", "T+1_close", "T+3_close", "T+5_close"])
    parser.add_argument("--trend-filter", default="none", choices=["none", "sma50", "sma200"])
    parser.add_argument("--output", default="reports", help="Output directory")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument("--run-grid", action="store_true", help="Run full parameter grid")
    parser.add_argument("--force-refresh", action="store_true", help="Force re-download data")

    args = parser.parse_args()

    try:
        yaml_config = load_config(args.config)
    except FileNotFoundError:
        logger.warning(f"Config file {args.config} not found, using defaults")
        yaml_config = {}

    start = args.start
    end = args.end
    cache_file = yaml_config.get("data", {}).get("cache_file", "data/tsla.parquet")

    logger.info("Fetching TSLA data...")
    df = fetch_tsla(start, end, cache_file, args.force_refresh)
    logger.info(f"Loaded {len(df)} trading days")

    if args.run_grid:
        strategy_config = yaml_config.get("strategy", {})
        gap_thresholds = strategy_config.get("gap_thresholds", [0.005, 0.01, 0.02, 0.03])
        holding_periods = strategy_config.get("holding_periods", ["T+0_intraday", "T+1_close", "T+3_close", "T+5_close"])
        trend_filters = strategy_config.get("trend_filters", ["none", "sma50", "sma200"])
        slippage = yaml_config.get("backtest", {}).get("slippage_bps", 5)

        logger.info(f"Running {len(gap_thresholds) * len(holding_periods) * len(trend_filters)} backtest configurations...")
        grid_results = run_backtest_grid(df, gap_thresholds, holding_periods, trend_filters, slippage)

        best_result = max(grid_results, key=lambda x: x.sharpe)
        logger.info(f"Best config: gap={best_result.config.gap_threshold:.2%}, period={best_result.config.holding_period}, sharpe={best_result.sharpe:.4f}")
    else:
        config = BacktestConfig(
            gap_threshold=args.gap_threshold,
            holding_period=args.holding_period,
            trend_filter=args.trend_filter if args.trend_filter != "none" else None,
            slippage_bps=yaml_config.get("backtest", {}).get("slippage_bps", 5),
        )
        best_result = run_backtest(df, config)
        grid_results = [best_result]

    logger.info("Computing metrics...")
    benchmark = compute_benchmark_comparison(df, best_result)
    correlation = compute_gap_return_correlation(df, best_result.config.holding_period)

    mc_config = yaml_config.get("monte_carlo", {})
    mc_result = run_monte_carlo(
        df, best_result,
        n_simulations=mc_config.get("n_simulations", 1000),
        random_seed=mc_config.get("random_seed", 42),
    )

    logger.info("Generating plots...")
    figures_dir = f"{args.output}/figures"
    generate_all_plots(df, best_result, mc_result, figures_dir)

    logger.info("Generating reports...")
    generate_summary_md(
        df, best_result, benchmark, mc_result, correlation, grid_results,
        f"{args.output}/summary.md"
    )
    save_grid_results(grid_results, f"{args.output}/results.csv")

    logger.info("Backtest complete!")
    print(f"\n{'='*60}")
    print("TSLA Gap Trading Strategy Backtest Summary")
    print(f"{'='*60}")
    print(f"Total Return: {best_result.total_return:+.2%}")
    print(f"Sharpe Ratio: {best_result.sharpe:.4f}")
    print(f"Max Drawdown: {best_result.max_drawdown:.2%}")
    print(f"Win Rate: {best_result.win_rate:.2%}")
    print(f"Monte Carlo Percentile: {mc_result.percentile_rank:.1f}th")
    print(f"{'='*60}")
    print(f"Reports saved to: {args.output}/")


if __name__ == "__main__":
    main()
