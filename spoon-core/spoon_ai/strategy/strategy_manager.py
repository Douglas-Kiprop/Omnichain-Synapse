import time
import requests
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse
from typing import List, Optional
from uuid import UUID
import os

from spoon_ai.schema import Strategy

class StrategyManager:
    def __init__(self, collection_name: str = "strategies", timeout: int = 5):
        # Get environment variables for Qdrant connection
        qdrant_host = os.getenv("QDRANT_HOST")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        
        # Initialize QdrantClient with environment variables
        if qdrant_host and qdrant_host.startswith("https://"):
            # For cloud deployment with full URL
            self.client = QdrantClient(url=qdrant_host, api_key=qdrant_api_key, timeout=timeout)
        elif qdrant_host:
            # For custom host without full URL
            self.client = QdrantClient(host=qdrant_host, api_key=qdrant_api_key, timeout=timeout)
        else:
            # Fallback to localhost
            self.client = QdrantClient(timeout=timeout)
            
        self.collection_name = collection_name
        self._create_collection_if_not_exists()

    def _create_collection_if_not_exists(self):
        max_retries = 2
        base_delay = 1  # seconds

        for i in range(max_retries):
            try:
                if not self.client.collection_exists(collection_name=self.collection_name):
                    print(f"Collection '{self.collection_name}' does not exist. Creating...")
                    self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
                    )
                    print(f"Collection '{self.collection_name}' created successfully.")
                else:
                    print(f"Collection '{self.collection_name}' already exists.")
                return
            except UnexpectedResponse as e:
                if e.status_code == 409:  # Conflict, collection already exists
                    print(f"Collection '{self.collection_name}' already exists (409 Conflict). Skipping creation.")
                    return
                else:
                    print(f"Unexpected Qdrant response during collection creation: {e}")
            except requests.exceptions.ConnectionError as e:
                print(f"Connection error to Qdrant: {e}")
            except Exception as e:
                print(f"An unexpected error occurred during collection creation: {e}")

            if i < max_retries - 1:
                delay = base_delay * (2 ** i)  # Exponential backoff
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                raise ConnectionError(f"Failed to connect to Qdrant or create collection after {max_retries} retries.")

    def create_strategy(self, strategy: Strategy) -> Strategy:
        # For now, we'll use a dummy vector. In a real scenario, you'd generate an embedding for the strategy.
        # For example, by embedding the strategy's description or conditions.
        dummy_vector = [0.0] * 1536  # Placeholder for a 1536-dimension vector

        point = PointStruct(
            id=str(strategy.id),
            vector=dummy_vector,
            payload=strategy.model_dump(mode='json') # Use model_dump for Pydantic v2
        )
        self.client.upsert(collection_name=self.collection_name, points=[point])
        return strategy

    def get_strategy(self, strategy_id: UUID) -> Optional[Strategy]:
        try:
            retrieved_point = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[str(strategy_id)],
                with_payload=True,
                with_vectors=False
            )
            if retrieved_point and retrieved_point[0]:
                return Strategy(**retrieved_point[0].payload)
            return None
        except Exception as e:
            print(f"Error retrieving strategy: {e}")
            return None

    def update_strategy(self, strategy: Strategy) -> Optional[Strategy]:
        # For now, we'll use a dummy vector. In a real scenario, you'd generate an embedding for the updated strategy.
        dummy_vector = [0.0] * 1536  # Placeholder for a 1536-dimension vector

        point = PointStruct(
            id=str(strategy.id),
            vector=dummy_vector,
            payload=strategy.model_dump(mode='json')
        )
        self.client.upsert(collection_name=self.collection_name, points=[point])
        return self.get_strategy(strategy.id)

    def delete_strategy(self, strategy_id: UUID) -> bool:
        try:
            self.client.delete(collection_name=self.collection_name, points_selector=[
                str(strategy_id)
            ])
            return True
        except Exception as e:
            print(f"Error deleting strategy: {e}")
            return False