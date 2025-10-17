Goals & Principles

- Keep the current agent backend (spoon-core) stable and separate.
- Introduce a new API service focused on data, analytics, signals, and portfolio.
- Reuse existing spoon-core modules (Binance clients, Chainbase tools, StrategyManager, CoinGeckoTool) where it saves time.
- Favor incremental delivery: wire the UI panels one-by-one with clear acceptance criteria.
- Ensure environment parity: local and Render configs behave consistently.
Target Architecture

- Agent Service (existing)
  
  - Endpoint POST /chat (already live).
  - Loads LLM via ChatBot , crypto tools, Qdrant for strategies.
  - No changes except minor bug fixes or compatibility patches.
- Synapse API Service (new)
  
  - FastAPI app exposing REST/WebSocket APIs for dashboard, portfolio, strategies, analytics, market data, and signals.
  - Background tasks for data ingestion, signal generation, risk computations.
  - Storage: Qdrant (already in use) plus a relational DB (Render Managed PostgreSQL) for time-series and portfolio persistence.
  - Caching: in-memory initially; optional Redis later for rate limits and hot data.
- Frontend Integration
  
  - UI calls Synapse API for each panel via GET/POST and subscribes to live updates via WebSockets (signals, alerts).
  - CORS configured to allow https://synapse-ui.vercel.app .
Proposed Monorepo Layout

- spoon-core/ (unchanged, agent backend)
- synapse-api/ (new service under current repo root)
  - app.py (FastAPI entry)
  - routers/ (per panel)
    - dashboard.py , portfolio.py , strategies.py , market_data.py , analytics.py , signals.py , health.py
  - services/ (business logic)
    - data_providers/ (coingecko.py, binance.py, chainbase.py)
    - portfolio_service.py , strategy_service.py , risk_service.py , signals_service.py
  - models/ (Pydantic schemas)
  - storage/ (db.py for Postgres, qdrant.py adapter)
  - tasks/ (scheduler.py for recurring jobs)
  - config.py (env management; OpenRouter, Chainbase, Qdrant, DB)
  - Dockerfile , requirements.txt (separate Render service)
UI → Backend Mapping

- Dashboard
  
  - Aggregates portfolio value, 24h P&L, active strategies, success rate.
  - Endpoint: GET /dashboard returns summary metrics and top cards.
  - Uses PortfolioService + StrategyService + SignalsService + market prices.
- Portfolio
  
  - Tracks assets via user-linked wallets and/or manual entries.
  - Chainbase for on-chain balances (EVM, SOL, etc.), Binance for CEX balances (optional).
  - Endpoints:
    - GET /portfolio returns holdings breakdown (BTC/ETH/SOL/others).
    - POST /portfolio/link to register wallet addresses or CEX API keys.
    - GET /portfolio/history for P&L curve time series.
  - Storage: Postgres ( portfolios , positions , wallets ) + price history cache.
- Strategies
  
  - CRUD and performance metrics; leverage existing StrategyManager (Qdrant).
  - Endpoints:
    - GET /strategies list summaries (+ status, success rate).
    - POST /strategies create (validated via Pydantic Strategy ).
    - GET /strategies/{id}/performance returns backtest/live metrics.
  - Strategy runs tracked in Postgres ( strategy_runs ) + results persisted.
- Market Data
  
  - OHLC, trending, quotes from CoinGecko/Binance; on-chain stats via Chainbase.
  - Endpoints:
    - GET /market/trending (CoinGecko trending).
    - GET /market/ohlc?symbol=BTC&interval=1h (Binance, cache).
    - GET /market/token/{address} (Chainbase token metadata).
  - Background cache refresh jobs (APScheduler) respect provider rate limits.
- Analytics
  
  - Risk metrics (volatility, drawdown, VaR), correlations, sentiment.
  - Endpoints:
    - GET /analytics/risk?portfolio_id=...
    - GET /analytics/sentiment (fear & greed proxy + price breadth).
    - GET /analytics/correlation?symbols=BTC,ETH,SOL
  - Computations: on demand + scheduled refresh; results stored for faster UI.
- Signals
  
  - Live signals (BUY/SELL/HOLD + timeframe + confidence) from rules/indicators.
  - Endpoints:
    - GET /signals current list
    - WS /signals/live stream updates
  - Signal engine uses configurable strategies (RSI/MACD/Breakouts, liquidity alerts via Chainbase).
- Synapse Agent Panel
  
  - Continues to call spoon-core /chat for reasoning + tool calls.
  - Optionally enhanced to cross-call Synapse API endpoints for context.
Data Sources & Connectors

- CoinGecko (prices, trending, no key) for light-weight quote data.
- Binance (OHLC, depth; client exists under spoon_ai/monitoring/clients/ ).
- Chainbase (on-chain balances, token metadata, transactions).
- Optional: Alternative.me for fear/greed (or compute internal sentiment proxy).
Storage Strategy

