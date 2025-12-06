import pytest
from unittest.mock import AsyncMock
import json
import aioredis

from core.data_prefetcher import DataPrefetcher

class DummyPool:
    async def disconnect(self):
        pass

class FakeRedis:
    def __init__(self):
        self.cache = {}
        self.setex_calls = []
    async def get(self, key):
        return self.cache.get(key)
    async def setex(self, key, ttl, value):
        self.cache[key] = value
        self.setex_calls.append((key, ttl, value))
    async def flushdb(self):
        self.cache.clear()
    async def close(self):
        pass

@pytest.fixture
def fake_redis(monkeypatch):
    instance = FakeRedis()
    def factory(*args, **kwargs):
        return instance
    monkeypatch.setattr(aioredis, 'Redis', factory)
    return instance

@pytest.fixture
def mock_binance_client():
    mock = AsyncMock()
    mock.get_price.return_value = None
    mock.get_klines.return_value = None
    return mock

@pytest.fixture
def mock_coingecko_client():
    mock = AsyncMock()
    mock.get_price.return_value = None
    mock.get_klines.return_value = None
    return mock

@pytest.fixture
async def prefetcher_with_mocks(mock_binance_client, mock_coingecko_client, fake_redis):
    p = DataPrefetcher(redis_url="redis://localhost:6379")
    p._binance = mock_binance_client
    p._coingecko = mock_coingecko_client
    p._pool = DummyPool()
    yield p
    await p.close()

