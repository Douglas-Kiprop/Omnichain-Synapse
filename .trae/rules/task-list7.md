# Task List 7: Autonomous Monitoring Service Re-Architecture (Formatted like task-list6.md)

---



## 0. Architecture & Repository Layout

* [ ] **Dedicated Service Approach**:

  * `synapse-api`: Handles strategy CRUD, auth, and user-facing APIs (port 8000). Owns DB schema.
  * `monitoring-service`: New standalone FastAPI service for loading, evaluating, and triggering strategies (port 9000). Fetches from DB directly; syncs via Redis Pub/Sub or HTTP webhooks.
  * `spoon-core`: Treated as a shared Python library (`pip install -e`). Reuses monitoring clients, notifiers, and scheduler modules.

* [ ] **New `monitoring-service` Directory Structure**:

  * [ ] `app.py`: FastAPI entrypoint with health/metrics.
  * [ ] `core/`: Engine logic.

    * [ ] `strategy_loader.py`
    * [ ] `data_prefetcher.py`
    * [ ] `condition_evaluator.py`
    * [ ] `logic_tree_evaluator.py`
    * [ ] `trigger_handler.py`
    * [ ] `batched_scheduler.py`
  * [ ] `clients/`: Async CEX/DEX clients.
  * [ ] `notifiers/`: Strategy-specific wrappers.
  * [ ] `cache/`: Redis integration.
  * [ ] `api/`: Internal routes.
  * [ ] `models/`: Imported from `synapse-api`.
  * [ ] `config.py`, `requirements.txt`, `Dockerfile`, `.env.example`.

* [ ] **Inter-Service Communication**:

  * [ ] Redis Pub/Sub: `strategy:updated` events.
  * [ ] Optional HTTP webhook from `synapse-api` → `monitoring-service`.

**Acceptance:**

* [ ] Repo layout created.
* [ ] Monitoring service boots on port 9000.
* [ ] `/health` returns `{ "status": "ok" }`.

---

## 1. Environment & Configuration

* [ ] Define environment variables in `monitoring-service/.env.example`:

  * [ ] `POSTGRES_URL`
  * [ ] `REDIS_URL`
  * [ ] `MONITORING_HOST`, `MONITORING_PORT`
  * [ ] `ENABLE_WEBSOCKETS`
  * [ ] Reuse notifier vars from spoon-core.

* [ ] Create `monitoring-service/config.py` using `pydantic-settings`.

* [ ] Update `synapse-api/core/config.py` with `MONITORING_SERVICE_URL`.

* [ ] Install `spoon-core` as editable dependency.

**Acceptance:**

* [ ] Config loads without errors.
* [ ] Redis/DB connections verified at startup.

---

## 2. Database (Shared Postgres) & Migrations

* [ ] Reuse existing strategy schema from `synapse-api`.
* [ ] Import models into `monitoring-service/models`.
* [ ] Add optimized loader queries (e.g., `selectinload`).
* [ ] Create async session factory.

**Acceptance:**

* [ ] Monitoring service can query strategies and write trigger logs.
* [ ] Queries efficient for 100+ strategies.

---

## 3. Authentication

* [ ] Use shared Postgres creds.
* [ ] Redis ACL if enabled.
* [ ] Internal API key auth (`X-MONITORING-KEY`).
* [ ] No user-facing auth inside monitoring-service.

**Acceptance:**

* [ ] Unauthorized /internal/- → 401.
* [ ] Authorized webhook triggers reload.

---

## 4. Market Data (Async Clients & Prefetcher)

* [ ] Extend spoon-core clients to async versions.
* [ ] Implement async Binance, Uniswap, Coingecko clients.
* [ ] Implement `DataPrefetcher` to batch fetch, cache, compute indicators.
* [ ] Integrate Redis for caching.
* [ ] Retry with tenacity + fallback.
* [ ] Optional WebSockets.

**Acceptance:**

* [ ] 10 strategies sharing BTC produce 1 upstream API call.
* [ ] Cache hit rate >95%.

---

## 5. Strategy Loader

* [ ] Implement loader to fetch and inline strategy structures.
* [ ] Validate logic trees.
* [ ] Compute required data.
* [ ] Cache resolved config in Redis.
* [ ] Implement reload mechanism.

**Acceptance:**

* [ ] Load 100 strategies in <1s.
* [ ] Invalid tree → mark strategy error.

---

## 6. Evaluators (Conditions & Logic Tree)

* [ ] Condition evaluator with registry:

  * price_alert
  * technical_indicator
* [ ] Logic-tree evaluator with short-circuiting.

**Acceptance:**

* [ ] Evaluate complex trees correctly.
* [ ] 50 conditions <50ms.

---

## 7. Trigger Handler & Notifiers

* [ ] Extend notifier wrapper.
* [ ] Implement templated strategy notifications.
* [ ] Insert trigger logs.
* [ ] Apply cooldown.

**Acceptance:**

* [ ] Multi-channel notifications.
* [ ] Cooldown respected.

---

## 8. Batched Scheduler

* [ ] Extend scheduler to group strategies by frequency.
* [ ] Implement batch evaluation jobs.
* [ ] Integrate with startup process.

**Acceptance:**

* [ ] Batches evaluate <500ms for 20 strategies.
* [ ] Manual run endpoint works.

---

## 9. API & Integration with `synapse-api`

