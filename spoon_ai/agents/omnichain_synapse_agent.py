import os
from dotenv import load_dotenv
from spoon_ai.agents.base import BaseAgent
from spoon_ai.tools.chainbase_tool import ChainbaseTool
from spoon_ai.tools.coingecko_tool import CoinGeckoTool
from spoon_ai.llm.openai_llm import OpenAILLM
from typing import Optional
import asyncio
import logging

# Set up logging for detailed debugging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class OmnichainSynapseAgent(BaseAgent):
    """
    An AI agent for onchain data analysis, leveraging Chainbase and CoinGecko tools.
    """
    def __init__(self, name: str = "OmnichainSynapseAgent", llm: Optional[OpenAILLM] = None, **kwargs):
        # Use OpenAI's default base_url if not provided
        llm = llm if llm else OpenAILLM(api_key=os.getenv("OPENAI_API_KEY"), base_url="https://api.openai.com/v1")
        super().__init__(name=name, llm=llm, **kwargs)
        try:
            self.register_tool(ChainbaseTool())
            logger.debug("Successfully registered ChainbaseTool")
        except Exception as e:
            logger.error(f"Failed to initialize ChainbaseTool: %s", e)
            raise
        try:
            self.register_tool(CoinGeckoTool())
            logger.debug("Successfully registered CoinGeckoTool")
        except Exception as e:
            logger.error(f"Failed to initialize CoinGeckoTool: %s", e)
            raise

    async def process(self, input_text: str) -> str:
        """
        Processes the user's input, reasons, makes tool calls, and generates a response.
        """
        try:
            # Parse for CoinGecko price queries
            if "price" in input_text.lower() and any(keyword in input_text.lower() for keyword in ["coin", "token"]):
                coin_id = input_text.lower().split("price of ")[-1].split(" ")[0].replace("$", "").strip("?.!,")
                if coin_id:
                    logger.debug(f"Calling CoinGeckoTool.get_coin_price with: {coin_id}")
                    try:
                        result = await asyncio.to_thread(self.tools["CoinGeckoTool"].get_coin_price, coin_id)
                        logger.debug(f"CoinGeckoTool result: {result}")
                        if isinstance(result, dict) and coin_id in result and "usd" in result[coin_id]:
                            return f"The current price of {coin_id} is {result[coin_id]['usd']} USD."
                        return f"Could not retrieve USD price for {coin_id}. Error: {result.get('error', 'Unknown error')}"
                    except Exception as e:
                        logger.error(f"Exception in CoinGeckoTool call: %s", e)
                        return f"An error occurred while fetching price: {str(e)}"

            # Parse for Chainbase wallet transactions (more flexible parsing)
            elif any(keyword in input_text.lower() for keyword in ["transactions", "txs"]) and any(keyword in input_text.lower() for keyword in ["wallet", "address", "0x"]):
                # Extract wallet address after "transactions for" or similar
                parts = input_text.lower().split("for")
                wallet_address = parts[-1].strip().split(" ")[0].strip("?.!,")
                if wallet_address.startswith("0x") and len(wallet_address) == 42:  # Basic Ethereum address validation
                    logger.debug(f"Calling ChainbaseTool.get_wallet_transactions with: {wallet_address}")
                    try:
                        result = await asyncio.to_thread(self.tools["ChainbaseTool"].get_wallet_transactions, wallet_address, chain_id=1)
                        logger.debug(f"ChainbaseTool result: {result}")
                        if isinstance(result, dict) and "data" in result and result.get("code") == 0:
                            return f"Transactions for {wallet_address}: {result['data']}"
                        return f"Could not retrieve transactions for {wallet_address}. Error: {result.get('error', 'Unknown error')}"
                    except Exception as e:
                        logger.error(f"Exception in ChainbaseTool call: %s", e)
                        return f"An error occurred while fetching transactions: {str(e)}"
                else:
                    return f"Invalid wallet address: {wallet_address}"

            # Fallback to LLM
            logger.debug(f"Falling back to LLM for input: {input_text}")
            try:
                return await self.llm.generate_response(input_text)
            except Exception as e:
                logger.error(f"Exception in LLM call: %s", e)
                return f"An error occurred while processing with LLM: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error in process: %s", e)
            return f"An unexpected error occurred: {str(e)}"

# Example Usage
if __name__ == "__main__":
    async def main():
        try:
            logger.info("Initializing OmnichainSynapseAgent")
            agent = OmnichainSynapseAgent()
            logger.info("Agent initialized successfully")

            print("\n--- Testing CoinGecko Tool ---")
            response_price = await agent.process("What is the price of bitcoin?")
            print(f"Agent Response: {response_price}")

            print("\n--- Testing Chainbase Tool ---")
            response_tx = await agent.process("Show me transactions for 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
            print(f"Agent Response: {response_tx}")

            print("\n--- Testing LLM Fallback ---")
            response_llm = await agent.process("Tell me a joke about blockchain.")
            print(f"Agent Response: {response_llm}")
        except Exception as e:
            logger.error(f"Failed to initialize or run agent: %s", e)
            print(f"[ERROR] Failed to initialize or run agent: {str(e)}")

    asyncio.run(main())