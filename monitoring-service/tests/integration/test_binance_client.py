import asyncio
from clients.async_binance import AsyncBinanceClient

async def main():
    client = AsyncBinanceClient()
    # Binance expects symbol like 'BTCUSDT'
    klines = await client.get_klines("BTC", "1h", 5)
    print("BTC/USDT 1h klines:", klines)
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())