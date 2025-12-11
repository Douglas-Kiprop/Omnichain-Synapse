import requests
import json
import os
from dotenv import load_dotenv
from spoon_ai.tools.base import BaseTool, ToolResult
from pydantic import Field
import logging

logger = logging.getLogger(__name__)

load_dotenv()

class TurfTool(BaseTool):
    """
    A tool to query TURF network for intent-driven, real-time data orchestration.
    Fetches structured data from Data Buckets based on natural language intent.
    """
    name: str = Field(default="turf_query", description="The name of the tool")
    description: str = Field(
        default="Query TURF for on-demand, context-aware data (e.g., real-time traffic, weather, or custom datasets). Provide an intent like 'analyze urban traffic in Seattle during rush hour'.",
        description="Description for LLM tool selection"
    )
    parameters: dict = Field(
        default={
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "description": "Natural language intent describing the data needed (required)."
                },
                "params": {
                    "type": "object",
                    "description": "Optional parameters (e.g., {'geo': '47.6062,-122.3321', 'temporal': 'now-1h', 'format': 'json'})."
                }
            },
            "required": ["intent"]
        },
        description="Parameters for TURF queries"
    )
    
    # Define api_key and base_url as Pydantic Fields
    api_key: str = Field(default_factory=lambda: os.getenv("TURF_API_KEY"), description="API key for TURF network")
    base_url: str = Field(default="https://api.turf.network/v1", description="Base URL for TURF API")

    def __init__(self, **data):
        super().__init__(**data) # Call BaseModel's __init__ to handle Field initialization
        if not self.api_key:
            raise ValueError("TURF_API_KEY not found in .env file")
        logger.info("Initializing TurfTool")

    async def execute(self, intent: str, params: dict = None) -> ToolResult:
        """
        Executes a TURF query via API.
        """
        try:
            url = f"{self.base_url}/query"
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            body = {
                "intent": intent,
                "params": params or {},
                "format": "json"  # Default; can be overridden in params
            }

            logger.info(f"Calling TURF API: {url} with intent '{intent}'")
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()

            # Handle response: Assume structure like {"data": {...}, "sources": [...], "metadata": {...}}
            return ToolResult(
                output={
                    "intent": intent,
                    "data": data.get("data", {}),
                    "sources": data.get("sources", []),
                    "metadata": data.get("metadata", {}),
                    "timestamp": int(response.headers.get("date", 0))
                }
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"TURF API error: {e}")
            return ToolResult(error=str(e))
        except Exception as e:
            logger.error(f"Unexpected error in TurfTool: {e}")
            return ToolResult(error=str(e))