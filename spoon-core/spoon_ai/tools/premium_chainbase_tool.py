# spoon-core/spoon_ai/tools/premium_chainbase_tool.py
import os
import requests
from dotenv import load_dotenv
from typing import Optional
from spoon_ai.tools.base import BaseTool
from spoon_ai.x402.verifier import verify_payment
from fastapi import HTTPException
from spoon_ai.utils.config import TREASURY_ADDRESS, PREMIUM_TOOL_FEE_WEI
from pydantic import Field, PrivateAttr

load_dotenv()

class PremiumChainbaseTool(BaseTool):
    """
    A tool to interact with the Chainbase API for blockchain data.
    This is a premium tool requiring payment for access.
    """
    name: str = Field("premium_chainbase", frozen=True)
    description: str = Field(
        "Get real-time on-chain data like wallet transactions or token balances (premium: requires 0.0005 AVAX payment)",
        frozen=True
    )

    # Required for tool schema
    parameters: dict = Field(
        {
            "type": "object",
            "properties": {
                "wallet_address": {
                    "type": "string",
                    "description": "The wallet address to query"
                },
                "chain_id": {
                    "type": "integer",
                    "description": "Chain ID (1=Ethereum, 56=BSC, etc.)",
                    "default": 1
                },
                "query_type": {
                    "type": "string",
                    "enum": ["balances", "transactions"],
                    "description": "Type of data to fetch",
                    "default": "balances"
                },
                "txn_hash": {
                    "type": "string",
                    "description": "Transaction hash proving payment (required for premium access)"
                }
            },
            "required": ["wallet_address", "txn_hash"]
        },
        frozen=True
    )

    # Private attributes for internal state (not model fields)
    _api_key: str = PrivateAttr()
    _base_url: str = PrivateAttr()

    def __init__(self):
        super().__init__()
        self._api_key = os.getenv("CHAINBASE_API_KEY")
        if not self._api_key:
            raise ValueError("CHAINBASE_API_KEY not found in .env")
        self._base_url = "https://api.chainbase.online/v1/"
        print(f"[DEBUG] PremiumChainbaseTool API Key loaded: {self._api_key is not None}")

    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        headers = {"x-api-key": self._api_key}
        url = f"{self._base_url}{endpoint}"
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_wallet_transactions(self, wallet_address: str, chain_id: int = 1) -> dict:
        return self._make_request("account/txs", {"chain_id": chain_id, "address": wallet_address})

    def get_token_balances(self, wallet_address: str, chain_id: int = 1) -> dict:
        return self._make_request("account/balance", {"chain_id": chain_id, "address": wallet_address})

    async def execute(self, wallet_address: str, chain_id: int = 1, query_type: str = "balances", txn_hash: Optional[str] = None) -> str:
        # Verify payment for premium access
        if not txn_hash or not verify_payment(txn_hash):
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "Payment required",
                    "payment": {
                        "amount": "0.0005",
                        "amount_wei": str(PREMIUM_TOOL_FEE_WEI),
                        "recipient": TREASURY_ADDRESS,
                        "description": "Access premium_chainbase"
                    }
                }
            )

        # Execute the requested query type
        if query_type == "transactions":
            result = self.get_wallet_transactions(wallet_address, chain_id)
        elif query_type == "balances":
            result = self.get_token_balances(wallet_address, chain_id)
        else:
            return f"Invalid query_type '{query_type}'. Use 'transactions' or 'balances'."

        return f"Premium Chainbase Result:\n{result}"

# Example Usage (for testing purposes, remove in production)
if __name__ == "__main__":
    # Ensure you have CHAINBASE_API_KEY set in your .env file
    # For example: CHAINBASE_API_KEY="your_chainbase_api_key"
    try:
        chainbase_tool = PremiumChainbaseTool()
        # Replace with a real wallet address for testing
        test_wallet_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Example: Vitalik Buterin's wallet

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