# spoon-core/spoon_ai/tools/premium_chainbase_tool.py
import os
import requests
import logging
from typing import Optional, Dict, Any
from pydantic import Field, PrivateAttr

from spoon_ai.tools.base import BaseTool
# Import the context getter and verification logic
from spoon_ai.x402.context import get_txn_hash
from spoon_ai.x402.verifier import verify_payment
from spoon_ai.utils.config import TREASURY_ADDRESS, PREMIUM_TOOL_FEE_WEI

logger = logging.getLogger(__name__)

class PaymentRequiredException(Exception):
    """
    Raised when a tool requires payment but a valid transaction hash is missing.
    The Server catches this and converts it to a 402 HTTP response.
    """
    def __init__(self, payment_details: dict):
        self.payment_details = payment_details
        super().__init__("Payment required")

class PremiumChainbaseTool(BaseTool):
    """
    A premium tool that interacts with Chainbase API.
    Checks x402 payment context before execution.
    """
    name: str = Field("premium_chainbase", frozen=True)
    description: str = Field(
        "Get real-time on-chain data like wallet transactions or token balances. Premium tool.",
        frozen=True
    )

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
                }
            },
            "required": ["wallet_address"]
        },
        frozen=True
    )

    _api_key: str = PrivateAttr()
    _base_url: str = PrivateAttr()

    def __init__(self):
        super().__init__()
        self._api_key = os.getenv("CHAINBASE_API_KEY")
        if not self._api_key:
            # It's better to log a warning than crash if not using the tool, 
            # but for premium tools strictly requiring it, raising is fine.
            logger.warning("CHAINBASE_API_KEY not found in .env")
        self._base_url = "https://api.chainbase.online/v1/"

    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        if not self._api_key:
            return {"error": "Server configuration error: Missing API Key"}
            
        headers = {"x-api-key": self._api_key}
        url = f"{self._base_url}{endpoint}"
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Chainbase API error: {e}")
            return {"error": str(e)}

    async def execute(
        self, 
        wallet_address: str, 
        chain_id: int = 1, 
        query_type: str = "balances",
        **kwargs # Catch generic kwargs
    ) -> str:
        """
        Executes the tool with implicit payment verification from context.
        """
        # 1. RETRIEVE HASH FROM CONTEXT (Thread-safe)
        txn_hash = get_txn_hash()
        
        logger.info(f"[PremiumChainbaseTool] Checking payment. Hash provided: {txn_hash}")

        # 2. VERIFY PAYMENT
        if not txn_hash or not verify_payment(txn_hash):
            logger.warning("[PremiumChainbaseTool] Payment verification failed")
            
            # Raise exception with payment metadata
            raise PaymentRequiredException({
                "amount": "0.0005",
                "amount_wei": str(PREMIUM_TOOL_FEE_WEI),
                "recipient": TREASURY_ADDRESS,
                "chain": "avalanche",
                "description": "Access premium_chainbase",
                "tool_name": "premium_chainbase"
            })

        logger.info(f"[PremiumChainbaseTool] Payment verified. Executing {query_type}...")

        # 3. EXECUTE LOGIC
        if query_type == "transactions":
            result = self._make_request("account/txs", {"chain_id": chain_id, "address": wallet_address})
        elif query_type == "balances":
            result = self._make_request("account/balance", {"chain_id": chain_id, "address": wallet_address})
        else:
            return f"Invalid query_type '{query_type}'."

        return f"Premium Chainbase Result:\n{result}"