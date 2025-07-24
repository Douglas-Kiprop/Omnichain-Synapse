import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ChainbaseTool:
    """
    A tool to interact with the Chainbase API for blockchain data.
    """
    def __init__(self):
        self.name = "ChainbaseTool"
        try:
            self.api_key = os.getenv("CHAINBASE_API_KEY")
            print(f"[DEBUG] ChainbaseTool API Key loaded: {self.api_key is not None}")
            if not self.api_key:
                raise ValueError("CHAINBASE_API_KEY not found in .env file")
            self.base_url = "https://api.chainbase.online/v1/"
        except Exception as e:
            print(f"[ERROR] Error during ChainbaseTool initialization: {e}")
            raise # Re-raise the exception to ensure it's caught by the agent's try-except

    def _make_request(self, endpoint, params=None):
        headers = {"x-api-key": self.api_key}
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def get_wallet_transactions(self, wallet_address: str, chain_id: int = 1):
        """
        Retrieves transactions for a given wallet address on a specific blockchain.

        Args:
            wallet_address (str): The blockchain wallet address.
            chain_id (int): The ID of the blockchain (e.g., 1 for Ethereum).

        Returns:
            dict: A dictionary containing transaction data or an error message.
        """
        # This endpoint might need further verification from Chainbase API docs
        endpoint = f"account/txs"
        params = {"chain_id": chain_id, "address": wallet_address}
        return self._make_request(endpoint, params)

    def get_token_balances(self, wallet_address: str, chain_id: int = 1):
        """
        Retrieves token balances for a given wallet address on a specific blockchain.

        Args:
            wallet_address (str): The blockchain wallet address.
            chain_id (int): The ID of the blockchain (e.g., 1 for Ethereum).

        Returns:
            dict: A dictionary containing token balance data or an error message.
        """
        endpoint = f"account/balance"
        params = {"chain_id": chain_id, "address": wallet_address}
        return self._make_request(endpoint, params)

# Example Usage (for testing purposes, remove in production)
if __name__ == "__main__":
    # Ensure you have CHAINBASE_API_KEY set in your .env file
    # For example: CHAINBASE_API_KEY="your_chainbase_api_key"
    try:
        chainbase_tool = ChainbaseTool()
        # Replace with a real wallet address for testing
        test_wallet_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045" # Example: Vitalik Buterin's wallet

        print(f"Fetching transactions for {test_wallet_address}...")
        transactions = chainbase_tool.get_wallet_transactions(test_wallet_address)
        print("Transactions:", transactions)

        print(f"Fetching token balances for {test_wallet_address}...")
        balances = chainbase_tool.get_token_balances(test_wallet_address)
        print("Token Balances:", balances)

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")