import requests
import time
from spoon_ai.tools.base import BaseTool, ToolResult
import logging
from pydantic import Field

logger = logging.getLogger(__name__)

class CoinGeckoTool(BaseTool):
    """
    A tool to interact with the CoinGecko API for cryptocurrency data.
    """
    name: str = Field(default="coingecko_price", description="The name of the tool")
    description: str = Field(default="Get the current price of a cryptocurrency using CoinGecko API.", description="A description of the tool")
    parameters: dict = Field(
        default={
            "type": "object",
            "properties": {
                "coin_id": {"type": "string", "description": "The ID of the coin (e.g., 'bitcoin', 'neo')"},
                "vs_currency": {"type": "string", "description": "The currency to compare against (e.g., 'usd')", "default": "usd"}
            },
            "required": ["coin_id"]
        },
        description="Input parameters for the CoinGecko price query"
    )

    def __init__(self):
        super().__init__()
        logger.info("Initializing CoinGeckoTool")

    async def execute(self, coin_id: str, vs_currency: str = "usd") -> ToolResult:
        """
        Retrieves the current price of a cryptocurrency.

        Args:
            coin_id (str): The ID of the coin (e.g., "bitcoin", "ethereum").
            vs_currency (str): The currency to compare against (e.g., "usd", "eur").

        Returns:
            ToolResult: A ToolResult object containing the coin's price or an error message.
        """
        logger.info(f"Fetching price for {coin_id} in {vs_currency} using CoinGecko")
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": coin_id, "vs_currencies": vs_currency}
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if coin_id in data and vs_currency in data[coin_id]:
                return ToolResult(
                    output={
                        "price": str(data[coin_id][vs_currency]),
                        "pair": f"{coin_id.upper()}-{vs_currency.upper()}",
                        "timestamp": int(time.time())
                    }
                )
            return ToolResult(
                error=f"No price data for {coin_id} in {vs_currency}",
                output={"price": "0", "pair": f"{coin_id.upper()}-{vs_currency.upper()}", "timestamp": int(time.time())}
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"CoinGecko API error: {e}")
            return ToolResult(error=str(e))

# Example Usage (for testing purposes, remove in production)
if __name__ == "__main__":
    try:
        coingecko_tool = CoinGeckoTool()
        print("Fetching Bitcoin price in USD...")
        btc_price = coingecko_tool.execute(coin_id="bitcoin")
        print("Bitcoin Price:", btc_price)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")