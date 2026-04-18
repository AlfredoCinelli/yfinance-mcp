"""Yahoo Finance Stock prices MCP Server."""

import asyncio
from datetime import date
from typing import Annotated

import yfinance as yf
from fastmcp import Context, FastMCP
from loguru import logger
from pydantic import Field

mcp = FastMCP(
    name="Finance MCP Server",
    instructions="Provides tools to fetch historical stock price data from Yahoo Finance.",
)


def _ticker_history(
        ticker: str,
        start: date,
        end: date,
        interval: str,
    ) -> list[dict]:
    """Fetch OHLCV history for one ticker and return [{date, close}, ...] records.

    Args:
        ticker: identifier of the financial product (e.g., 'AAPL' for Apple stock)
        start: start date from which fetching product information
        end: end date to which fetching product information
        interval: time interval at which fetch is performed (e.g., '1d' at daily level)

    Returns:
        list of dictionaries where each dictionary has date and closing price in an
            interval unit (e.g., daily closing prices for Apple stock)
    """
    t = yf.Ticker(ticker)
    df = t.history(
        start=start.isoformat(),
        end=end.isoformat(),
        interval=interval,
        auto_adjust=True,
    )
    if df.empty:
        return []
    df.index = df.index.strftime("%Y-%m-%d")
    return [
        {"date": idx, "close": round(float(row["Close"]), 4)}
        for idx, row in df.iterrows()
    ]


@mcp.tool
async def get_stock_price(
    ticker: Annotated[str, Field(description="Stock ticker symbol, e.g. 'AAPL'")],
    start: Annotated[date, Field(description="Start date (inclusive), e.g. '2024-01-01'")],
    end: Annotated[date, Field(description="End date (inclusive), e.g. '2024-12-31'")],
    interval: Annotated[
        str,
        Field(
            description="Data interval. Valid values: '1d', '1wk', '1mo'. Defaults to '1d'.",
            pattern="^(1d|1wk|1mo)$",
        ),
    ] = "1d",
    ctx: Context = None,
) -> list[dict]:
    """Fetch historical closing prices for a single stock over a given time period.

    Args:
        ticker: Stock ticker symbol, e.g. 'AAPL'.
        start: Start date (inclusive) for the historical data.
        end: End date (inclusive) for the historical data.
        interval: Data frequency. One of '1d' (daily), '1wk' (weekly), '1mo' (monthly).
        ctx: FastMCP context.

    Returns:
        A list of dicts with 'date' (YYYY-MM-DD) and 'close' (float) keys,
        ordered chronologically. Returns an empty list if no data is found.
    """
    logger.info("get_stock_price called: ticker=%s start=%s end=%s interval=%s", ticker, start, end, interval)
    if ctx:
        await ctx.info(f"Fetching {ticker} from {start} to {end} (interval={interval})")
    records = await asyncio.to_thread(_ticker_history, ticker, start, end, interval)
    logger.info("get_stock_price returned %d records for %s", len(records), ticker)
    if ctx:
        await ctx.info(f"Returned {len(records)} records for {ticker}")
    return records


@mcp.tool
async def get_multiple_stocks_prices(
    tickers: Annotated[
        list[str],
        Field(description="List of stock ticker symbols, e.g. ['AAPL', 'MSFT', 'GOOGL']"),
    ],
    start: Annotated[date, Field(description="Start date (inclusive), e.g. '2024-01-01'")],
    end: Annotated[date, Field(description="End date (inclusive), e.g. '2024-12-31'")],
    interval: Annotated[
        str,
        Field(
            description="Data interval. Valid values: '1d', '1wk', '1mo'. Defaults to '1d'.",
            pattern="^(1d|1wk|1mo)$",
        ),
    ] = "1d",
    ctx: Context = None,
) -> dict[str, list[dict]]:
    """Fetch historical closing prices for multiple stocks over a given time period.

    Args:
        tickers: List of stock ticker symbols, e.g. ['AAPL', 'MSFT', 'GOOGL'].
        start: Start date (inclusive) for the historical data.
        end: End date (inclusive) for the historical data.
        interval: Data frequency. One of '1d' (daily), '1wk' (weekly), '1mo' (monthly).
        ctx: FastMCP context.

    Returns:
        A dict keyed by ticker symbol. Each value is a list of dicts with
        'date' (YYYY-MM-DD) and 'close' (float) keys, ordered chronologically.
        Tickers with no data map to an empty list.
    """
    logger.info("get_multiple_stocks_prices called: tickers=%s start=%s end=%s interval=%s", tickers, start, end, interval)
    if ctx:
        await ctx.info(f"Fetching {len(tickers)} tickers from {start} to {end} (interval={interval})")
    tasks = [asyncio.to_thread(_ticker_history, ticker, start, end, interval) for ticker in tickers]
    results = await asyncio.gather(*tasks)
    result = dict(zip(tickers, results, strict=True))
    for ticker, records in result.items():
        logger.info("  %s -> %d records", ticker, len(records))
        if ctx:
            await ctx.info(f"  {ticker} -> {len(records)} records")
    return result
