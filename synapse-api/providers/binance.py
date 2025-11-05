import httpx
from datetime import datetime
from typing import List

async def get_klines(symbol: str, interval: str, limit: int = 500):
    """
    Fetches kline/candlestick data from Binance.

    :param symbol: Trading pair symbol (e.g., 'BTCUSDT').
    :param interval: Kline interval (e.g., '1m', '5m', '1h', '4h', '1d').
    :param limit: Number of data points to retrieve (max 1000).
    :return: A list of kline data.
    """
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": min(limit, 1000)  # Ensure limit does not exceed 1000
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Process the raw kline data into a more structured format
            processed_data = []
            for kline in data:
                # Binance kline data format:
                # [
                #   1499040000000,      // Open time
                #   "0.01634790",       // Open
                #   "0.80000000",       // High
                #   "0.01575800",       // Low
                #   "0.01577100",       // Close
                #   "148976.11427815",  // Volume
                #   1499644799999,      // Close time
                #   "2434.19055334",    // Quote asset volume
                #   308,                // Number of trades
                #   "1756.87402397",    // Taker buy base asset volume
                #   "28.46694368",      // Taker buy quote asset volume
                #   "17928899.62484339" // Ignore
                # ]
                processed_data.append({
                    "open_time": datetime.fromtimestamp(kline[0] / 1000),
                    "open": float(kline[1]),
                    "high": float(kline[2]),
                    "low": float(kline[3]),
                    "close": float(kline[4]),
                    "volume": float(kline[5]),
                    "close_time": datetime.fromtimestamp(kline[6] / 1000),
                    "quote_asset_volume": float(kline[7]),
                    "trade_count": int(kline[8]),
                    "taker_buy_base_asset_volume": float(kline[9]),
                    "taker_buy_quote_asset_volume": float(kline[10]),
                })
            return processed_data

        except httpx.HTTPStatusError as e:
            # In a real application, you'd want to log this error
            print(f"HTTP error occurred: {e}")
            return None
        except httpx.RequestError as e:
            # And this one too
            print(f"An error occurred while requesting from Binance: {e}")
            return None