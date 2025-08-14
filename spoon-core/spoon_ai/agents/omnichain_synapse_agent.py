import os
from dotenv import load_dotenv
from spoon_ai.agents.spoon_react import SpoonReactAI # Changed from BaseAgent
from spoon_ai.tools.chainbase_tool import ChainbaseTool
from spoon_ai.tools.coingecko_tool import CoinGeckoTool
from spoon_ai.chat import ChatBot # Import ChatBot instead of GeminiLLM
from typing import Optional
import asyncio
import logging
from spoon_ai.tools.crypto_tools import get_crypto_tools # New import
from spoon_ai.strategy.strategy_manager import StrategyManager # New import
from spoon_ai.schema import Strategy # New import

# Set up logging for detailed debugging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class OmnichainSynapseAgent(SpoonReactAI):
    """
    An AI agent for onchain data analysis, leveraging Chainbase and CoinGecko tools.
    """
    def __init__(self, name: str = "OmnichainSynapseAgent", llm: Optional[ChatBot] = None, **kwargs):
        # Use ChatBot directly, it will pick up config from environment/config.json
        llm = llm if llm else ChatBot() # Changed to ChatBot
        
        # Initialize SpoonReactAI with the LLM and register tools via its tool manager
        super().__init__(name=name, llm=llm, **kwargs)
        
        # Initialize StrategyManager
        self.strategy_manager = StrategyManager()
        
        # Register tools with SpoonReactAI's tool manager
        try:
            # Load and register all crypto tools from spoon-toolkit
            crypto_tools = get_crypto_tools()
            self.avaliable_tools.add_tools(*crypto_tools)
            logger.debug(f"Successfully registered {len(crypto_tools)} crypto tools.")
        except Exception as e:
            logger.error(f"Failed to initialize crypto tools: %s", e)
            raise

    async def process(self, input_text: str) -> str:
        """
        Processes the user's input, reasons, makes tool calls, and generates a response.
        This method now primarily relies on SpoonReactAI's internal ReAct loop.
        """
        logger.debug(f"OmnichainSynapseAgent received input: {input_text}")
        try:
            # Delegate the processing to the SpoonReactAI's run method.
            # This will engage the ReAct loop, which uses the LLM to reason,
            # select tools from self.avaliable_tools, and generate a response.
            response = await super().run(request=input_text)
            logger.debug(f"SpoonReactAI run method returned: {response}")
            return response
        except Exception as e:
            logger.error(f"Error during SpoonReactAI processing: {e}")
            return f"An error occurred while processing your request: {str(e)}"

    async def _craft_strategy(self, strategy_data: dict) -> dict:
        """
        Internal method to craft and validate a strategy before saving.
        Args:
            strategy_data: Dictionary containing strategy parameters
        Returns:
            Dictionary with status and either the strategy or error message
        """
        try:
            # Validate required fields
            required_fields = ['name', 'description', 'parameters']
            for field in required_fields:
                if field not in strategy_data:
                    return {"status": "error", "message": f"Missing required field: {field}"}

            # Create the strategy
            # Convert dict to Strategy object before passing to create_strategy
            return await self.create_strategy(strategy_data)
        except Exception as e:
            logger.error(f"Failed to craft strategy: {e}")
            return {"status": "error", "message": str(e)}

    async def create_strategy(self, strategy_data: dict) -> dict:
        """Creates a new strategy and stores it in Qdrant."""
        try:
            # Convert strategy_data dict to Strategy Pydantic model
            strategy_obj = Strategy(**strategy_data)
            # Call synchronous strategy_manager method without await
            strategy = self.strategy_manager.create_strategy(strategy_obj)
            return {"status": "success", "strategy": strategy.model_dump(mode='json')} # Use model_dump(mode='json') for proper serialization
        except Exception as e:
            logger.error(f"Failed to create strategy: {e}")
            return {"status": "error", "message": str(e)}

    async def get_strategy(self, strategy_id: str) -> dict:
        """Retrieves a strategy by its ID."""
        try:
            # Call synchronous strategy_manager method without await
            strategy = self.strategy_manager.get_strategy(strategy_id)
            if strategy:
                return {"status": "success", "strategy": strategy.model_dump(mode='json')} # Use model_dump(mode='json') for proper serialization
            return {"status": "error", "message": f"Strategy with ID {strategy_id} not found."}
        except Exception as e:
            logger.error(f"Failed to get strategy: {e}")
            return {"status": "error", "message": str(e)}

    async def update_strategy(self, strategy_id: str, updates: dict) -> dict:
        """Updates an existing strategy."""
        try:
            # First, get the existing strategy to update it
            existing_strategy = self.strategy_manager.get_strategy(strategy_id)
            if not existing_strategy:
                return {"status": "error", "message": f"Strategy with ID {strategy_id} not found for update."}

            # Update the existing strategy object with new data
            updated_strategy_data = existing_strategy.model_dump()
            updated_strategy_data.update(updates)
            updated_strategy_obj = Strategy(**updated_strategy_data)

            # Call synchronous strategy_manager method without await
            strategy = self.strategy_manager.update_strategy(updated_strategy_obj)
            return {"status": "success", "strategy": strategy.model_dump(mode='json')} # Use model_dump(mode='json') for proper serialization
        except Exception as e:
            logger.error(f"Failed to update strategy: {e}")
            return {"status": "error", "message": str(e)}

    async def delete_strategy(self, strategy_id: str) -> dict:
        """Deletes a strategy by its ID."""
        try:
            # Call synchronous strategy_manager method without await
            self.strategy_manager.delete_strategy(strategy_id)
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Failed to delete strategy: {e}")
            return {"status": "error", "message": str(e)}

