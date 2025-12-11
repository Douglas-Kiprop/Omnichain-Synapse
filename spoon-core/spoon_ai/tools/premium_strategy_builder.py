# spoon_ai/tools/premium_strategy_builder.py

import os
import requests
import json
import uuid
import logging
from typing import Optional, List, Dict, Any
from pydantic import Field, PrivateAttr

from spoon_ai.tools.base import BaseTool
from spoon_ai.x402.context import get_txn_hash
from spoon_ai.x402.verifier import verify_payment
from spoon_ai.utils.config import TREASURY_ADDRESS, PREMIUM_TOOL_FEE_WEI

# Re-use the exception for the 402 flow
from spoon_ai.tools.premium_chainbase_tool import PaymentRequiredException

logger = logging.getLogger(__name__)

class PremiumStrategyBuilderTool(BaseTool):
    """
    A premium tool that builds and saves executable trading strategies to the Synapse API.
    It constructs a schema-compliant JSON payload for the monitoring engine.
    Requires 0.0005 AVAX payment.
    """
    name: str = Field("premium_strategy_builder", frozen=True)
    description: str = Field(
        "Builds and saves a technical analysis trading strategy to the Synapse Engine. "
        "Requires parameters for asset, indicator, threshold, and logic. "
        "PREMIUM TOOL: Requires payment.",
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
                    "description": "Technical indicator to use (e.g., 'rsi', 'sma', 'ema')"
                },
                "condition_operator": {
                    "type": "string",
                    "enum": ["gt", "lt", "eq", "cross_above", "cross_below"],
                    "description": "Comparison operator (gt=greater than, lt=less than)"
                },
                "threshold_value": {
                    "type": "number",
                    "description": "The value to compare against (e.g., 30 for RSI, 50000 for price)"
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
    _api_token: str = PrivateAttr()

    def __init__(self):
        super().__init__()
        # Configuration for connecting to synapse-api
        self._api_url = os.getenv("SYNAPSE_API_URL", "http://localhost:8000")
        self._api_token = os.getenv("SYNAPSE_API_TOKEN", "") # Bearer token for a demo user

    async def execute(
        self, 
        strategy_name: str, 
        asset_pair: str, 
        indicator: str,
        condition_operator: str,
        threshold_value: float,
        timeframe: str = "1h",
        risk_description: str = "AI Generated Strategy",
        **kwargs
    ) -> str:
        """
        Executes the strategy creation with x402 payment gating and strict schema construction.
        """
        # 1. RETRIEVE HASH FROM CONTEXT
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

        logger.info(f"[PremiumStrategyBuilder] Payment verified. Constructing payload...")

        # 3. CONSTRUCT STRICT SCHEMA PAYLOAD
        # We must generate a UUID for the condition to reference it in the logic_tree
        condition_uuid = str(uuid.uuid4())
        
        # Construct TechnicalIndicatorPayload
        # Matches: class TechnicalIndicatorPayload(BaseModel) in models.py
        tech_payload = {
            "indicator": indicator.lower(),
            "params": {"period": 14}, # Defaulting period for simplicity, could be a parameter
            "operator": condition_operator,
            "value": threshold_value,
            "asset": asset_pair.upper(),
            "timeframe": timeframe
        }

        # Construct ConditionCreate
        # Matches: class ConditionCreate(BaseModel)
        condition_obj = {
            "id": condition_uuid,
            "type": "technical_indicator",
            "payload": tech_payload,
            "label": f"{indicator.upper()} {condition_operator} {threshold_value}",
            "enabled": True
        }

        # Construct Logic Tree
        # Matches: class LogicNode(BaseModel) - referencing the condition
        logic_tree = {
            "operator": "AND",
            "conditions": [
                {"ref": condition_uuid} # Reference the UUID generated above
            ]
        }

        # Construct Full Strategy Payload
        # Matches: class StrategyCreateSchema(BaseModel)
        strategy_payload = {
            "name": strategy_name,
            "description": f"{risk_description}. Logic: {indicator} {condition_operator} {threshold_value}",
            "schedule": "1m", # Monitoring frequency
            "assets": [asset_pair.upper()],
            "notification_preferences": {
                "channels": {
                    "email": {"enabled": True, "email": "demo@synapse.com"} 
                },
                "alert_on": {"trigger": True, "error": True},
                "cooldown": {"enabled": True, "duration": "1h"}
            },
            "conditions": [condition_obj],
            "logic_tree": logic_tree,
            "status": "active"
        }

        # 4. SEND TO SYNAPSE API
        try:
            headers = {
                "Content-Type": "application/json",
                # Include auth token if your API requires it
                "Authorization": f"Bearer {self._api_token}" 
            }
            
            url = f"{self._api_url}/strategies" # Note: endpoint is usually /strategies based on your router
            
            logger.info(f"[PremiumStrategyBuilder] Posting to {url}...")
            
            response = requests.post(
                url, 
                json=strategy_payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                strategy_id = data.get('id', 'unknown')
                return (
                    f"✅ **Strategy Built & Deployed!**\n\n"
                    f"**Name:** {strategy_name}\n"
                    f"**ID:** `{strategy_id}`\n"
                    f"**Status:** Active 🟢\n\n"
                    f"The monitoring service is now tracking **{asset_pair}** for **{indicator.upper()} {condition_operator} {threshold_value}**. "
                    f"You will be notified when this condition is met."
                )
            else:
                logger.error(f"Synapse API Error ({response.status_code}): {response.text}")
                return f"Failed to save strategy. Database Schema Error: {response.text}"

        except Exception as e:
            logger.error(f"Strategy Builder Connection Error: {e}")
            return f"Error connecting to Strategy Engine: {str(e)}"