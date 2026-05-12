# TSLA Gap Trading Strategy Backtest

量化回测"特斯拉启动理论"在 TSLA 上的实际表现。

## 策略逻辑

- **跳空高开** (今开 > 昨收): 当日开盘做多,收盘平仓
- **跳空低开** (今开 < 昨收): 当日开盘做空,收盘平仓
- **平开** (无显著缺口): 不交易

## 安装

```bash
cd tsla-gap-backtest
pip install -r requirements.txt
```

## 快速开始

### 运行完整回测

```bash
python -m src.main --run-grid
```

### 单一配置回测

```bash
python -m src.main --gap-threshold 0.01 --holding-period T+0_intraday --trend-filter none
```

### 自定义参数

```bash
python -m src.main \
  --start 2015-01-01 \
  --end 2024-12-31 \
  --gap-threshold 0.02 \
  --holding-period T+1_close \
  --trend-filter sma50 \
  --output reports/custom/
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--start` | 2010-06-29 | 回测起始日期 |
| `--end` | 2026-05-12 | 回测结束日期 |
| `--gap-threshold` | 0.0 | 缺口阈值 (0.01 = 1%) |
| `--holding-period` | T+0_intraday | 持有期: T+0_intraday, T+1_close, T+3_close, T+5_close |
| `--trend-filter` | none | 趋势过滤: none, sma50, sma200 |
| `--output` | reports | 输出目录 |
| `--run-grid` | False | 运行完整参数网格 |
| `--force-refresh` | False | 强制重新下载数据 |

## 配置文件

编辑 `config.yaml` 自定义参数网格:

```yaml
strategy:
  gap_thresholds: [0.005, 0.01, 0.02, 0.03]
  holding_periods: ["T+0_intraday", "T+1_close", "T+3_close", "T+5_close"]
  trend_filters: ["none", "sma50", "sma200"]

backtest:
  slippage_bps: 5  # 双边滑点 (basis points)
  commission: 0.0  # 手续费

monte_carlo:
  n_simulations: 1000
```

## 输出文件

```
reports/
├── summary.md          # 文字总结 + 关键指标
├── results.csv         # 所有配置的回测结果
└── figures/
    ├── 01_gap_vs_return.png      # 缺口 vs 收益散点图
    ├── 02_cumulative_returns.png # 累计收益曲线
    ├── 03_bucketed_returns.png   # 分桶平均收益
    ├── 04_rolling_sharpe.png     # 滚动12月夏普
    ├── 05_drawdown.png           # 回撤曲线
    └── 06_yearly_heatmap.png     # 逐年月度热力图
```

## 运行测试

```bash
pytest tests/ -v
```

## 项目结构

```
tsla-gap-backtest/
├── src/
│   ├── data.py        # 数据下载与校验
│   ├── strategy.py    # 信号生成
│   ├── backtest.py    # 向量化回测引擎
│   ├── metrics.py     # 指标计算 + 蒙特卡洛
│   ├── plots.py       # 可视化
│   └── main.py        # CLI 入口
├── data/              # 本地数据缓存
├── reports/           # 回测报告输出
├── tests/             # 单元测试
├── config.yaml        # 配置文件
└── requirements.txt   # 依赖
```

## 核心问题

本回测旨在回答:

1. **在多大缺口阈值下策略有正期望?**
2. **不同市场环境 (上涨/下跌/震荡) 下表现如何?**
3. **与 buy-and-hold、随机入场相比有没有显著优势?**

## 注意事项

- 数据自动调整股票分拆 (2020-08-31 5:1, 2022-08-25 3:1)
- 默认滑点假设: 双边 5 bps
- 蒙特卡洛显著性检验: 1000 次随机模拟
- 所有收益均为税前、不考虑融资成本

## License

MIT
