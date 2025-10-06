"""
Crypto Tools Integration Module

This module provides integration of spoon-toolkit crypto tools as core tools
for the spoon-core chat functionality.
"""

import logging
from typing import List, Optional
from spoon_ai.tools.base import BaseTool
from spoon_ai.tools.tool_manager import ToolManager
from spoon_ai.tools.coingecko_tool import CoinGeckoTool  # Import custom tool

logger = logging.getLogger(__name__)

def get_crypto_tools() -> List[BaseTool]:
    """
    Import and return all available crypto tools from spoon-toolkit.

    Returns:
        List[BaseTool]: List of instantiated crypto tools
    """
    crypto_tools = []

    # Always add the CoinGeckoTool which is part of spoon-core
    try:
        coingecko_tool = CoinGeckoTool()
        crypto_tools.append(coingecko_tool)
        logger.info(f"✅ Loaded crypto tool: {coingecko_tool.name}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to load CoinGeckoTool: {e}")

    # Try to import tools from spoon-toolkits
    try:
        # Import crypto tools from spoon-toolkit
        from spoon_toolkits.crypto import (
            #GetTokenPriceTool,
            Get24hStatsTool,
            GetKlineDataTool,
            PriceThresholdAlertTool,
            LpRangeCheckTool,
            SuddenPriceIncreaseTool,
            LendingRateMonitorTool,
        )

        # Import additional crypto tools
        # from spoon_toolkits.crypto.blockchain_monitor import CryptoMarketMonitor
        from spoon_toolkits.crypto.predict_price import PredictPrice
        from spoon_toolkits.crypto.token_holders import TokenHolders
        from spoon_toolkits.crypto.wallet_analysis import WalletAnalysis
        
        # Instantiate crypto tools
        tool_classes = [
            #GetTokenPriceTool,
            Get24hStatsTool,
            GetKlineDataTool,
            PriceThresholdAlertTool,
            LpRangeCheckTool,
            SuddenPriceIncreaseTool,
            LendingRateMonitorTool,
            # CryptoMarketMonitor,
            PredictPrice,
            TokenHolders,  
            WalletAnalysis,          
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
    
    # Try to import chainbase tools separately
    try:
        # Import Chainbase tools from chainbase_tools.py
        from spoon_toolkits.chainbase.chainbase_tools import (
            GetLatestBlockNumberTool,
            GetBlockByNumberTool,
            GetTransactionByHashTool,
            GetAccountTransactionsTool,
            ContractCallTool,
            GetAccountTokensTool,
            GetAccountNFTsTool, 
            GetAccountBalanceTool,
            GetTokenMetadataTool,
        )
        
        # Chainbase Tools
        chainbase_tool_classes = [
            GetLatestBlockNumberTool,
            GetBlockByNumberTool,
            GetTransactionByHashTool,
            GetAccountTransactionsTool,
            ContractCallTool,
            GetAccountTokensTool,
            GetAccountNFTsTool, 
            GetAccountBalanceTool,
            GetTokenMetadataTool,
        ]
        
        for tool_class in chainbase_tool_classes:
            try:
                logger.info(f"Attempting to load chainbase tool: {tool_class.__name__}")
                tool_instance = tool_class()
                crypto_tools.append(tool_instance)
                logger.info(f"✅ Loaded chainbase tool: {tool_instance.name}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load chainbase tool {tool_class.__name__}: {e}")
                
    except ImportError as e:
        logger.warning(f"⚠️ Failed to import chainbase tools from spoon-toolkit.chainbase: {e}")

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
        #"get_token_price",
        "coingecko_price",  # Updated to match CoinGeckoTool name
        "get_24h_stats",
        "get_kline_data",
        "price_threshold_alert",
        "lp_range_check",
        "monitor_sudden_price_increase",
        "lending_rate_monitor",
        "crypto_market_monitor",
        "predict_price",
        "token_holders",  
        "wallet_analysis",      
        "crypto_powerdata_cex",
        "crypto_powerdata_dex",
        "crypto_powerdata_indicators",
        "crypto_powerdata_price",

        # Chainbase Tools (from chainbase_tools.py)
        "get_latest_block_number",
        "get_block_by_number",
        "get_transaction_by_hash",
        "get_transactions_by_account",
        "contract_call",
        "get_account_tokens",
        "get_account_nfts", 
        "get_account_balance",
        "get_token_metadata",
    ]

    # Tools that require special configuration
    TOOLS_REQUIRING_CONFIG = [
        "lending_rate_monitor",  # May need API keys
        "predict_price",         # Requires ML dependencies
        "token_holders",         # Requires Bitquery API key
        "wallet_analysis",
        "crypto_powerdata_cex",  # May need API keys for private data
        "crypto_powerdata_dex",  # Requires OKX API Key
        "crypto_powerdata_price", # Requires OKX/CEX API Keys

        # Chainbase Tools (from chainbase_tools.py)
        "get_latest_block_number",
        "get_block_by_number",
        "get_transaction_by_hash",
        "get_transactions_by_account",
        "contract_call",
        "get_account_tokens",
        "get_account_nfts", 
        "get_account_balance",
        "get_token_metadata",
    ]

    @classmethod
    def get_available_tools(cls) -> List[str]:
        """Get list of available crypto tool names"""
        return cls.DEFAULT_TOOLS.copy()

    @classmethod
    def get_tools_requiring_config(cls) -> List[str]:
        """Get list of tools that may require additional configuration"""
        return cls.TOOLS_REQUIRING_CONFIG.copy()