import httpx
from core.config import settings

async def get_market_data(vs_currency: str = "usd", limit: int = 250, timeframe: str = "24h"):
    """
    Fetches market data for a list of cryptocurrencies from CoinGecko.
    """
    url = f"https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": vs_currency,
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": timeframe
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            return data
        except httpx.HTTPStatusError as e:
            # In a real application, you'd want to log this error
            print(f"HTTP error occurred: {e}")
            return None
        except httpx.RequestError as e:
            # And this one too
            print(f"An error occurred while requesting from CoinGecko: {e}")
            return None