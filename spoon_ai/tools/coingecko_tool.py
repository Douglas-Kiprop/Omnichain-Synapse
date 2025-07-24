import requests

class CoinGeckoTool:
    """
    A tool to interact with the CoinGecko API for cryptocurrency data.
    """
    def __init__(self):
        self.name = "CoinGeckoTool" # Add this line
        self.base_url = "https://api.coingecko.com/api/v3/"

    def _make_request(self, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def get_coin_price(self, coin_id: str, vs_currency: str = "usd"):
        """
        Retrieves the current price of a cryptocurrency.

        Args:
            coin_id (str): The ID of the coin (e.g., "bitcoin", "ethereum").
            vs_currency (str): The currency to compare against (e.g., "usd", "eur").

        Returns:
            dict: A dictionary containing the coin's price or an error message.
        """
        endpoint = "simple/price"
        params = {"ids": coin_id, "vs_currencies": vs_currency}
        return self._make_request(endpoint, params)

    def get_coin_market_chart(self, coin_id: str, vs_currency: str = "usd", days: str = "1"):
        """
        Retrieves historical market data for a cryptocurrency.

        Args:
            coin_id (str): The ID of the coin.
            vs_currency (str): The currency to compare against.
            days (str): Data granularity (e.g., "1", "7", "30", "max").

        Returns:
            dict: A dictionary containing market chart data or an error message.
        """
        endpoint = f"coins/{coin_id}/market_chart"
        params = {"vs_currency": vs_currency, "days": days}
        return self._make_request(endpoint, params)

# Example Usage (for testing purposes, remove in production)
if __name__ == "__main__":
    try:
        coingecko_tool = CoinGeckoTool()

        print("Fetching Bitcoin price in USD...")
        btc_price = coingecko_tool.get_coin_price("bitcoin")
        print("Bitcoin Price:", btc_price)

        print("Fetching Ethereum market chart for the last 7 days...")
        eth_chart = coingecko_tool.get_coin_market_chart("ethereum", days="7")
        print("Ethereum Market Chart (last 7 days):")
        # Print only a snippet to avoid large output
        if eth_chart and 'prices' in eth_chart:
            print(eth_chart['prices'][:5]) # Print first 5 data points
        else:
            print(eth_chart)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")