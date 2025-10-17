# Task List: Synapse API — Feature-Oriented Backend (Privy Auth + Supabase Postgres)

This task list defines a robust architecture and phased implementation for the new `synapse-api` backend powering Authentication, Portfolio, Market Data, Signals, Analytics, and Strategies — while keeping the `spoon-core` agent service untouched. Mark tasks as `[x]` when completed.

Works on local and in Render with the same flow and environment variables.

---

## 0. Architecture & Repository Layout

- [ ] Create `synapse-api` service with feature-based structure (Postgres-first; Supabase connection via `POSTGRES_URL`):

```
synapse-api/
app.py
core/
  config.py            # pydantic-settings; env management
  db.py                # Postgres session (SQLAlchemy), Alembic init
  security.py          # CORS config, JWT helpers, auth dependency
  logging.py           # structured logging config
  errors.py            # error types + global exception handlers
providers/
  privy.py             # JWKS verification + claims normalization
  chainbase.py         # on-chain balances, token metadata
  coingecko.py         # prices + trending (lightweight)
  binance.py           # OHLC, quotes (REST)
auth/
  router.py            # /auth endpoints
  service.py           # auth orchestration
  models.py            # UserProfile, Identity models
  repository.py        # users/identities persistence (Postgres)
  webhook.py           # optional Privy webhooks
portfolio/
  router.py
  service.py
  models.py
  repository.py
market/
  router.py
  service.py
  models.py
  cache.py
signals/
  router.py
  service.py
  engine/
    rules.py           # rsi/macd/breakouts; config-driven
  models.py
  repository.py
  websocket.py         # WS /signals/live
analytics/
  router.py
  service.py
  models.py
strategies/
  router.py
  service.py
  models.py
  repository.py        # Postgres for runs; Qdrant for vectors
tests/
  unit/
  integration/
Dockerfile
requirements.txt
alembic.ini
migrations/            # Alembic migration scripts
.env.example
```

**Architecture principles:**
- Keep `spoon-core` (agent) unchanged; all new features live in `synapse-api`.
- Feature-sliced backend: each domain owns its router/service/models/repository.
- Shared infra in `core/` and external connectors in `providers/`.
- Postgres-first on Supabase; Qdrant remains for vectors (strategies).

---

## 1. Environment & Configuration

- [ ] Define env variables (identical locally and on Render):
  - [ ] `ALLOWED_ORIGINS="https://synapse-ui.vercel.app,http://localhost:3000,http://localhost:8080"`
  - [ ] `POSTGRES_URL` (Supabase Postgres connection string)
  - [ ] `PRIVY_APP_ID`
  - [ ] `PRIVY_JWKS_URL` (Privy JWKS endpoint for RS256 verification)
  - [ ] `CHAINBASE_API_KEY`
  - [ ] `BINANCE_API_KEY` and `BINANCE_API_SECRET` (optional)
  - [ ] `QDRANT_HOST`, `QDRANT_API_KEY`
- [ ] Implement `core/config.py` via `pydantic-settings` + `.env`
- [ ] Implement `core/security.py` for CORS and JWT helpers (bearer auth dependency)

**Acceptance:**
- Env variables load consistently in local and deployed environments.
- CORS allows Vercel + localhost dev origins.

---

## 2. Database (Supabase Postgres) & Migrations

- [ ] Add SQLAlchemy + Alembic setup in `core/db.py`
- [ ] Design initial schema + migrations:
  - [ ] `users` (id [privy_user_id], email, name, picture, created_at)
  - [ ] `identities` (user_id, type: email/google/twitter/wallet/passkey, value, verified_at)
  - [ ] `wallets` (user_id, address, chain, label, verified_via_privy)
  - [ ] `portfolios`, `positions` (asset, qty, source, timestamps)
  - [ ] `signals` (symbol, timeframe, type, confidence, metadata jsonb, created_at)
  - [ ] `strategy_runs` (strategy_id, metrics jsonb, started_at, finished_at)
- [ ] Create indexes for common queries (e.g., `wallets(user_id)`, `signals(symbol,timeframe)`)

**Acceptance:**
- Migrations run cleanly against Supabase Postgres.
- Tables and indexes created and visible via Supabase console.

---

## 3. Authentication (Privy Web2 + Web3)

- [ ] Implement `providers/privy.py`:
  - [ ] Verify RS256 JWT via `PRIVY_JWKS_URL` and `PRIVY_APP_ID` (audience)
  - [ ] Normalize claims to `UserProfile` + identities (email/social/wallet/passkey)
- [ ] Build `auth/service.py`:
  - [ ] Verify token, upsert user + identities in Postgres
  - [ ] Optional: issue short-lived server session for WS auth
- [ ] Build `auth/router.py`:
  - [ ] `POST /auth/verify` { token } → verifies, upserts, returns normalized profile
  - [ ] `GET /auth/me` (Bearer token) → returns current user
  - [ ] `POST /auth/logout` (if server sessions used)
  - [ ] `POST /auth/webhook` (optional) for Privy events
- [ ] Add `core/security.py` auth dependency for protected routes

**Acceptance:**
- Privy modal (email, Google, Twitter, wallet, passkey) logs in successfully.
- Backend verifies token and persists user.
- `GET /auth/me` returns identities + wallets.
- Missing/invalid token returns 401.

---

## 4. Market Data

