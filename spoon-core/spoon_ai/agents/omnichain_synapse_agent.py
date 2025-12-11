# omnichain_synapse.py

import os
import asyncio
import logging
from typing import Optional
from dotenv import load_dotenv

# Ensure you import the base classes correctly, including the exception
from spoon_ai.agents.spoon_react import SpoonReactAI 
from spoon_ai.chat import ChatBot
from spoon_ai.tools.crypto_tools import get_crypto_tools
from spoon_ai.tools.premium_chainbase_tool import PaymentRequiredException # Needed for exception handling

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

class OmnichainSynapseAgent(SpoonReactAI):
    """
    An AI agent for onchain data analysis, leveraging Chainbase and CoinGecko tools.
    """
    def __init__(self, name: str = "OmnichainSynapseAgent", llm: Optional[ChatBot] = None, **kwargs):
        llm = llm if llm else ChatBot()
        super().__init__(name=name, llm=llm, **kwargs)
        
        try:
            crypto_tools = get_crypto_tools()
            self.avaliable_tools.add_tools(*crypto_tools)
            logger.debug(f"Successfully registered {len(crypto_tools)} crypto tools.")
        except Exception as e:
            logger.error(f"Failed to initialize crypto tools: %s", e)
            raise

    async def process(self, input_text: str) -> str:
        """
        Processes the user's input with payment exception bubbling and history reset.
        """
        logger.debug(f"OmnichainSynapseAgent received input: {input_text}")
        try:
            response = await super().run(request=input_text)
            logger.debug(f"SpoonReactAI run method returned: {response}")
            return response
        except PaymentRequiredException as e:
            # 🛑 CRITICAL FIX: Reset the agent's history and state when the 
            # conversation is broken by the PaymentRequiredException.
            logger.info("💰 OmnichainSynapseAgent bubbling Payment Exception... Clearing history.")
            self.clear() # Resetting state/messages/tool_calls
            raise e # Re-raise to trigger the FastAPI 402 handler
            
        except Exception as e:
            logger.error(f"Error during SpoonReactAI processing: {e}")
            return f"An error occurred while processing your request: {str(e)}"

# Example Usage
if __name__ == "__main__":
    async def main():
        # Example or placeholder main function logic
        pass
    asyncio.run(main())