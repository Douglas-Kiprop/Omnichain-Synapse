# Omnichain Synapse Agent 🧠: Multi-Agent Crypto Strategy Creation and Execution Engine

This repository contains the core components of a sophisticated, multi-module system designed for automated, secure, and monetized decentralized finance (DeFi) strategy execution and market monitoring.

The system is built around the Omnichain Synapse Agent, an intelligent LLM-powered entity that orchestrates specialized tools, interacts with Avalanche blockchain network, and operates within a usage-based monetization framework powered by the x402 Payment Protocol.

This README documents the architecture, setup, environment variables, APIs, and deployment for the entire repository.

## ✨ Key Features

Multi-Agent Orchestration: Utilizes the ReAct (Reasoning and Acting) framework within a custom OmnichainSynapseAgent to analyze user intent, select appropriate tools, and execute complex multi-step tasks.

x402 Protocol Integration: Implements the open x402 standard to enforce machine-to-machine, usage-based crypto payments for premium tools and services, ensuring automated monetization and access control.

Omnichain Strategy & Trade Tools: Seamlessly integrates tools for fetching market data (CoinMarketCap, CoinGecko, Chainbase), building trading strategies, and executing trades triggers.

Real-time Monitoring Service: A dedicated microservice for asynchronously evaluating user-defined, condition-based strategies and triggering notifications when market criteria are met.

## Repository Structure

- `monitoring-service/` — FastAPI service for strategy evaluation and trigger logging.
- `synapse-api/` — FastAPI backend for user authentication, market data, and strategy management (Supabase/Postgres).
- `spoon-core/` — Agent runtime with tool orchestration, MCP-style integrations, and premium x402 payment gating.

## Tech Stack

- FastAPI, Uvicorn
- SQLAlchemy Async, Psycopg (binary)
- Redis (aioredis) for caching
- Aiohttp/Requests for external APIs
- Web3 (for x402 payment verification on Avalanche)
- Pydantic, dotenv

## Quick Start

Clone the repository:

```bash
git clone https://github.com/your-org/Omnichain-Synapse.git
```

Change to repo root:

```bash
cd Omnichain-Synapse
```

This monorepo contains three independent Python services. For clean isolation, use separate Python environments per service.

### Prerequisites

- Windows recommended; commands below are Windows-friendly.
- Python versions:
  - `monitoring-service`: Python 3.10
  - `spoon-core`: Python 3.10
  - `synapse-api`: Python 3.11
- Postgres database (Supabase or local)
- Redis instance (local or managed)
- For premium tools: Avalanche RPC access and an on-chain wallet

## Environment Variables

Create `.env` files in each service directory based on provided `.env.example` files where available.

### monitoring-service/.env

- `POSTGRES_URL` — Postgres DSN (use psycopg/async-capable URL, the service will normalize to `postgresql+psycopg://`)
- `REDIS_URL` — Redis connection string (e.g. `redis://localhost:6379`)
- `MONITORING_HOST` — Host binding, default `0.0.0.0`
- `MONITORING_PORT` — Port, default `9000`
- `ENABLE_WEBSOCKETS` — `true`/`false`
- `ENABLE_SCHEDULER` — `true`/`false` (enables batched strategy evaluation loop)
- `SCHEDULER_INTERVAL_SECONDS` — scheduler loop interval
- `MONITORING_API_KEY` — API key required as header `X-Monitoring-Key`

### synapse-api/.env

- `POSTGRES_URL` — Supabase DSN (normalized to `postgresql+psycopg://` internally, `sslmode` stripped)
- `PRIVY_APP_ID`, `PRIVY_APP_SECRET`, `PRIVY_JWKS_URL` — Privy auth config
- `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRE_HOURS` — JWT settings
- `ALLOWED_ORIGINS` — JSON array or CSV of allowed origins
- `COINGECKO_API_KEY`, `BINANCE_API_KEY`, `BINANCE_SECRET_KEY` — optional external providers
- `CHAINBASE_API_KEY` — optional, if needed by certain tools
- `ENVIRONMENT` — `development`/`production`

