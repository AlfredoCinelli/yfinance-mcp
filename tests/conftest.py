"""Shared fixtures for yfinance-mcp tests."""

from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from finance_mcp_server.config import ScalekitSettings


@pytest.fixture
def date_range():
    """Return a standard (start, end) date pair for tests."""
    return date(2024, 1, 1), date(2024, 1, 31)


@pytest.fixture
def sample_history_df():
    """Return a DataFrame that mimics yfinance Ticker.history() output."""
    idx = pd.DatetimeIndex(["2024-01-02", "2024-01-03", "2024-01-04"], name="Date")
    return pd.DataFrame(
        {
            "Open": [150.0, 151.0, 152.0],
            "High": [155.0, 156.0, 157.0],
            "Low": [149.0, 150.0, 151.0],
            "Close": [153.1234, 154.5678, 155.9999],
            "Volume": [1000000, 1100000, 1200000],
        },
        index=idx,
    )


@pytest.fixture
def empty_history_df():
    """Return an empty DataFrame like yfinance returns for invalid tickers."""
    return pd.DataFrame()


@pytest.fixture
def expected_records():
    """Return the expected output of _ticker_history for sample_history_df."""
    return [
        {"date": "2024-01-02", "close": 153.1234},
        {"date": "2024-01-03", "close": 154.5678},
        {"date": "2024-01-04", "close": 156.0},
    ]


@pytest.fixture
def scalekit_settings():
    """Return a ScalekitSettings with dummy values for testing."""
    return ScalekitSettings(
        client_id="test-client-id",
        env_url="https://auth.example.com",
        client_secret="test-secret",
        audience="test-audience",
        _env_file=None,
    )
