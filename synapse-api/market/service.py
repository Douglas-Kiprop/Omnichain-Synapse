from .models import GainerLoserEntry, VolumeAnalysisEntry
from providers import coingecko, binance
from datetime import datetime
from . import cache

async def get_gainers_losers(limit: int = 10, timeframe: str = "24h"):
    """
    Fetches and processes data to identify top gainers and losers.
    """
    cache_key = cache.generate_cache_key("gainers_losers", limit, timeframe)
    cached_data = await cache.get_cached_data(cache_key, cache.market_cache)
    if cached_data:
        return cached_data

    market_data = await coingecko.get_market_data(timeframe=timeframe)
    if not market_data:
        return {"gainers": [], "losers": []}

    # Sort by the dynamic percentage change key
    if timeframe == "24h":
        percentage_change_key = 'price_change_percentage_24h'
    else:
        percentage_change_key = f'price_change_percentage_{timeframe}_in_currency'

    # Sort by the dynamic percentage change key
    sorted_by_change = sorted(
        [d for d in market_data if d.get(percentage_change_key) is not None],
        key=lambda x: x[percentage_change_key],
        reverse=True
    )

    # Separate into gainers and losers
    gainers = sorted_by_change[:limit]
    losers = sorted(
        [d for d in market_data if d.get(percentage_change_key) is not None],
        key=lambda x: x[percentage_change_key]
    )[:limit]

    def to_gainer_loser_entry(d):
        percentage_change = d.get(percentage_change_key, 0) or 0
        current_price = d.get('current_price', 0) or 0
        
        # Calculate price_change from percentage_change and current_price
        if percentage_change != 0:
            price_at_start = current_price / (1 + percentage_change / 100)
            price_change = current_price - price_at_start
        else:
            price_change = 0

        return GainerLoserEntry(
            symbol=d.get('symbol', '').upper(),
            price_change=price_change,
            percentage_change=percentage_change,
            current_price=current_price,
            volume=d.get('total_volume', 0) or 0,
            timestamp=datetime.now()
        )

    result = {
        "gainers": [to_gainer_loser_entry(g) for g in gainers],
        "losers": [to_gainer_loser_entry(l) for l in losers]
    }

    await cache.set_cached_data(cache_key, result, cache.market_cache)
    return result

async def get_volume_analysis(symbol: str, interval: str, limit: int = 100):
    """
    Fetches and analyzes volume data for a given symbol.
    """
    cache_key = cache.generate_cache_key("volume_analysis", symbol, interval, limit)
    cached_data = await cache.get_cached_data(cache_key, cache.volume_cache)
    if cached_data:
        return cached_data

    klines = await binance.get_klines(symbol=symbol, interval=interval, limit=limit)
    if not klines:
        return []

    volume_entries = []
    for k in klines:
        volume_entries.append(VolumeAnalysisEntry(
            symbol=symbol.upper(),
            timestamp=k['close_time'], # Using close_time for the entry
            volume=k['volume'],
            quote_asset_volume=k['quote_asset_volume'],
            trade_count=k['trade_count']
        ))
    
    await cache.set_cached_data(cache_key, volume_entries, cache.volume_cache)
    return volume_entries

    volume_entries = []
    for k in klines:
        volume_entries.append(VolumeAnalysisEntry(
            symbol=symbol.upper(),
            timestamp=k['close_time'], # Using close_time for the entry
            volume=k['volume'],
            quote_asset_volume=k['quote_asset_volume'],
            trade_count=k['trade_count']
        ))
    return volume_entries