### spoon-core/.env

- LLM keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.
- x402/premium tool config:
  - `AVALANCHE_RPC` — RPC endpoint URL
  - `TREASURY_ADDRESS` — recipient address for premium tool payments
  - `PREMIUM_TOOL_FEE_WEI` — minimum required fee in wei
- Optional: `CHAINBASE_API_KEY` (if calling `premium_chainbase`)

## Service Setup and Run

### monitoring-service

Install and run:

```bash
python -m pip install -r monitoring-service/requirements.txt
```

```bash
uvicorn monitoring-service.app:app --host 0.0.0.0 --port 9000
```

- Startup tasks:
  - Validates `REDIS_URL` via `cache.redis_client.test_redis_connection`.
  - If `POSTGRES_URL` is set, initializes async SQLAlchemy engine and, if `ENABLE_SCHEDULER=true`, starts `BatchedScheduler`.
- Scheduler:
  - Evaluates active strategies on an interval (`SCHEDULER_INTERVAL_SECONDS`).
  - Uses `DataPrefetcher` to cache and fetch price/klines via `AsyncBinanceClient` and `AsyncCoinGeckoClient`.
  - Applies `ConditionEvaluator` (price, RSI, SMA/EMA, MACD, Bollinger, volume) and `LogicTreeEvaluator` (AND/OR).
  - Logs triggers as `StrategyTriggerLog` and updates `Strategy` stats.

Endpoints:
- `GET /health` — service health
- Router mounted at `/internal` requiring `X-Monitoring-Key`:
  - `GET /internal/health`
  - `GET /internal/strategies` — list active strategies
  - `GET /internal/trigger_logs` — list all trigger logs
  - `POST /internal/trigger_log` — create a trigger log
  - `GET /internal/metrics` — counts of active strategies and total logs
  - `POST /internal/reload_strategies` or `/internal/reload-strategies` — reloads active strategies
  - `GET /internal/simulate/{strategy_id}` — basic simulated evaluation snapshot
  - `GET /internal/cache/get?key=prices:BTC` — read Redis key

Model highlights:
- `Strategy` — normalized `conditions`, `logic_tree` (refs + groups), `schedule`, `assets`, `notification_preferences`, `required_data`, status and stats.
- `StrategyCondition` — typed payload with enable toggle.
- `StrategyTriggerLog` — stores `triggered_at`, snapshot, message.

### synapse-api

Install and run:

```bash
python -m pip install -r synapse-api/requirements.txt
```

```bash
python synapse-api/run_synapse.py
```

- Lifecycle:
  - CORS, logging setup, DB init via `core.db.init_db` (normalizes DSN to psycopg, removes `sslmode`).
- Routers:
  - `auth` — authentication endpoints.
  - `market` — market data endpoints.
  - `strategy` — strategy CRUD plus agent gateway.

Strategy endpoints:
- `POST /strategies` — authenticated via `get_current_user`, request body `StrategyCreateSchema`.
- `POST /strategies/agent` — agent gateway: uses `get_current_user_from_privy_token` (validate using raw Privy token in headers).
- `GET /strategies` — list for current user, filterable by status.
- `GET /strategies/{strategy_id}` — retrieve one.
- `PUT /strategies/{strategy_id}` — update.
- `DELETE /strategies/{strategy_id}` — delete.

Run directly via uvicorn:

```bash
uvicorn synapse-api.app:app --host 0.0.0.0 --port 8000
```

### spoon-core (Agent Server + CLI)

Install:

```bash
python -m pip install -r spoon-core/requirements.txt
```

Agent Server (FastAPI):

```bash
uvicorn spoon_ai.agents.run_agent_server:app --host 0.0.0.0 --port 8765
```

- Endpoints:
  - `GET /` — online status
  - `GET /health` — agent health
  - `POST /chat` — body `{ "message": "...", "txn_hash": "..." }`
    - Extracts Privy token from headers and sets combined context via `tool_context` (txn hash + privy token).
    - When calling a premium tool (e.g., `premium_chainbase`), if payment verification fails, raises `PaymentRequiredException` → returned as HTTP 402 with payment instructions.

