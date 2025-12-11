"""
Crypto Tools Integration Module

This module provides integration of spoon-toolkit crypto tools as core tools
for the spoon-core chat functionality.
"""

import logging
from typing import List, Optional
from spoon_ai.tools.base import BaseTool
from spoon_ai.tools.tool_manager import ToolManager

# --- CRITICAL CHANGE 1: REMOVE COINGECKO, ADD COINMARKETCAP ---
from spoon_ai.tools.coinmarketcap_tool import CoinMarketCapTool 
# --- REMOVED: from spoon_ai.tools.coingecko_tool import CoinGeckoTool ---

# Import the premium Chainbase tool
from spoon_ai.tools.premium_chainbase_tool import PremiumChainbaseTool

# ✅ NEW: Import the Premium Strategy Builder
from spoon_ai.tools.premium_strategy_builder import PremiumStrategyBuilderTool

logger = logging.getLogger(__name__)

def get_crypto_tools() -> List[BaseTool]:
    """
    Import and return all available crypto tools from spoon-toolkit.

    Returns:
        List[BaseTool]: List of instantiated crypto tools
    """
    crypto_tools = []

    # --- CRITICAL CHANGE 2: Load the new CoinMarketCap Tool ---
    try:
        cmc_tool = CoinMarketCapTool()
        crypto_tools.append(cmc_tool)
        logger.info(f"✅ Loaded crypto tool: {cmc_tool.name}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to load CoinMarketCapTool: {e}")

    
    # Try to import tools from spoon-toolkits
    try:
        # Import crypto tools from spoon-toolkit
        from spoon_toolkits.crypto import (
            Get24hStatsTool,
            GetKlineDataTool,
            PriceThresholdAlertTool,
            LpRangeCheckTool,
            SuddenPriceIncreaseTool,
            LendingRateMonitorTool,
        )

                
        # Instantiate crypto tools
        tool_classes = [
            Get24hStatsTool,
            GetKlineDataTool,
            PriceThresholdAlertTool,
            LpRangeCheckTool,
            SuddenPriceIncreaseTool,
            LendingRateMonitorTool,
                         
        ]

        for tool_class in tool_classes:
            try:
                logger.info(f"Attempting to load crypto tool: {tool_class.__name__}")
                tool_instance = tool_class()
                crypto_tools.append(tool_instance)
                logger.info(f"✅ Loaded crypto tool: {tool_instance.name}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load crypto tool {tool_class.__name__}: {e}")

    except ImportError as e:
        logger.warning(f"⚠️ Failed to import crypto tools from spoon-toolkit.crypto: {e}")
    
    # PREMIUM: Load the premium Chainbase tool
    try:
        premium_chainbase_tool = PremiumChainbaseTool()
        crypto_tools.append(premium_chainbase_tool)
        logger.info(f"✅ Loaded premium crypto tool: {premium_chainbase_tool.name}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to load PremiumChainbaseTool: {e}")

    # ✅ PREMIUM: Load the Strategy Builder Tool
    try:
        strategy_builder = PremiumStrategyBuilderTool()
        crypto_tools.append(strategy_builder)
        logger.info(f"✅ Loaded premium crypto tool: {strategy_builder.name}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to load PremiumStrategyBuilderTool: {e}")

    logger.info(f"🔧 Loaded {len(crypto_tools)} crypto tools successfully")
    return crypto_tools

def create_crypto_tool_manager() -> ToolManager:
    """
    Create a ToolManager instance with all crypto tools loaded.

    Returns:
        ToolManager: Tool manager with crypto tools
    """
    crypto_tools = get_crypto_tools()
    return ToolManager(crypto_tools)

def get_crypto_tool_names() -> List[str]:
    """
    Get list of available crypto tool names.

    Returns:
        List[str]: List of crypto tool names
    """
    crypto_tools = get_crypto_tools()
    return [tool.name for tool in crypto_tools]

def add_crypto_tools_to_manager(tool_manager: ToolManager) -> ToolManager:
    """
    Add crypto tools to an existing ToolManager instance.

    Args:
        tool_manager (ToolManager): Existing tool manager

    Returns:
        ToolManager: Updated tool manager with crypto tools
    """
    crypto_tools = get_crypto_tools()
    tool_manager.add_tools(*crypto_tools)
    return tool_manager

class CryptoToolsConfig:
    """Configuration class for crypto tools integration"""

    # Default tools to load (can be customized)
    DEFAULT_TOOLS = [
        # --- CRITICAL CHANGE 3: Update tool name ---
        "coinmarketcap_data",  
        "get_24h_stats",
        "get_kline_data",
        "price_threshold_alert",
        "lp_range_check",
        "monitor_sudden_price_increase",
        "lending_rate_monitor",
        "crypto_market_monitor",              
        "crypto_powerdata_cex",
        "crypto_powerdata_dex",
        "crypto_powerdata_indicators",
        "crypto_powerdata_price",

        # Premium Tools
        "premium_chainbase",
        "premium_strategy_builder", 
    ]

    # Tools that require special configuration
    TOOLS_REQUIRING_CONFIG = [
        "lending_rate_monitor",         
        "crypto_powerdata_cex", 
        "crypto_powerdata_dex", 
        "crypto_powerdata_price",

        # Premium Tools
        "premium_chainbase",
        "premium_strategy_builder", 
        
        # --- CRITICAL CHANGE 4: Add CoinMarketCap key requirement ---
        "coinmarketcap_data",
    ]

    @classmethod
    def get_available_tools(cls) -> List[str]:
        """Get list of available crypto tool names"""
        return cls.DEFAULT_TOOLS.copy()

    @classmethod
    def get_tools_requiring_config(cls) -> List[str]:
        """Get list of tools that may require additional configuration"""
        return cls.TOOLS_REQUIRING_CONFIG.copy()