- Postgres (Render Managed):
  - users , portfolios , wallets , positions
  - signals (type, symbol, timeframe, confidence, metadata)
  - strategy_runs (metrics, timestamps)
  - market_ohlc (optional local cache if needed)
- Qdrant (existing):
  - Strategies vector data.
- No Redis initially; add later for caching/rate-limits if necessary.
Background Jobs

- Scheduler (APScheduler/async):
  - Refresh OHLC caches (minutely/hourly per symbol).
  - Recompute risk metrics and correlations daily/hourly.
  - Run signal detectors every 1–5 minutes depending on timeframe.
- Graceful startup/shutdown with FastAPI lifespan.
Security & Config

- Environment variables:
  - OPENAI_BASE_URL (OpenRouter), OPENAI_API_KEY (OpenRouter key)
  - CHAINBASE_API_KEY , BINANCE_API_KEY/SECRET (if needed)
  - QDRANT_HOST , QDRANT_API_KEY
  - POSTGRES_URL (Render DB)
  - ALLOWED_ORIGINS ( https://synapse-ui.vercel.app )
- CORS
  - Allow Vercel domain; keep localhost origins for dev.
- Auth
  - Phase 1: no auth or simple bearer.
  - Phase 2: user-bound portfolio endpoints require auth.
Non-Disruptive Delivery

- Keep spoon-core service untouched for agent flows.
- Launch synapse-api as a separate Render service with its own Dockerfile .
- Frontend switches panel calls to https://<synapse-api-host>/... progressively.
Deployment & Ops

- Render:
  - New Web Service for synapse-api .
  - Health endpoint GET /healthz .
  - Logging using Python logging with JSON format for structured logs.
- Observability:
  - Request/response timing, error rates per endpoint.
  - Background job metrics (last run time, durations).
- Resilience:
  - Retry/backoff wrappers on provider calls.
  - Circuit-breaker for flaky sources.
  - Graceful degradation (fallbacks to cached/stale data with flags).
Incremental Milestones

- Milestone 0: Environment parity
  
  - Ensure OPENAI_BASE_URL=https://openrouter.ai/api/v1 on Render agent service.
  - Confirm spoon-toolkits loads on Render or log installation failures clearly.
- Milestone 1: Synapse API scaffolding
  
  - Create FastAPI app, CORS, health, basic config loader.
  - Deploy a “hello world” endpoint to Render.
- Milestone 2: Market Data endpoints
  
  - GET /market/trending , GET /market/ohlc .
  - Cache layer with freshness TTL; UI wires “Market Data” panel.
- Milestone 3: Signals engine + live updates
  
  - Implement signal rules for AVAX/MATIC/DOT/LINK as in UI.
  - GET /signals , WS /signals/live endpoint; UI wires “Live Signals”.
- Milestone 4: Portfolio service
  
  - Wallet linking, on-chain balances via Chainbase.
  - GET /portfolio breakdown; UI wires “Portfolio” and Dashboard cards.
- Milestone 5: Risk analytics
  
  - Volatility, drawdown, simple VaR, correlation matrix.
  - GET /analytics/risk , GET /analytics/correlation ; UI wires “Risk Analysis”.
- Milestone 6: Strategy performance
  
  - Integrate StrategyManager + backtest using OHLC cache.
  - GET /strategies/{id}/performance ; UI wires “Strategy Performance”.
- Milestone 7: Dashboard aggregate
  
  - Compose cards from portfolio + strategies + signals.
  - GET /dashboard returns all top-level KPIs.
- Milestone 8: Hardening
  
  - Rate limits, pagination, better error handling, retries.
  - Add structured logs, metrics, and minimal auth for user-bound endpoints.
Acceptance Criteria per Panel

- Dashboard: returns consistent values for Portfolio Value, P&L, Active Strategies, Success Rate; updates at least every minute.
- Portfolio: loads holdings from wallets (on-chain) and displays breakdown; supports at least ETH and SOL chains.
- Market Data: trending and OHLC endpoints return data under 500ms p95 with caching.
- Signals: live stream produces BUY/SELL/HOLD with confidence and timeframe; UI updates without refresh.
- Analytics: risk metrics and correlations computed over configurable lookback windows; returned as JSON ready for charts.
- Strategies: performance endpoint returns win-rate, Sharpe-lite, and cumulative returns for selected strategy.
Risk & Dependencies

- Provider rate limits (Binance/Chainbase) — mitigate with caching, staggered jobs.
- Data consistency across chains — normalize units and token metadata via Chainbase.
- Render resource limits — jobs tuned for runtime tier; move heavy tasks to scheduled batches.