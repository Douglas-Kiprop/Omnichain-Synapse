import requests
import time
from spoon_ai.tools.base import BaseTool, ToolResult
import logging
from pydantic import Field

logger = logging.getLogger(__name__)

class CoinGeckoTool(BaseTool):
    """
    A multi-purpose tool to interact with the CoinGecko API for various cryptocurrency data.
    Supports fetching prices, contract-based prices, market data, historical data, and trending coins.
    """
    name: str = Field(default="coingecko_price", description="The name of the tool")
    description: str = Field(
        default="Get cryptocurrency data from CoinGecko (price, contract price, market data, historical data, trending).",
        description="A description of the tool"
    )
    parameters: dict = Field(
        default={
            "type": "object",
            "properties": {
                "function": {
                    "type": "string",
                    "description": "The type of data to fetch",
                    "enum": [
                        "price", "contract_price", "market_data", "historical", "trending"
                    ],
                    "default": "price"
                },
                "coin_id": {"type": "string", "description": "The ID of the coin (e.g., 'bitcoin')"},
                "vs_currency": {"type": "string", "description": "Currency to compare against (e.g., 'usd')", "default": "usd"},
                "contract_address": {"type": "string", "description": "Token contract address (for contract_price)"},
                "platform_id": {"type": "string", "description": "Platform ID (e.g., 'ethereum') for contract_price"},
                "date": {"type": "string", "description": "Date for historical data in 'dd-mm-yyyy' format"}
            },
            "required": ["function"]
        },
        description="Parameters for CoinGecko API calls"
    )

    def __init__(self):
        super().__init__()
        logger.info("Initializing CoinGeckoTool")

    async def execute(self, function: str, **kwargs) -> ToolResult:
        """
        Executes the requested CoinGecko API call based on the function parameter.
        """
        try:
            base_url = "https://api.coingecko.com/api/v3"

            if function == "price":
                coin_id = kwargs.get("coin_id")
                vs_currency = kwargs.get("vs_currency", "usd")
                url = f"{base_url}/simple/price"
                params = {"ids": coin_id, "vs_currencies": vs_currency}

            elif function == "contract_price":
                platform_id = kwargs.get("platform_id")
                contract_address = kwargs.get("contract_address")
                vs_currency = kwargs.get("vs_currency", "usd")
                url = f"{base_url}/simple/token_price/{platform_id}"
                params = {"contract_addresses": contract_address, "vs_currencies": vs_currency}

            elif function == "market_data":
                coin_id = kwargs.get("coin_id")
                url = f"{base_url}/coins/{coin_id}"
                params = {"localization": "false"}

            elif function == "historical":
                coin_id = kwargs.get("coin_id")
                date = kwargs.get("date")
                url = f"{base_url}/coins/{coin_id}/history"
                params = {"date": date, "localization": "false"}

            elif function == "trending":
                url = f"{base_url}/search/trending"
                params = {}

            else:
                return ToolResult(error=f"Unknown function '{function}'")

            logger.info(f"Calling CoinGecko API: {url} with {params}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            return ToolResult(
                output={
                    "function": function,
                    "data": data,
                    "timestamp": int(time.time())
                }
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"CoinGecko API error: {e}")
            return ToolResult(error=str(e))
        except Exception as e:
            logger.error(f"Unexpected error in CoinGeckoTool: {e}")
            return ToolResult(error=str(e))


# Example test
if __name__ == "__main__":
    tool = CoinGeckoTool()
    import asyncio
    async def test():
        print(await tool.execute(function="price", coin_id="bitcoin", vs_currency="usd"))
        print(await tool.execute(function="trending"))
    asyncio.run(test())