- [ ] Implement `providers/coingecko.py` for trending + quotes
- [ ] Implement `providers/binance.py` for OHLC & quotes (REST; cache results)
- [ ] Build `market/service.py` with caching and rate limiting
- [ ] Build `market/router.py`:
  - [ ] `GET /market/trending`
  - [ ] `GET /market/ohlc?symbol=&interval=`
  - [ ] `GET /market/quote?symbol=`

**Acceptance:**
- p95 latency under 500ms using cache.
- Clear error handling and freshness metadata.

---

## 5. Portfolio

- [ ] Implement `providers/chainbase.py` for on-chain balances + token metadata
- [ ] Build `portfolio/service.py` to aggregate on-chain holdings (+ optional CEX)
- [ ] Build `portfolio/router.py`:
  - [ ] `POST /portfolio/link` (wallet or CEX credentials)
  - [ ] `GET /portfolio` (asset breakdown)
  - [ ] `GET /portfolio/history` (P&L time series)

**Acceptance:**
- ETH + SOL chains supported initially.
- Holdings reflect user-linked wallets.
- Dashboard top cards sourced from portfolio endpoints.

---

## 6. Signals & Live Updates

- [ ] Implement `signals/engine/rules.py` (RSI, MACD, breakouts, liquidity alerts)
- [ ] Build `signals/service.py` (APScheduler periodic computations)
- [ ] Build `signals/websocket.py` (`WS /signals/live`) for streaming
- [ ] Build `signals/router.py` (`GET /signals`)

**Acceptance:**
- Live stream produces BUY/SELL/HOLD with confidence and timeframe.
- UI updates without page refresh via WebSockets.

---

## 7. Analytics

- [ ] Implement analytics (volatility, drawdown, VaR-lite, correlation matrix)
- [ ] Build `analytics/service.py` with compute + caching
- [ ] Build `analytics/router.py`:
  - [ ] `GET /analytics/risk?portfolio_id=...`
  - [ ] `GET /analytics/correlation?symbols=...`

**Acceptance:**
- Configurable lookbacks; JSON results ready for charts.
- Performance acceptable for dashboard usage.

---

## 8. Strategies

- [ ] Integrate Qdrant (existing StrategyManager where appropriate) for vectors
- [ ] Build `strategies/service.py` and `strategies/repository.py`
- [ ] Build `strategies/router.py`:
  - [ ] `GET /strategies` list
  - [ ] `POST /strategies` create
  - [ ] `GET /strategies/{id}/performance` metrics
  - [ ] `PUT /strategies/{id}` update status

**Acceptance:**
- CRUD works with user isolation.
- Performance returns win-rate and cumulative returns.

---

## 9. App Shell & Core

- [ ] Implement `app.py` with lifespan startup/shutdown
- [ ] Include routers: `health`, `auth`, `market`, `portfolio`, `signals`, `analytics`, `strategies`
- [ ] Maintain consistent error responses; structured logs via `core/logging.py`
- [ ] Health endpoint: `GET /healthz`

**Acceptance:**
- Service boots with clean logs, health endpoint returns `ok`.
- Errors shaped with consistent JSON format.

---

## 10. Observability & Security

- [ ] Structured logging (request IDs, duration)
- [ ] Basic rate limiting for public endpoints
- [ ] Input validation with Pydantic models
- [ ] Secrets handling: no raw tokens in logs; encrypt sensitive creds
- [ ] Optional: `/metrics` for basic telemetry

**Acceptance:**
- Logs useful for debugging without leaking secrets.
- Rate limits protect from abuse.

---

## 11. Testing & QA

- [ ] Unit tests per feature (auth, market, portfolio, signals, analytics, strategies)
- [ ] Integration: login → `/auth/verify` → `/auth/me`
- [ ] Mock providers to avoid hitting external APIs in CI
- [ ] Load tests for market endpoints with cache enabled

**Acceptance:**
- CI passes; mocks keep tests deterministic.
- Basic load test meets latency targets.

---

## 12. Deployment

- [ ] Create `synapse-api/Dockerfile`
- [ ] Render: new Web Service for `synapse-api` (or Supabase functions if preferred for edge tasks)
- [ ] Configure env vars (Privy, Postgres/Supabase, Qdrant, Chainbase)
- [ ] CORS includes Vercel domain
- [ ] Rollouts safe; `spoon-core` (agent) remains unchanged

**Acceptance:**
- Successful deployment; endpoints reachable from UI.
- No disruption to agent backend.

---

## 13. Milestones (Sequential Delivery)

- [ ] Milestone A: Scaffolding (core, health, CORS, Postgres, Alembic)
- [ ] Milestone B: Authentication (Privy JWKS, `/auth/verify`, `/auth/me`)
- [ ] Milestone C: Market Data (trending, OHLC, caching)
- [ ] Milestone D: Signals (rules, scheduler, WS live)
- [ ] Milestone E: Portfolio (link wallets, on-chain balances)
- [ ] Milestone F: Analytics (risk, correlation)
- [ ] Milestone G: Strategies (CRUD + performance)
- [ ] Milestone H: Hardening (rate limits, logging, metrics, tests)

---

### Notes

- **Supabase Postgres**: Use your Supabase connection string in `POSTGRES_URL`. This keeps the backend provider-agnostic while giving you managed Postgres.
- **Feature isolation**: Each feature has its own folder with `router/service/models/repository` and pulls shared infra from `core/` and connectors from `providers/`.
- **Non-disruptive**: Agent backend (`spoon-core`) remains as-is; Synapse UI panels call `synapse-api`.
- **Paritized env**: Same variable names and behavior locally and in deployment.
