# spoon_ai/tools/premium_strategy_builder.py

import os
import requests
import json
import uuid
import logging
from typing import Optional, List, Dict, Any
from pydantic import Field, PrivateAttr

from spoon_ai.tools.base import BaseTool
# --- NEW IMPORT ---
from spoon_ai.x402.context import get_txn_hash, get_user_privy_token 
# --- END NEW IMPORT ---
from spoon_ai.x402.verifier import verify_payment
from spoon_ai.utils.config import TREASURY_ADDRESS, PREMIUM_TOOL_FEE_WEI

# Re-use the exception for the 402 flow
from spoon_ai.tools.premium_chainbase_tool import PaymentRequiredException

logger = logging.getLogger(__name__)

class PremiumStrategyBuilderTool(BaseTool):
    """
    A premium tool that builds and saves executable trading strategies to the Synapse API.
    It constructs a schema-compliant JSON payload for the monitoring engine.
    Requires 0.0005 AVAX payment and Privy Token authentication.
    """
    name: str = Field("premium_strategy_builder", frozen=True)
    description: str = Field(
        "Builds and saves a technical analysis trading strategy to the Synapse Engine. "
        "Can create strategies based on a technical indicator (e.g., RSI) AND an optional price threshold. "
        "PREMIUM TOOL: Requires payment and user login.",
        frozen=True
    )
    
    parameters: dict = Field(
        {
            "type": "object",
            "properties": {
                "strategy_name": {
                    "type": "string",
                    "description": "Unique name for the strategy (e.g., 'BTC RSI Dip')"
                },
                "asset_pair": {
                    "type": "string",
                    "description": "The trading pair symbol (e.g., 'BTC', 'ETH', 'AVAX')"
                },
                "indicator": {
                    "type": "string",
                    "description": "Technical indicator to use (e.g., 'rsi', 'sma', 'ema', 'macd', 'bollinger')"
                },
                "condition_operator": {
                    "type": "string",
                    "enum": ["gt", "lt", "eq", "cross_above", "cross_below"],
                    "description": "Comparison operator for the indicator (gt=greater than, lt=less than)"
                },
                "threshold_value": {
                    "type": "number",
                    "description": "The value to compare the indicator against (e.g., 30 for RSI)"
                },
                "price_operator": {
                    "type": "string",
                    "enum": ["above", "below"],
                    "description": "Optional: Direction for a secondary price alert (e.g., 'above' or 'below')"
                },
                "price_threshold": {
                    "type": "number",
                    "description": "Optional: The specific price to alert on (e.g., 50000 for BTC)"
                },
                "timeframe": {
                    "type": "string",
                    "enum": ["1m", "5m", "15m", "30m", "1h", "4h", "12h", "1d"],
                    "description": "Candle timeframe for analysis",
                    "default": "1h"
                },
                "risk_description": {
                    "type": "string",
                    "description": "Brief description of the logic for the user"
                }
            },
            "required": ["strategy_name", "asset_pair", "indicator", "condition_operator", "threshold_value"]
        },
        frozen=True
    )

    _api_url: str = PrivateAttr()
    
    def __init__(self):
        super().__init__()
        # Configuration for connecting to synapse-api
        self._api_url = os.getenv("SYNAPSE_API_URL", "http://localhost:8000")

    async def execute(
        self, 
        strategy_name: str, 
        asset_pair: str, 
        indicator: str,
        condition_operator: str,
        threshold_value: float,
        price_operator: Optional[str] = None,
        price_threshold: Optional[float] = None,
        timeframe: str = "1h",
        risk_description: str = "AI Generated Strategy",
        **kwargs
    ) -> str:
        """
        Executes the strategy creation with x402 payment gating and Privy Token authentication.
        """
        # 1. RETRIEVE HASH FROM CONTEXT (x402 Payment)
        txn_hash = get_txn_hash()
        
        logger.info(f"[PremiumStrategyBuilder] Request: {strategy_name}. Hash: {txn_hash}")

        # 2. VERIFY PAYMENT (The Gate)
        if not txn_hash or not verify_payment(txn_hash):
            logger.warning("[PremiumStrategyBuilder] Payment verification failed")
            
            # Raise exception to trigger the 402 Flow
            raise PaymentRequiredException({
                "amount": "0.0005",
                "amount_wei": "500000000000000",
                "recipient": TREASURY_ADDRESS,
                "chain": "avalanche",
                "description": f"Build Strategy: {strategy_name}",
                "tool_name": "premium_strategy_builder"
            })

        logger.info("[PremiumStrategyBuilder] Payment verified. Constructing payload...")

        # 3. GET USER AUTHENTICATION TOKEN
        privy_token = get_user_privy_token()
        if not privy_token:
            logger.error("[PremiumStrategyBuilder] Privy Token missing in context. Cannot save strategy.")
            return "Error: User authentication token is missing. Please ensure you are logged in."

        # 4. CONSTRUCT STRICT SCHEMA PAYLOAD (Updated for multiple conditions)
        
        conditions_list = []
        logic_refs = []
        full_description = f"Logic: {indicator.upper()} {condition_operator} {threshold_value}"

        # --- CONDITION 1: TECHNICAL INDICATOR (REQUIRED) ---
        condition_uuid_1 = str(uuid.uuid4())
        tech_payload = {
            "indicator": indicator.lower(),
            "params": {"period": 14},
            "operator": condition_operator,
            "value": threshold_value,
            "asset": asset_pair.upper(),
            "timeframe": timeframe
        }
        conditions_list.append({
            "id": condition_uuid_1,
            "type": "technical_indicator",
            "payload": tech_payload,
            "label": f"{indicator.upper()} {condition_operator} {threshold_value}",
            "enabled": True
        })
        logic_refs.append({"ref": condition_uuid_1})
        

        # --- CONDITION 2: PRICE ALERT (OPTIONAL) ---
        if price_operator and price_threshold is not None:
            condition_uuid_2 = str(uuid.uuid4())
            price_payload = {
                "asset": asset_pair.upper(),
                "direction": price_operator.lower(),
                "target_price": price_threshold,
            }
            conditions_list.append({
                "id": condition_uuid_2,
                "type": "price_alert",
                "payload": price_payload,
                "label": f"Price {price_operator.upper()} {price_threshold}",
                "enabled": True
            })
            logic_refs.append({"ref": condition_uuid_2})
            full_description += f" AND Price {price_operator.upper()} {price_threshold}"


        # Construct Logic Tree (uses AND if multiple conditions exist, or just the single condition if only one)
        logic_tree = {
            "operator": "AND",
            "conditions": logic_refs
        }

        # Construct Full Strategy Payload
        strategy_payload = {
            "name": strategy_name,
            "description": f"{risk_description}. {full_description}",
            "schedule": "1m",
            "assets": [asset_pair.upper()],
            "notification_preferences": {
                "channels": {
                    "email": {"enabled": True, "email": "demo@synapse.com"} 
                },
                "alert_on": {"trigger": True, "error": True},
                "cooldown": {"enabled": True, "duration": "1h"}
            },
            "conditions": conditions_list, # Sends 1 or 2 conditions
            "logic_tree": logic_tree,
            "status": "active"
        }

        # 5. SEND TO SYNAPSE API (Updated URL and Header)
        try:
            headers = {
                "Content-Type": "application/json",
                # CRITICAL CHANGE: Use the retrieved Privy Token for authentication
                "Authorization": f"Bearer {privy_token}" 
            }
            
            # CRITICAL CHANGE: Target the new secure endpoint
            url = f"{self._api_url}/strategies/agent" 
            
            logger.info(f"[PremiumStrategyBuilder] Posting to {url} with Privy Token...")
            
            response = requests.post(
                url, 
                json=strategy_payload,
                headers=headers,
                timeout=10
            )
            
            # Handle API responses
            if response.status_code in [200, 201]:
                data = response.json()
                strategy_id = data.get('id', 'unknown')
                return (
                    f"✅ **Strategy Built & Deployed!**\n\n"
                    f"**Name:** {strategy_name}\n"
                    f"**ID:** `{strategy_id}`\n"
                    f"**Status:** Active 🟢\n\n"
                    f"The monitoring service is now tracking **{asset_pair}** for **{full_description.replace('Logic: ', '')}**. "
                    f"The strategy is saved to your dashboard and you will be notified when this condition is met."
                )
            
            elif response.status_code in [401, 403]:
                logger.error(f"Synapse API Auth Error ({response.status_code}): Token Rejected.")
                return (
                    f"Error: Authentication failed with the strategy engine. "
                    f"Please verify your login session and try again. The token was rejected."
                )

            else:
                response_detail = response.json().get('detail', response.text)
                logger.error(f"Synapse API Error ({response.status_code}): {response_detail}")
                return f"Failed to save strategy. API Error: {response_detail}"

        except Exception as e:
            logger.error(f"Strategy Builder Connection Error: {e}")
            return f"Error connecting to Strategy Engine: {str(e)}"