# Example Usage
if __name__ == "__main__":
    async def main():
        try:
            logger.info("Initializing OmnichainSynapseAgent")
            agent = OmnichainSynapseAgent()
            logger.info("Agent initialized successfully")

            print("\n--- Testing Agent with Crypto Tools ---")
            # Test with a query that might trigger one of the new crypto tools
            # For example, GetTokenPriceTool or Get24hStatsTool
            response_neo_price = await agent.process("What is the current price of NEO-USDT?")
            print(f"Agent Response (NEO Price): {response_neo_price}")

            # Example: Get ETH balance of a wallet
            #response_eth_balance = await agent.process(f"What is the Ethereum (ETH) balance of the wallet address 0xd8da6bf26964af9d7eed9e03e53415d37aa96045?")
            #print(f"Agent Response (ETH Wallet Balance): {response_eth_balance}")

            # Example: Get recent transactions for a wallet address
            # This assumes a tool like 'GetWalletTransactions' exists
            #response_transactions = await agent.process(f"Show me the last 5 transactions for the wallet address 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 on Ethereum.")
            #print(f"Agent Response (Wallet Transactions): {response_transactions}")

            # Example: Request a general wallet overview
            #response_overview = await agent.process(f"Provide a summary of the activity for wallet 0x3BB3974bb07FD75A1aD694Deb099376c6918D5E6.")
            #print(f"Agent Response (Wallet Overview): {response_overview}")


            # Removed other queries as per user's instruction to test one query at a time.
            #response_stats = await agent.process("Tell me the 24-hour trading volume for Bitcoin.")
            #print(f"Agent Response (Bitcoin 24h Stats): {response_stats}")

            # response_kline = await agent.process("Get the daily kline data for BNB for the last 7 days.")
            # print(f"Agent Response (BNB Kline Data): {response_kline}")

            # print("\n--- Testing LLM Fallback ---")
            # # This will still fall back to the LLM if no tool is deemed necessary.
            #response_llm = await agent.process("Explain what a blockchain is in simple terms.")
            #print(f"Agent Response (General): {response_llm}")

        except Exception as e:
            logger.error(f"Failed to initialize or run agent: %s", e)
            print(f"[ERROR] Failed to initialize or run agent: {str(e)}")

    asyncio.run(main())