"""Unit tests for strategy module."""

import numpy as np
import pandas as pd
import pytest

from src.strategy import compute_gap, generate_signals, get_holding_period_return


@pytest.fixture
def sample_df():
    """Create sample DataFrame for testing."""
    dates = pd.date_range("2020-01-01", periods=10, freq="B")
    data = {
        "open_adj": [100, 102, 99, 101, 103, 98, 100, 105, 102, 100],
        "close_adj": [101, 100, 100, 102, 101, 99, 104, 103, 101, 102],
        "prev_close": [np.nan, 101, 100, 100, 102, 101, 99, 104, 103, 101],
        "gap_pct": [np.nan, 0.0099, -0.01, 0.01, 0.0098, -0.0297, 0.0101, 0.0096, -0.0097, -0.0099],
        "intraday_return": [0.01, -0.0196, 0.0101, 0.0099, -0.0194, 0.0102, 0.04, -0.019, -0.0098, 0.02],
        "return_t1": [-0.0196, 0.0, 0.0303, -0.0196, -0.0194, 0.0505, -0.0095, -0.0194, 0.0099, np.nan],
        "return_t3": [0.0099, -0.01, 0.0404, 0.0099, 0.0194, -0.0095, -0.0286, np.nan, np.nan, np.nan],
        "return_t5": [0.0099, 0.04, -0.0095, 0.0, -0.0097, np.nan, np.nan, np.nan, np.nan, np.nan],
        "sma50": [100] * 10,
        "sma200": [100] * 10,
        "volume": [1000000] * 10,
        "volume_sma20": [900000] * 10,
    }
    return pd.DataFrame(data, index=dates)


class TestComputeGap:
    """Tests for compute_gap function."""

    def test_basic_gap(self, sample_df):
        """Test basic gap calculation."""
        gap = compute_gap(sample_df)
        assert len(gap) == len(sample_df)
        assert pd.isna(gap.iloc[0])

    def test_gap_values(self, sample_df):
        """Test gap values are correct."""
        gap = compute_gap(sample_df)
        assert abs(gap.iloc[1] - 0.0099) < 0.001
        assert gap.iloc[2] < 0


class TestGenerateSignals:
    """Tests for generate_signals function."""

    def test_signal_generation(self, sample_df):
        """Test signal generation with threshold."""
        result = generate_signals(sample_df, gap_threshold=0.01)
        assert "position" in result.columns
        assert set(result["position"].unique()).issubset({-1, 0, 1})

    def test_long_only(self, sample_df):
        """Test long-only signals."""
        result = generate_signals(sample_df, gap_threshold=0.01, direction="long")
        assert (result["position"] >= 0).all()

    def test_short_only(self, sample_df):
        """Test short-only signals."""
        result = generate_signals(sample_df, gap_threshold=0.01, direction="short")
        assert (result["position"] <= 0).all()

    def test_threshold_filter(self, sample_df):
        """Test that higher threshold produces fewer signals."""
        result_low = generate_signals(sample_df, gap_threshold=0.005)
        result_high = generate_signals(sample_df, gap_threshold=0.03)
        assert (result_low["position"] != 0).sum() >= (result_high["position"] != 0).sum()

    def test_trend_filter_sma50(self, sample_df):
        """Test SMA50 trend filter."""
        sample_df_high = sample_df.copy()
        sample_df_high["close_adj"] = 110  # Above SMA50
        result = generate_signals(sample_df_high, gap_threshold=0.01, trend_filter="sma50")
        assert "position" in result.columns


class TestGetHoldingPeriodReturn:
    """Tests for get_holding_period_return function."""

    def test_intraday(self, sample_df):
        """Test intraday return retrieval."""
        ret = get_holding_period_return(sample_df, "T+0_intraday")
        assert len(ret) == len(sample_df)
        assert ret.name == "intraday_return"

    def test_t1(self, sample_df):
        """Test T+1 return retrieval."""
        ret = get_holding_period_return(sample_df, "T+1_close")
        assert ret.name == "return_t1"

    def test_t3(self, sample_df):
        """Test T+3 return retrieval."""
        ret = get_holding_period_return(sample_df, "T+3_close")
        assert ret.name == "return_t3"

    def test_t5(self, sample_df):
        """Test T+5 return retrieval."""
        ret = get_holding_period_return(sample_df, "T+5_close")
        assert ret.name == "return_t5"


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame()
        with pytest.raises((KeyError, ValueError)):
            compute_gap(df)

    def test_single_row(self):
        """Test with single row DataFrame."""
        df = pd.DataFrame({
            "open_adj": [100],
            "prev_close": [np.nan],
            "gap_pct": [np.nan],
        }, index=pd.date_range("2020-01-01", periods=1))
        gap = compute_gap(df)
        assert pd.isna(gap.iloc[0])

    def test_zero_threshold(self, sample_df):
        """Test with zero threshold (all non-zero gaps are signals)."""
        result = generate_signals(sample_df, gap_threshold=0.0)
        non_nan = sample_df["gap_pct"].notna()
        non_zero = sample_df["gap_pct"] != 0
        expected_signals = (non_nan & non_zero).sum()
        actual_signals = (result["position"] != 0).sum()
        assert actual_signals <= expected_signals
