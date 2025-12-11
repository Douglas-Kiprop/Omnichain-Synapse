# spoon_ai/tools/coinmarketcap_tool.py

import requests
import time
import os
import logging
from typing import Dict, Any, Optional
from pydantic import Field

from spoon_ai.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

class CoinMarketCapTool(BaseTool):
    """
    A multi-purpose tool to interact with the CoinMarketCap Professional API.
    Supports fetching current prices, 24h market metrics, and general market data
    for cryptocurrencies.
    
    Requires the COINMARKETCAP_API_KEY environment variable to be set.
    """
    name: str = Field(default="coinmarketcap_data", description="The name of the tool")
    description: str = Field(
        default="Get cryptocurrency data from CoinMarketCap (current price, market cap, 24h change).",
        description="A description of the tool"
    )
    parameters: dict = Field(
        default={
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "The crypto symbol (e.g., 'BTC', 'ETH', 'AVAX'). Max 10 symbols per call."
                },
                "vs_currency": {
                    "type": "string", 
                    "description": "The currency to convert the price against (e.g., 'USD', 'EUR', 'BTC').", 
                    "default": "USD"
                }
            },
            "required": ["symbol"]
        },
        description="Parameters for CoinMarketCap API calls"
    )

    def __init__(self):
        super().__init__()
        # CRITICAL: Reads the API key from environment variables
        self._api_key: Optional[str] = os.getenv("COINMARKETCAP_API_KEY")
        self._base_url: str = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        
        if not self._api_key:
            logger.warning("COINMARKETCAP_API_KEY not found in environment variables.")

    async def execute(self, symbol: str, vs_currency: str = "USD", **kwargs) -> ToolResult:
        """
        Fetches the latest quotes (price, market cap, volume) for the given symbol(s).
        """
        if not self._api_key:
            return ToolResult(error="Error: COINMARKETCAP_API_KEY is missing. Cannot fetch data.")
            
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self._api_key, 
        }
        
        # CMC requires IDs or Symbols, we are standardizing on Symbols here
        parameters = {
            'symbol': symbol.upper(),
            'convert': vs_currency.upper()
        }

        try:
            logger.info(f"Calling CoinMarketCap API: {self._base_url} for {symbol}")
            
            response = requests.get(
                self._base_url,
                headers=headers,
                params=parameters,
                timeout=10
            )
            response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
            data: Dict[str, Any] = response.json()

            # CMC returns a structured response; extract key data for the AI's use
            if data and data.get('data'):
                # Handle single symbol response (e.g., 'BTC')
                if symbol.upper() in data['data']:
                    coin_data = data['data'][symbol.upper()]
                    quote = coin_data['quote'][vs_currency.upper()]
                    
                    output = {
                        "symbol": coin_data['symbol'],
                        "name": coin_data['name'],
                        "price": quote['price'],
                        "market_cap": quote['market_cap'],
                        "volume_24h": quote['volume_24h'],
                        "percent_change_24h": quote['percent_change_24h'],
                        "last_updated": quote['last_updated'],
                        "source": "CoinMarketCap",
                    }
                    
                    return ToolResult(
                        output={
                            "function": "quotes_latest",
                            "data": output,
                            "summary": f"Current price of {symbol.upper()} is ${output['price']:,.2f} {vs_currency.upper()} (24h change: {output['percent_change_24h']:,.2f}%)",
                            "timestamp": int(time.time())
                        }
                    )
            
            # Catch cases where symbol is not found or API returns an unexpected structure
            error_message = data.get('status', {}).get('error_message', f"Symbol '{symbol}' not found or API returned an unexpected response.")
            logger.error(f"CoinMarketCap API data error: {error_message}")
            return ToolResult(error=error_message)


        except requests.exceptions.HTTPError as e:
            # Handle specific API errors (400, 401, 429)
            if response.status_code == 429:
                 error_msg = f"CoinMarketCap API Error: Rate limit exceeded (429). Please wait a minute and try again."
            else:
                 error_msg = f"CoinMarketCap API HTTP Error: {e}. Detail: {response.text}"
            logger.error(error_msg)
            return ToolResult(error=error_msg)
        
        except requests.exceptions.RequestException as e:
            # Handle connection or timeout errors
            error_msg = f"CoinMarketCap Connection Error: {str(e)}"
            logger.error(error_msg)
            return ToolResult(error=error_msg)
        
        except Exception as e:
            logger.error(f"Unexpected error in CoinMarketCapTool: {e}")
            return ToolResult(error=f"Unexpected tool error: {str(e)}")


# Example test
if __name__ == "__main__":
    tool = CoinMarketCapTool()
    import asyncio
    async def test():
        # Requires COINMARKETCAP_API_KEY to be set in your environment for this test to pass
        print(await tool.execute(symbol="BTC", vs_currency="USD"))
        print(await tool.execute(symbol="ETH"))
        print(await tool.execute(symbol="XRP", vs_currency="USD"))

    asyncio.run(test())