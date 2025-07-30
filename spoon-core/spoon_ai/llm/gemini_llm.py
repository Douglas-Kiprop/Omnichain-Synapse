import os
from google import genai
from spoon_ai.chat import ChatBot
from typing import List
from spoon_ai.schema import Message

class GeminiLLM(ChatBot):
    def __init__(self, api_key: str, model_name: str = "gemini-pro", **kwargs):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in the environment variables.")
        super().__init__(api_key=api_key, model_name=model_name, llm_provider="gemini", **kwargs)
        self.client = genai.Client(api_key=api_key)

    async def generate_response(self, prompt: str) -> str:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        response = await self.ask(messages)
        return response

    async def ask(self, messages: List[dict]) -> str:
        try:
            response = self.client.generate_content(
                model=self.model_name,
                contents=[{"parts": [{"text": messages[-1]["content"]}]}]
            )
            return response.text
        except Exception as e:
            return f"Gemini API request failed: {str(e)}"