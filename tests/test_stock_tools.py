"""Tests for Yahoo Finance MCP tools – yfinance is always mocked."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from finance_mcp_server.mcp_servers.stock import (
    _ticker_history,
    get_multiple_stocks_prices,
    get_stock_price,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.tools]


# ---------------------------------------------------------------------------
# _ticker_history (sync helper)
# ---------------------------------------------------------------------------
class TestTickerHistory:
    """Tests for the synchronous _ticker_history helper."""

    @patch("finance_mcp_server.mcp_servers.stock.yf.Ticker")
    def test_returns_records_with_date_and_close(self, mock_ticker_cls, sample_history_df, date_range):
        mock_ticker_cls.return_value.history.return_value = sample_history_df
        start, end = date_range

        result = _ticker_history("AAPL", start, end, "1d")

        assert len(result) == 3
        assert all("date" in r and "close" in r for r in result)
        mock_ticker_cls.assert_called_once_with("AAPL")
        mock_ticker_cls.return_value.history.assert_called_once_with(
            start="2024-01-01", end="2024-01-31", interval="1d", auto_adjust=True,
        )

    @patch("finance_mcp_server.mcp_servers.stock.yf.Ticker")
    def test_close_rounded_to_four_decimals(self, mock_ticker_cls, sample_history_df, date_range):
        mock_ticker_cls.return_value.history.return_value = sample_history_df
        start, end = date_range

        result = _ticker_history("AAPL", start, end, "1d")

        for record in result:
            decimal_part = str(record["close"]).split(".")[-1]
            assert len(decimal_part) <= 4

    @patch("finance_mcp_server.mcp_servers.stock.yf.Ticker")
    def test_empty_dataframe_returns_empty_list(self, mock_ticker_cls, empty_history_df, date_range):
        mock_ticker_cls.return_value.history.return_value = empty_history_df
        start, end = date_range

        result = _ticker_history("INVALID", start, end, "1d")

        assert result == []

    @pytest.mark.parametrize(
        "interval",
        [
            pytest.param("1d", id="daily"),
            pytest.param("1wk", id="weekly"),
            pytest.param("1mo", id="monthly"),
        ],
    )
    @patch("finance_mcp_server.mcp_servers.stock.yf.Ticker")
    def test_interval_forwarded_to_yfinance(self, mock_ticker_cls, sample_history_df, date_range, interval):
        mock_ticker_cls.return_value.history.return_value = sample_history_df
        start, end = date_range

        _ticker_history("AAPL", start, end, interval)

        call_kwargs = mock_ticker_cls.return_value.history.call_args[1]
        assert call_kwargs["interval"] == interval

    @patch("finance_mcp_server.mcp_servers.stock.yf.Ticker")
    def test_dates_formatted_as_iso(self, mock_ticker_cls, sample_history_df):
        mock_ticker_cls.return_value.history.return_value = sample_history_df
        start = date(2024, 3, 15)
        end = date(2024, 6, 20)

        _ticker_history("MSFT", start, end, "1d")

        call_kwargs = mock_ticker_cls.return_value.history.call_args[1]
        assert call_kwargs["start"] == "2024-03-15"
        assert call_kwargs["end"] == "2024-06-20"


# ---------------------------------------------------------------------------
# get_stock_price (async tool)
# ---------------------------------------------------------------------------
class TestGetStockPrice:
    """Tests for the get_stock_price MCP tool."""

    @patch("finance_mcp_server.mcp_servers.stock._ticker_history")
    async def test_returns_records(self, mock_history, date_range):
        mock_history.return_value = [
            {"date": "2024-01-02", "close": 150.0},
            {"date": "2024-01-03", "close": 151.0},
        ]
        start, end = date_range

        result = await get_stock_price(ticker="AAPL", start=start, end=end)

        assert len(result) == 2
        assert result[0]["date"] == "2024-01-02"

    @patch("finance_mcp_server.mcp_servers.stock._ticker_history")
    async def test_default_interval(self, mock_history, date_range):
        mock_history.return_value = []
        start, end = date_range

        await get_stock_price(ticker="AAPL", start=start, end=end)

        call_args = mock_history.call_args[0]
        assert call_args[3] == "1d"

    @pytest.mark.parametrize(
        "interval",
        [
            pytest.param("1d", id="daily"),
            pytest.param("1wk", id="weekly"),
            pytest.param("1mo", id="monthly"),
        ],
    )
    @patch("finance_mcp_server.mcp_servers.stock._ticker_history")
    async def test_custom_interval(self, mock_history, date_range, interval):
        mock_history.return_value = []
        start, end = date_range

        await get_stock_price(ticker="AAPL", start=start, end=end, interval=interval)

        call_args = mock_history.call_args[0]
        assert call_args[3] == interval

    @patch("finance_mcp_server.mcp_servers.stock._ticker_history")
    async def test_empty_result(self, mock_history, date_range):
        mock_history.return_value = []
        start, end = date_range

        result = await get_stock_price(ticker="INVALID", start=start, end=end)

        assert result == []

    @patch("finance_mcp_server.mcp_servers.stock._ticker_history")
    async def test_context_info_called_when_provided(self, mock_history, date_range):
        mock_history.return_value = [{"date": "2024-01-02", "close": 150.0}]
        start, end = date_range
        mock_ctx = AsyncMock()

        await get_stock_price(ticker="AAPL", start=start, end=end, ctx=mock_ctx)

        assert mock_ctx.info.call_count == 2


# ---------------------------------------------------------------------------
# get_multiple_stocks_prices (async tool)
# ---------------------------------------------------------------------------
class TestGetMultipleStocksPrices:
    """Tests for the get_multiple_stocks_prices MCP tool."""

    @patch("finance_mcp_server.mcp_servers.stock._ticker_history")
    async def test_returns_dict_keyed_by_ticker(self, mock_history, date_range):
        mock_history.side_effect = [
            [{"date": "2024-01-02", "close": 150.0}],
            [{"date": "2024-01-02", "close": 250.0}],
        ]
        start, end = date_range

        result = await get_multiple_stocks_prices(
            tickers=["AAPL", "MSFT"], start=start, end=end,
        )

        assert set(result.keys()) == {"AAPL", "MSFT"}
        assert len(result["AAPL"]) == 1
        assert len(result["MSFT"]) == 1

    @patch("finance_mcp_server.mcp_servers.stock._ticker_history")
    async def test_empty_results_for_invalid_tickers(self, mock_history, date_range):
        mock_history.return_value = []
        start, end = date_range

        result = await get_multiple_stocks_prices(
            tickers=["INVALID1", "INVALID2"], start=start, end=end,
        )

        assert result == {"INVALID1": [], "INVALID2": []}

    @pytest.mark.parametrize(
        "tickers",
        [
            pytest.param(["AAPL"], id="single-ticker"),
            pytest.param(["AAPL", "MSFT", "GOOGL"], id="three-tickers"),
        ],
    )
    @patch("finance_mcp_server.mcp_servers.stock._ticker_history")
    async def test_variable_ticker_count(self, mock_history, date_range, tickers):
        mock_history.return_value = [{"date": "2024-01-02", "close": 100.0}]
        start, end = date_range

        result = await get_multiple_stocks_prices(
            tickers=tickers, start=start, end=end,
        )

        assert len(result) == len(tickers)
        assert mock_history.call_count == len(tickers)

    @patch("finance_mcp_server.mcp_servers.stock._ticker_history")
    async def test_custom_interval_forwarded(self, mock_history, date_range):
        mock_history.return_value = []
        start, end = date_range

        await get_multiple_stocks_prices(
            tickers=["AAPL"], start=start, end=end, interval="1wk",
        )

        call_args = mock_history.call_args[0]
        assert call_args[3] == "1wk"