* [ ] Internal API routes:

  * [ ] `/internal/reload-strategies`
  * [ ] `/internal/simulate/{strategy_id}`
  * [ ] `/metrics`
* [ ] Add Redis pub/sub or webhook integration from `synapse-api`.

**Acceptance:**

* [ ] Strategy reload fires reliably.
* [ ] Simulation returns snapshot.

---

## 10. App Shell & Core

* [ ] Build FastAPI app with CORS + routes.
* [ ] Startup loads strategies + starts scheduler.
* [ ] Shutdown stops scheduler.
* [ ] Add Prometheus metrics.

**Acceptance:**

* [ ] Service boots/stops cleanly.
* [ ] Metrics at `/metrics`.

---

## 11. Observability & Security

* [ ] Add metrics for hits, triggers, latency.
* [ ] Structured logging everywhere.
* [ ] Sanitize snapshots.
* [ ] Rate limit internal API.

**Acceptance:**

* [ ] Grafana dashboards populate.
* [ ] Logs are structured and filterable.

---

## 12. Testing & QA

* [ ] Unit tests for loader, evaluators, prefetcher, triggers.
* [ ] Integration tests for eval loops.
* [ ] E2E tests with docker-compose.

**Acceptance:**

* [ ] 90% coverage.
* [ ] Load test: 10k evals/min.

---

## 13. Deployment

* [ ] Deploy monitoring-service via Docker/Kubernetes.
* [ ] Add HPA.
* [ ] Update synapse-api deployment.
* [ ] Configure CI/CD pipelines.

**Acceptance:**

* [ ] 24/7 uptime.
* [ ] Zero-downtime rolling deploy.

---

## 14. Milestones (Sequential Delivery)

* [ ] **Milestone 1: Foundation (Week 1)**

  * Repo, config, DB integration.
  * Loader + scheduler init.

* [ ] **Milestone 2: Data & Eval (Week 2)**

  * Async clients, prefetcher.
  * Condition + logic-tree evaluators.

* [ ] **Milestone 3: Triggers & API (Week 3)**

  * Notifiers + trigger handler.
  * Internal API + sync.

* [ ] **Milestone 4: Polish & Scale (Week 4)**

  * Caching, retries, observability.
  * Tests + deployment.

* [ ] **Milestone 5: Extras**

  * WebSockets.
  * ML hooks.
  * Backtesting endpoint.

---

## Notes

* Shared DB is source of truth.
* Dedicated monitoring-service enables independent scaling.
* Extensible condition registry for future chains.
* Simulation endpoint recommended for UX.
* High-load mitigation: shard by user_id; batch DB queries.


monitoring-service/
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── requirements.txt
├── pyproject.toml                    # optional (if using poetry)
├── app.py                            # FastAPI entrypoint + startup/shutdown
├── config.py                         # Settings via pydantic-settings
├── main.py                           # alias for app.py (optional)
│
├── core/
│   ├── __init__.py
│   ├── strategy_loader.py            # Loads + resolves active strategies from DB
│   ├── data_prefetcher.py            # Async batch data fetching + Redis cache
│   ├── condition_evaluator.py        # Typed condition evaluation (price_alert, RSI, etc.)
│   ├── logic_tree_evaluator.py       # Recursive AND/OR tree resolver
│   ├── trigger_handler.py            # Cooldowns, notifications, DB logs
│   ├── batched_scheduler.py          # Groups strategies by schedule → batch jobs
│   └── metrics.py                    # Prometheus counters/histograms
│
├── clients/
│   ├── __init__.py
│   ├── async_binance.py              # aiohttp version of Binance client
│   ├── async_coingecko.py            # Fallback price provider
│   ├── async_uniswap.py              # Async DEX client (Alchemy/Infura)
│   └── base.py                       # Abstract async client interface
│
├── notifiers/
│   ├── __init__.py
│   ├── notification_manager.py       # Wrapper around spoon-core's NotificationManager
│   └── templates.py                  # Rich Markdown alert templates
│
├── cache/
│   ├── __init__.py
│   ├── redis_client.py               # aioredis connection + helpers
│   └── keys.py                       # Cache key constants (prices:BTC, klines:BTC:1h)
│
├── api/
│   ├── __init__.py
│   ├── routes.py                     # Internal endpoints (/internal/reload, /simulate)
│   └── dependencies.py               # Auth key check, DB session
│
├── db/
│   ├── __init__.py
│   ├── session.py                    # Async SQLAlchemy session factory
│   └── base.py                       # Re-export Base from synapse-api
│
├── models/
│   ├── __init__.py
│   └── strategy.py                   # Re-import from synapse-api (symlink or copy)
│   #   └── (Strategy, StrategyCondition, StrategyTriggerLog, enums, schemas)
│
├── utils/
│   ├── __init__.py
│   ├── logger.py                     # Structured logging setup
│   ├── exceptions.py
│   └── helpers.py                    # Duration parser, cron parsing, etc.
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # DB + Redis fixtures
│   ├── unit/
│   │   ├── test_strategy_loader.py
│   │   ├── test_evaluators.py
│   │   ├── test_prefetcher.py
│   │   └── test_trigger_handler.py
│   └── integration/
│       └── test_full_eval_cycle.py
│
└── scripts/
    ├── run.sh                        # dev startup script
    ├── reload_strategies.py          # manual reload trigger
    └── simulate_strategy.py          # CLI simulation tool