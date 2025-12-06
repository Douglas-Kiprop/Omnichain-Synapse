import asyncio
from clients.async_coingecko import AsyncCoinGeckoClient

async def main():
    client = AsyncCoinGeckoClient()
    price = await client.get_price("bitcoin", "usd")
    print("bitcoin usd price:", price)
    
    # Test klines as well
    klines = await client.get_klines("bitcoin", "1d", limit=7, currency="usd")
    print(f"CoinGecko Bitcoin 1d klines (last 7): {klines}")

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())