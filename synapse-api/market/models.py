from pydantic import BaseModel
from datetime import datetime

class GainerLoserEntry(BaseModel):
    """
    Represents a single entry in the gainers or losers list.
    """
    symbol: str
    price_change: float
    percentage_change: float
    current_price: float
    volume: float
    timestamp: datetime

class VolumeAnalysisEntry(BaseModel):
    """
    Represents a single data point for volume analysis.
    """
    symbol: str
    timestamp: datetime
    volume: float
    quote_asset_volume: float
    trade_count: int | None = None