@pytest.mark.asyncio
async def test_get_klines_from_redis_cache(prefetcher_with_mocks, fake_redis):
    mock_klines = [{"timestamp": 1, "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 10.0}]
    key = "klines:BTC:1h:5:usd"
    fake_redis.cache[key] = json.dumps(mock_klines)

    result = await prefetcher_with_mocks.get_klines("BTC", "1h", 5, "usd")

    assert result == mock_klines
    prefetcher_with_mocks._binance.get_klines.assert_not_called()
    prefetcher_with_mocks._coingecko.get_klines.assert_not_called()

@pytest.mark.asyncio
async def test_get_klines_from_binance_and_cache(prefetcher_with_mocks, fake_redis):
    mock_klines = [{"timestamp": 2, "open": 2.0, "high": 3.0, "low": 1.0, "close": 2.5, "volume": 20.0}]
    prefetcher_with_mocks._binance.get_klines.return_value = mock_klines

    result = await prefetcher_with_mocks.get_klines("BTC", "1h", 5, "usd")

    assert result == mock_klines
    prefetcher_with_mocks._binance.get_klines.assert_called_once_with("BTC", "1h", 5, "usd")
    prefetcher_with_mocks._coingecko.get_klines.assert_not_called()

    key = "klines:BTC:1h:5:usd"
    assert key in fake_redis.cache
    assert json.loads(fake_redis.cache[key]) == mock_klines
    assert fake_redis.setex_calls[0][1] == 60

@pytest.mark.asyncio
async def test_get_klines_from_coingecko_fallback_and_cache(prefetcher_with_mocks, fake_redis):
    mock_klines_coingecko = [{"timestamp": 3, "open": None, "high": None, "low": None, "close": 3.0, "volume": 30.0}]
    prefetcher_with_mocks._binance.get_klines.return_value = None
    prefetcher_with_mocks._coingecko.get_klines.return_value = mock_klines_coingecko

    result = await prefetcher_with_mocks.get_klines("ETH", "1h", 5, "usd")

    assert result == mock_klines_coingecko
    prefetcher_with_mocks._binance.get_klines.assert_called_once_with("ETH", "1h", 5, "usd")
    prefetcher_with_mocks._coingecko.get_klines.assert_called_once_with("ETH", "1h", 5, "usd")

    key = "klines:ETH:1h:5:usd"
    assert key in fake_redis.cache
    assert json.loads(fake_redis.cache[key]) == mock_klines_coingecko
    assert fake_redis.setex_calls[0][1] == 60

@pytest.mark.asyncio
async def test_get_klines_no_data_found(prefetcher_with_mocks, fake_redis):
    prefetcher_with_mocks._binance.get_klines.return_value = None
    prefetcher_with_mocks._coingecko.get_klines.return_value = None

    result = await prefetcher_with_mocks.get_klines("XYZ", "1h", 5, "usd")

    assert result is None
    prefetcher_with_mocks._binance.get_klines.assert_called_once_with("XYZ", "1h", 5, "usd")
    prefetcher_with_mocks._coingecko.get_klines.assert_called_once_with("XYZ", "1h", 5, "usd")
    assert fake_redis.setex_calls == []

@pytest.mark.asyncio
async def test_get_prices_from_redis_cache(prefetcher_with_mocks, fake_redis):
    key_btc = "prices:BTC"
    key_eth = "prices:ETH"
    fake_redis.cache[key_btc] = "100.0"
    fake_redis.cache[key_eth] = "200.0"

    result = await prefetcher_with_mocks.get_prices(["BTC", "ETH"], "usd")

    assert result == {"BTC": 100.0, "ETH": 200.0}
    prefetcher_with_mocks._binance.get_price.assert_not_called()
    prefetcher_with_mocks._coingecko.get_price.assert_not_called()

@pytest.mark.asyncio
async def test_get_prices_fetch_and_cache(prefetcher_with_mocks, fake_redis):
    prefetcher_with_mocks._binance.get_price.side_effect = [150.0, 250.0]

    result = await prefetcher_with_mocks.get_prices(["BTC", "ETH"], "usd")

    assert result == {"BTC": 150.0, "ETH": 250.0}
    assert prefetcher_with_mocks._binance.get_price.call_count == 2
    prefetcher_with_mocks._binance.get_price.assert_any_call("BTC", "usd")
    prefetcher_with_mocks._binance.get_price.assert_any_call("ETH", "usd")

    key_btc = "prices:BTC"
    key_eth = "prices:ETH"
    assert key_btc in fake_redis.cache
    assert key_eth in fake_redis.cache
    assert fake_redis.cache[key_btc] == "150.0"
    assert fake_redis.cache[key_eth] == "250.0"
    assert fake_redis.setex_calls[0][1] == 30

@pytest.mark.asyncio
async def test_get_prices_coingecko_fallback(prefetcher_with_mocks, fake_redis):
    prefetcher_with_mocks._binance.get_price.side_effect = [None, None]
    prefetcher_with_mocks._coingecko.get_price.side_effect = [160.0, 260.0]

    result = await prefetcher_with_mocks.get_prices(["BTC", "ETH"], "usd")

    assert result == {"BTC": 160.0, "ETH": 260.0}
    assert prefetcher_with_mocks._binance.get_price.call_count == 2
    assert prefetcher_with_mocks._coingecko.get_price.call_count == 2
    prefetcher_with_mocks._coingecko.get_price.assert_any_call("BTC", "usd")
    prefetcher_with_mocks._coingecko.get_price.assert_any_call("ETH", "usd")

    key_btc = "prices:BTC"
    key_eth = "prices:ETH"
    assert key_btc in fake_redis.cache
    assert key_eth in fake_redis.cache
    assert fake_redis.cache[key_btc] == "160.0"
    assert fake_redis.cache[key_eth] == "260.0"
    assert fake_redis.setex_calls[0][1] == 30

@pytest.mark.asyncio
async def test_get_prices_no_data_found(prefetcher_with_mocks, fake_redis):
    prefetcher_with_mocks._binance.get_price.return_value = None
    prefetcher_with_mocks._coingecko.get_price.return_value = None

    result = await prefetcher_with_mocks.get_prices(["BTC"], "usd")

    assert result == {"BTC": None}
    prefetcher_with_mocks._binance.get_price.assert_called_once_with("BTC", "usd")
    prefetcher_with_mocks._coingecko.get_price.assert_called_once_with("BTC", "usd")
    assert fake_redis.setex_calls == []
