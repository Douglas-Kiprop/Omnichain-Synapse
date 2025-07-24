import os
from openai import OpenAI
from spoon_ai.chat import ChatBot # Import ChatBot
from typing import List, Union
from spoon_ai.schema import Message

class OpenAILLM(ChatBot):
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo", **kwargs):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set in the environment variables.")
        super().__init__(api_key=api_key, model_name=model_name, llm_provider="openai", **kwargs)

    async def generate_response(self, prompt: str) -> str:
        # This method is no longer directly used for agent's LLM calls
        # The agent will call the 'ask' method inherited from ChatBot
        # However, if you still want to use this for direct prompts outside the agent's loop:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        response = await self.ask(messages)
        return response

    # The 'ask' method is inherited from ChatBot and handles the actual API interaction.
    # No need to re-implement it here unless you want to override its behavior.