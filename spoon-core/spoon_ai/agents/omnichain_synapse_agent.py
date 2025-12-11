import os
from dotenv import load_dotenv
from spoon_ai.agents.spoon_react import SpoonReactAI  # Changed from BaseAgent
from spoon_ai.tools.coingecko_tool import CoinGeckoTool
from spoon_ai.chat import ChatBot  # Import ChatBot instead of GeminiLLM
from typing import Optional
import asyncio
import logging
from spoon_ai.tools.crypto_tools import get_crypto_tools  # New import


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
        llm = llm if llm else ChatBot()  # Changed to ChatBot
        
        # Initialize SpoonReactAI with the LLM and register tools via its tool manager
        super().__init__(name=name, llm=llm, **kwargs)
        
        # New: For x402 premium tool verification (does not affect original init)
        self.current_txn_hash: Optional[str] = None
        
        # Register tools with SpoonReactAI's tool manager
        try:
            # Load and register all crypto tools from spoon-toolkit
            crypto_tools = get_crypto_tools()
            self.avaliable_tools.add_tools(*crypto_tools)
            logger.debug(f"Successfully registered {len(crypto_tools)} crypto tools.")
        except Exception as e:
            logger.error(f"Failed to initialize crypto tools: %s", e)
            raise

    async def process(self, input_text: str, txn_hash: Optional[str] = None) -> str:
        """
        Processes the user's input, reasons, makes tool calls, and generates a response.
        This method now primarily relies on SpoonReactAI's internal ReAct loop.
        """
        logger.debug(f"OmnichainSynapseAgent received input: {input_text}")
        # New: Set txn_hash for premium verification (does not affect original process)
        self.current_txn_hash = txn_hash
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
        finally:
            # New: Clean up txn_hash after processing
            self.current_txn_hash = None

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