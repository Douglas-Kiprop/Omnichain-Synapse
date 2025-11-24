from typing import Optional
from uuid import UUID

class StrategyManager:
    def __init__(self, *args, **kwargs):
        # Legacy Qdrant client removed; no external connections on startup.
        self.collection_name = "strategies"

    def _create_collection_if_not_exists(self):
        # No-op: legacy collection creation removed.
        return

    def create_strategy(self, strategy):
        # Disabled: persistence moved to synapse-api per new architecture.
        raise RuntimeError("StrategyManager disabled. Use synapse-api for persistence.")

    def get_strategy(self, strategy_id: UUID) -> Optional[dict]:
        return None

    def update_strategy(self, strategy) -> Optional[dict]:
        return None

    def delete_strategy(self, strategy_id: UUID) -> bool:
        return False