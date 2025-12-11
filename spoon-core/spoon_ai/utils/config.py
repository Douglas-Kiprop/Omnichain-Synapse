import os

from dotenv import load_dotenv

load_dotenv()

# DB
DATABASE_URL = os.getenv("DATABASE_URL")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# DEEPSEEK
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Redis
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

SECRET_KEY = "spoon-ai-secret-key"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# New: x402 config
AVALANCHE_RPC = "https://api.avax-test.network/ext/bc/C/rpc"
TREASURY_ADDRESS = os.getenv("TREASURY_ADDRESS", "0x636b2b787b6564018d9d9d84272838185d8254b4")  # Add to .env
TREASURY_ADDRESS = "0x636b2b787b6564018d9d9d84272838185d8254b4"  # Your wallet or contract
PREMIUM_TOOL_FEE_WEI = int(0.0005 * 1e18)  # 0.0005 AVAX in wei