Payment Flow (x402):
- `premium_chainbase` checks `get_txn_hash()` and `verify_payment(txn_hash)`:
  - Ensures `to == TREASURY_ADDRESS` and `value >= PREMIUM_TOOL_FEE_WEI`.
- If missing/invalid payment:
  - Server returns 402 JSON: `recipient`, `amount_wei`, `chain`, `tool_name`.
- Client should:
  1. Pay specified amount to `TREASURY_ADDRESS` on Avalanche.
  2. Resubmit `POST /chat` with `txn_hash` set to on-chain transaction hash.

CLI:

```bash
python spoon-core/main.py
```

- Interactive CLI with tooling and optional MCP server integration.

## Data Access & Prefetching

- `AsyncBinanceClient` — accurate OHLCV klines and spot prices via Binance symbols (`BTC`, `ETH`), quote mapped from `usd`→`USDT`.
- `AsyncCoinGeckoClient` — CoinGecko data; klines derived from `market_chart` for recent windows (price and volume only).
- `DataPrefetcher` — redis-backed caching for `prices:{asset}` and `klines:{symbol:interval:limit:currency}` to reduce API calls.

## Database

- `monitoring-service`:
  - Initializes async SQLAlchemy via normalized psycopg DSN.
  - Stores `Strategy`, `StrategyCondition`, `StrategyTriggerLog`.

- `synapse-api`:
  - Async SQLAlchemy with psycopg-binary.
  - Alembic migrations under `migrations/`.
  - Models for users, strategies, etc.

## Deployment

Each service ships with a Dockerfile.

- monitoring-service:
  - Context should be the service directory, Dockerfile path `./Dockerfile`.
  - Command runs `uvicorn app:app --port 9000`.
- synapse-api:
  - Dockerfile installs PyYAML with `--no-build-isolation` and runs on port `8000`.
  - Health check hits `/health`.
- spoon-core:
  - Runs agent server on port `8765`.

Render (guidelines):
- Create three separate “Web Service” entries, one per service.
- Root Directory set to the specific service (`monitoring-service`, `synapse-api`, `spoon-core`).
- Dockerfile Path: `./Dockerfile`.
- Build Context Directory: `.`.
- Configure environment variables per service.

## Testing

- `monitoring-service/tests/` contains unit and integration tests for clients, evaluators, schedulers.
- `spoon-core/tests/` includes agent/tool tests.

## Common API Examples

Monitoring Service (requires `X-Monitoring-Key`):

```bash
curl -H "X-Monitoring-Key: YOUR_KEY" http://localhost:9000/internal/strategies
```

```bash
curl -H "X-Monitoring-Key: YOUR_KEY" http://localhost:9000/internal/trigger_logs
```

Agent Server (premium tool flow):

```bash
curl -X POST http://localhost:8765/chat -H "Content-Type: application/json" -d "{\"message\":\"query wallet\", \"txn_hash\": \"0x...\"}"
```

Synapse API (agent gateway with Privy token):

```bash
curl -X POST http://localhost:8000/strategies/agent -H "Authorization: Bearer PRIVY_TOKEN" -H "Content-Type: application/json" -d "{\"name\":\"My Strategy\", \"schedule\":\"1h\", \"assets\":[], \"notification_preferences\":{}, \"conditions\":[], \"logic_tree\": {\"operator\": \"AND\", \"conditions\": []}}"
```

## Notes and Caveats

- `spoon-core` has premium tools which require on-chain payment; ensure `AVALANCHE_RPC`, `TREASURY_ADDRESS`, and `PREMIUM_TOOL_FEE_WEI` are set.
- `monitoring-service` scheduler depends on `ENABLE_SCHEDULER=true` and valid Postgres/Redis configuration.
- CoinGecko klines are approximate (price/volume only); use Binance for accurate OHLCV.
- The Chainbase toolkit in `spoon-toolkits` may be missing; any Chainbase-specific imports in tool collections should be removed/updated accordingly.

## License

Proprietary. Do not distribute without permission.