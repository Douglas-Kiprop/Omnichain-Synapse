from typing import List, Optional
from fastapi import APIRouter, Query
from market import service
from market.models import GainerLoserEntry, VolumeAnalysisEntry, HeatmapEntry

router = APIRouter(
    prefix="/market",
    tags=["Market Data"],
)

@router.get("/gainers-losers")
async def get_gainers_losers_endpoint(
    limit: int = Query(10, ge=1, le=50),
    timeframe: str = Query("24h", pattern="^(1h|24h|7d|14d|30d|200d|1y)$", description="Timeframe for price change percentage (e.g., 1h, 24h, 7d)")
):
    """
    Get the top N market gainers and losers over the last 24 hours.
    """
    return await service.get_gainers_losers(limit=limit, timeframe=timeframe)

@router.get("/volume-analysis")
async def get_volume_analysis_endpoint(
    symbol: str,
    interval: str = Query("1h", description="e.g., 1h, 4h, 1d"),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get volume analysis for a specific trading pair.
    """
    return await service.get_volume_analysis(symbol=symbol, interval=interval, limit=limit)

@router.get("/heatmap-data", response_model=List[HeatmapEntry])
async def get_heatmap_data_endpoint(
    sort_by: str = Query(..., description="Sort by 'volume' or 'price_change'"),
    limit: int = Query(20, description="Limit the number of results")
):
    return await service.get_heatmap_data(sort_by, limit)