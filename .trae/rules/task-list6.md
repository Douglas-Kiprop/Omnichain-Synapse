# Task List: Autonomous Strategy Monitoring & Telegram Notifications

This task list defines the implementation for autonomous strategy monitoring and Telegram notifications, leveraging both the `synapse-api` for strategy persistence and the `spoon-core` agent service for monitoring logic and alerts.

---

## 0. Architecture & Repository Layout

- [ ] **Two-Backend Approach**:
  - `synapse-api`: Will serve as the central data store for user-defined strategies, utilizing its robust Postgres database.
  - `spoon-core`: Will host the agent logic, monitoring service, and notification capabilities. It will fetch strategy definitions from `synapse-api` and execute monitoring tasks.
- [ ] **New `synapse-api/strategy` Module**:
  - [ ] `router.py`: FastAPI endpoints for strategy CRUD operations.
  - [ ] `service.py`: Business logic for interacting with strategy data in the database.
  - [ ] `models.py`: SQLAlchemy/Pydantic models for strategy definitions.
- [ ] **Leveraging `spoon-core/spoon_ai/monitoring`**:
  - [ ] `spoon_ai/monitoring/main.py`: The dedicated monitoring FastAPI service.
  - [ ] `spoon_ai/monitoring/core/scheduler.py`: For scheduling periodic strategy evaluations.
  - [ ] `spoon_ai/monitoring/core/tasks.py`: For defining monitoring tasks.
  - [ ] `spoon_ai/monitoring/core/strategy_evaluator.py` (new): For evaluating strategy conditions.
  - [ ] `spoon_ai/monitoring/clients`: For fetching market data for condition evaluation.
  - [ ] `spoon_ai/monitoring/notifiers/notification.py`: For dispatching notifications.
- [ ] **Leveraging `spoon-core/spoon_ai/social_media/telegram.py`**: For sending Telegram messages.

**Architecture principles:**
- `synapse-api` owns strategy data persistence and CRUD.
- `spoon-core`'s dedicated monitoring service handles strategy evaluation and notifications.
- `spoon-core`'s agent server (`run_agent_server.py`) will proxy strategy management requests to `synapse-api`.
- Clear separation of concerns between data storage, agent logic, and monitoring.

---

## 1. Environment & Configuration

- [ ] Define new environment variables:
  - [ ] `TELEGRAM_BOT_TOKEN`: For the Telegram bot in `spoon-core`.
  - [ ] `SYNAPSE_API_BASE_URL`: Base URL for `spoon-core` to access `synapse-api`'s endpoints.
  - [ ] `MONITORING_HOST` (if different from default `0.0.0.0`) and `MONITORING_PORT` (if different from default `8888`) for `spoon-core`'s monitoring service.
- [ ] Update `spoon-core`'s `.env.example` and `config.json` with new variables.
- [ ] Ensure `synapse-api`'s `core/config.py` is set up to manage its environment variables.

**Acceptance:**
- All necessary environment variables are defined and accessible in both `synapse-api` and `spoon-core`.
- `spoon-core`'s monitoring service can successfully connect to `synapse-api`.

---

## 2. Database (Supabase Postgres) & Migrations

- [ ] **New `strategies` table in `synapse-api`**:
  - [ ] Design a Pydantic/SQLAlchemy model for `Strategy` in `synapse-api/strategy/models.py` with the following fields:
    - `id` (UUID, primary key)
    - `user_id` (UUID, foreign key to `users` table)
    - `name` (str)
    - `description` (str)
    - `conditions` (JSONB, e.g., `[{ "type": "price_alert", "asset": "ETH", "operator": ">", "value": 3000 }]`)
    - `frequency` (str, e.g., "1h", "24h", "5m")
    - `notification_preferences` (JSONB, e.g., `{"telegram_chat_id": "123456789"}`)
    - `status` (str, e.g., "active", "paused", "triggered")
    - `created_at` (datetime)
    - `updated_at` (datetime)
- [ ] Create Alembic migration script in `synapse-api/migrations` to add the `strategies` table.
- [ ] Create indexes for common queries (e.g., `strategies(user_id, status)`).

**Acceptance:**
- `strategies` table is successfully created in the `synapse-api` database.
- Strategy data can be stored and retrieved with the defined schema.

---

## 3. Authentication

- [ ] Ensure `synapse-api`'s new strategy endpoints (`/strategies`) are protected by existing authentication mechanisms (e.g., Bearer token, `get_current_user` dependency).
- [ ] Ensure `spoon-core`'s monitoring service can securely authenticate with `synapse-api` to fetch strategies (e.g., using an API key or internal token if applicable).

**Acceptance:**
- Only authenticated users can manage their strategies via `synapse-api`.
- `spoon-core`'s monitoring service can reliably fetch strategies from `synapse-api`.

---

## 4. Market Data

- [ ] **Data Sourcing for Strategy Evaluation**:
  - [ ] `spoon-core`'s monitoring service will primarily use its own `spoon_ai/monitoring/clients` (CEX/DEX) to fetch real-time market data required for evaluating strategy conditions.
  - [ ] Extend `spoon_ai/monitoring/clients` as needed to support specific data points required by strategy conditions (e.g., specific price feeds, yield rates from DeFi protocols).
  - [ ] Implement robust error handling and retry mechanisms within `spoon_ai/monitoring/clients` for external API calls.

**Acceptance:**
- `spoon-core`'s monitoring service can reliably fetch all necessary market data to evaluate strategy conditions.

---

## 5. Portfolio (No changes for this task)

---

## 6. Signals & Live Updates (No changes for this task)

---

## 7. Analytics (No changes for this task)

---

## 8. Strategies (in `synapse-api`)

- [ ] **Implement Strategy CRUD Endpoints**:
  - [ ] Create `synapse-api/strategy/router.py` and `synapse-api/strategy/service.py`.
  - [ ] In `synapse-api/strategy/router.py`, define FastAPI endpoints:
    - `POST /strategies`: Create a new strategy.
    - `GET /strategies`: Retrieve all strategies for the authenticated user.
    - `GET /strategies/{strategy_id}`: Retrieve a specific strategy.
    - `PUT /strategies/{strategy_id}`: Update an existing strategy.
    - `DELETE /strategies/{strategy_id}`: Delete a strategy.
  - [ ] These endpoints will use `synapse-api/strategy/service.py` to interact with the database.
- [ ] **Update `spoon-core`'s `run_agent_server.py`**:
  - [ ] Modify the existing `/strategies` endpoints in `spoon_ai/agents/run_agent_server.py` to make HTTP calls to the new `synapse-api` strategy endpoints for persistence. This ensures the frontend interacts with `synapse-api` via `spoon-core`'s agent server.

**Acceptance:**
- Frontend can successfully create, retrieve, update, and delete strategies via `spoon-core`'s agent server, which then interacts with `synapse-api`.
- Strategies are correctly stored and managed in `synapse-api`'s database.

---

## 9. Strategy Monitoring & Notification (in `spoon-core`)

- [ ] **Integrate Telegram Client into Notifiers**:
  - [ ] Review `spoon_ai/monitoring/notifiers/notification.py` to understand its current structure.
  - [ ] Modify `spoon_ai/monitoring/notifiers/notification.py` to:
    - Import `TelegramClient` from `spoon_ai/social_media/telegram.py`.
    - Add a method (e.g., `send_telegram_notification(alert_message: str, chat_id: str)`) that utilizes `TelegramClient.send_proactive_message`.
    - Ensure `TelegramClient` is properly initialized with the `TELEGRAM_BOT_TOKEN`.
- [ ] **Implement Strategy Evaluation Logic**:
  - [ ] Create a new module: `spoon_ai/monitoring/core/strategy_evaluator.py`.
  - [ ] Define a function `evaluate_strategy(strategy: Strategy) -> Optional[str]` within this module:
    - Takes a `Strategy` object (Pydantic model, potentially fetched from `synapse-api`).
    - Parses its `conditions` (JSONB field).
    - Uses `spoon_ai/monitoring/clients` to fetch relevant market data.
    - Evaluates if the conditions are met.
    - If conditions are met, generates a descriptive alert message.
    - Returns the alert message (str) if triggered, otherwise `None`.
- [ ] **Integrate with `MonitoringTaskManager` and Scheduler**:
  - [ ] Review `spoon_ai/monitoring/core/scheduler.py` and `spoon_ai/monitoring/core/tasks.py`.
  - [ ] In `spoon_ai/monitoring/core/tasks.py` (or a new task file), define a `MonitorStrategyTask`:
    - This task will be responsible for:
      - Making an HTTP call to `synapse-api` to fetch all active strategies.
      - Iterating through each fetched `Strategy` object.
      - Calling `strategy_evaluator.evaluate_strategy()` for each strategy.
      - If an alert message is returned, calling the `send_telegram_notification` method in `spoon_ai/monitoring/notifiers/notification.py` with the alert message and the strategy's `telegram_chat_id`.
  - [ ] In `spoon_ai/monitoring/core/scheduler.py`, configure the scheduler to:
    - Schedule the `MonitorStrategyTask` to run at a configurable interval (e.g., every 5 minutes).
    - Implement logic to dynamically add/remove/update scheduled tasks as strategies are created/updated/deleted in `synapse-api`.
- [ ] **Error Handling and Logging**:
  - [ ] Implement comprehensive error handling for API calls to `synapse-api`, data fetching from clients, and Telegram notifications.
  - [ ] Ensure detailed logging within the `spoon_ai/monitoring` service for all events and errors.

**Acceptance:**
- `spoon-core`'s monitoring service runs continuously.
- Strategies are fetched from `synapse-api` and evaluated periodically.
- When strategy conditions are met, a Telegram notification is sent to the specified chat ID.
- Robust error handling prevents service crashes and provides clear logs.

---

## 10. App Shell & Core

- [ ] Update `synapse-api/app.py` to include the new `strategies` router.
- [ ] Ensure consistent error responses and structured logs across `synapse-api` (including new strategy endpoints).
- [ ] Ensure `spoon-core`'s monitoring service (`spoon_ai/monitoring/main.py`) starts cleanly and logs effectively.

**Acceptance:**
- Both `synapse-api` and `spoon-core` monitoring service boot without errors.
- New strategy endpoints are accessible and functional.

---

## 11. Observability & Security

- [ ] Apply existing `synapse-api` observability and security practices (structured logging, input validation, secrets handling) to the new strategy endpoints.
- [ ] Implement similar practices within `spoon-core`'s monitoring service.
- [ ] Consider rate limiting for `spoon-core`'s calls to `synapse-api` if fetching many strategies frequently.

**Acceptance:**
- New features adhere to existing security and observability standards.

---

## 12. Testing & QA

- [ ] **Unit Tests**:
  - [ ] For `synapse-api/strategy/service.py` (CRUD operations).
  - [ ] For `spoon_ai/monitoring/core/strategy_evaluator.py` (condition evaluation logic).
  - [ ] For `spoon_ai/monitoring/notifiers/notification.py` (Telegram integration).
  - [ ] For `spoon_ai/monitoring/core/tasks.py` (monitoring task logic).
- [ ] **Integration Tests**:
  - [ ] For `synapse-api/strategy/router.py` endpoints.
  - [ ] For the full `spoon-core` monitoring loop (fetching strategies, evaluating, notifying).
  - [ ] Mock external APIs (market data, Telegram) to ensure deterministic tests.

**Acceptance:**
- All new features are covered by unit and integration tests.
- Tests pass consistently.

---

## 13. Deployment

- [ ] **`synapse-api` Deployment**:
  - [ ] Update `synapse-api/Dockerfile` if necessary.
  - [ ] Deploy `synapse-api` with the new database schema (after running migrations).
  - [ ] Configure new environment variables (e.g., `POSTGRES_URL`).
- [ ] **`spoon-core` Monitoring Service Deployment**:
  - [ ] Determine if `spoon-core`'s monitoring service (`spoon_ai/monitoring/main.py`) will run as part of the main agent server or as a separate, dedicated service.
  - [ ] Create a `Dockerfile` or deployment configuration for the `spoon-core` monitoring service if it's a separate deployment.
  - [ ] Configure new environment variables (e.g., `TELEGRAM_BOT_TOKEN`, `SYNAPSE_API_BASE_URL`).

**Acceptance:**
- Both `synapse-api` and `spoon-core` monitoring service are successfully deployed and operational.
- End-to-end strategy monitoring and notification works in the deployed environment.

---

## 14. Milestones (Sequential Delivery)

- [ ] **Milestone 1: `synapse-api` Strategy Persistence**
  - [ ] Define `Strategy` model in `synapse-api`.
  - [ ] Create Alembic migration for `strategies` table.
  - [ ] Implement CRUD endpoints for strategies in `synapse-api`.
  - [ ] Update `spoon-core`'s `run_agent_server.py` to proxy strategy requests.
- [ ] **Milestone 2: `spoon-core` Strategy Evaluation**
  - [ ] Implement `spoon_ai/monitoring/core/strategy_evaluator.py`.
  - [ ] Ensure `spoon_ai/monitoring/clients` can fetch necessary data.
- [ ] **Milestone 3: `spoon-core` Notification Integration**
  - [ ] Integrate `TelegramClient` into `spoon_ai/monitoring/notifiers/notification.py`.
  - [ ] Configure `spoon-core` with `TELEGRAM_BOT_TOKEN`.
- [ ] **Milestone 4: `spoon-core` Monitoring Orchestration**
  - [ ] Define `MonitorStrategyTask` in `spoon_ai/monitoring/core/tasks.py`.
  - [ ] Configure `spoon_ai/monitoring/core/scheduler.py` to run the task.
  - [ ] Implement logic to fetch strategies from `synapse-api` within the monitoring service.
- [ ] **Milestone 5: End-to-End Testing & Refinement**
  - [ ] Comprehensive unit and integration tests.
  - [ ] Error handling and logging review.
  - [ ] Frontend integration (UI calls `synapse-api` via `spoon-core` agent server).

---

### Notes

- **`synapse-api` as Source of Truth**: `synapse-api` will be the single source of truth for all strategy definitions.
- **Dedicated Monitoring Service**: `spoon-core`'s `spoon_ai/monitoring` service will run as a separate, dedicated process, ensuring continuous, non-blocking monitoring.
- **Frontend Integration**: The frontend will interact with `spoon-core`'s agent server for strategy management, which then communicates with `synapse-api`.
- **User Instructions**: Clear instructions for users on setting up their Telegram bot and providing chat IDs will be necessary.



- Implement Strict, Type-Specific Pydantic Schemas for ConditionPayload :

- Action: Define a dedicated Pydantic BaseModel for each specific condition type . For example:
  - PriceAlertPayload(BaseModel): asset: str, direction: str, target_price: float
  - TechnicalIndicatorPayload(BaseModel): indicator: str, params: Dict[str, Any], operator: str, value: float, asset: str, timeframe: str (explicitly include timeframe here!)
  - ...and so on for every condition.type you support.
- Action: Modify ConditionCreate.payload to be a Union of these specific payload schemas. Use a Pydantic validator to dynamically select the correct schema based on the condition.type field.
- Benefit: This ensures that any ConditionPayload reaching the service layer (and thus the monitoring engine) is guaranteed to conform to its expected structure and data types. The monitoring engine can then confidently work with strongly typed objects instead of generic dictionaries.
- Enhance logic_tree Validation for Deep Structure:

- Action: Create a recursive Pydantic model for LogicNode that can validate nested structures. The logic_tree field in StrategyCreateSchema should then use this LogicNode model.
- Benefit: The monitoring engine will receive a logic_tree that is guaranteed to be structurally sound, allowing it to traverse and evaluate conditions without needing extensive defensive checks.
- Standardize Empty String/None for Optional Fields:

- Action: Decide whether "" or None is the canonical representation for "empty" for fields like description and condition.label .
- Action: Adjust frontend behavior to send the chosen representation (e.g., null instead of "" if None is preferred).
- Benefit: Reduces ambiguity and simplifies logic in the monitoring engine.
- Add Format Validation for NotificationCooldown.duration :

- Action: Implement a Pydantic validator in NotificationCooldown to ensure that if duration is provided as a string, it adheres to the expected "1h" or ISO 8601 format.
- Benefit: Prevents runtime parsing errors in the monitoring engine when it tries to interpret cooldown durations.
- Clarify and Implement required_data Population:

- Action: Determine if required_data should be populated by the frontend or derived by the backend service.
- If Frontend: Ensure the frontend sends this data based on the conditions.
- If Backend: Implement logic in the create_user_strategy service function to analyze the conditions and logic_tree and populate required_data with the necessary data sources (e.g., "BTC-1h-RSI", "ETH-daily-price").
- Benefit: The monitoring engine will have a clear, pre-computed list of data it needs to fetch for each strategy, optimizing its data retrieval process.

By implementing these changes, you shift the burden of validation and structural guarantees to the API boundary, allowing your monitoring engine to focus purely on its core logic: fetching data, evaluating conditions, and triggering actions, all with the confidence that the input data is well-formed and unambiguous.


Roles

- Clients
  - Speak to external data sources (Binance, Coingecko, Uniswap) using async HTTP/WebSocket.
  - Encapsulate each provider’s auth, endpoints, rate limits, payload shapes, and error semantics.
  - Return raw or minimally normalized data (e.g., prices, candles, indicator inputs) with consistent types.
- Data Prefetcher
  - Orchestrates data requests across many strategies to minimize upstream calls.
  - Deduplicates requests (e.g., 10 strategies needing BTC price → 1 fetch, fan-out to consumers).
  - Performs caching (via Redis) with consistent keys and TTLs; serves cache hits fast.
  - Normalizes outputs into a single “evaluation context” per strategy (e.g., {"prices": {...}, "klines": {...}} ).
Relationship

- The prefetcher depends on clients to retrieve fresh data when the cache doesn’t have it or is expired.
- Clients are leaf-level providers; the prefetcher is a coordination/caching layer that decides:
  - What to fetch (based on strategy assets and computed required_data ).
  - Where to fetch from (primary provider, then fallback providers).
  - When to serve cached results versus refreshing from a client.
- Evaluators consume the prefetcher’s outputs, not the clients directly. That keeps condition logic decoupled from provider-specific quirks.
Workflow

- Scheduler tick groups strategies by frequency and computes the union of required assets/timeframes.
- Prefetcher checks Redis for each item:
  - Cache hit → hydrate context from Redis.
  - Cache miss → call the appropriate client(s), normalize, write to Redis with TTL, and hydrate context.
- ConditionEvaluator runs against that context (e.g., price_alert uses context["prices"][asset] ).
- LogicTreeEvaluator reduces the condition results to a single boolean.
- TriggerHandler persists logs and updates counters when the tree evaluates to true.
Caching Strategy

- Keys: use predictable, hierarchical keys (e.g., prices:{ASSET} , klines:{ASSET}:{TF} , indicators:{ASSET}:{IND}:{TF} ).
- TTLs: align with schedule (shorter TTL for fast schedules like 1m ; longer TTL for 1h ).
- Invalidation: refresh on demand for critical paths (manual reload, upstream webhook, or when TTL elapses).
- Serialization: store compact, parseable values; avoid large snapshots in Redis.
Error Handling & Resilience

- Clients: implement retries (with jitter), exponential backoff, provider-specific error parsing, and rate-limit handling.
- Prefetcher: fall back across providers (primary → secondary → tertiary), and return partial contexts where possible.
- Observability: record metrics for cache hits/misses, fetch latency, provider errors, and batch durations.
Extending Each

- Clients
  - Add async implementations for Binance/Coingecko/Uniswap with a shared base.py interface ( get_price , get_klines , etc.).
  - Normalize output schemas (e.g., number types, timezones, symbol normalization).
  - Add per-provider rate-limiters and credential management.
- Data Prefetcher
  - Implement batch calls per provider, symbol remapping, and multi-asset requests.
  - Add a registry for “data requirements” (e.g., price, kline, indicator inputs) inferred from strategies.
  - Enrich cached data with timestamps/source metadata for traceability.
Scheduler Auto-Start

- Yes—enable auto-start at app startup behind a config flag (e.g., ENABLE_SCHEDULER=true ).
- Correct implementation
  - On startup: construct the scheduler; use short-lived DB sessions per tick (not one long-lived session).
  - On shutdown: stop the scheduler task cleanly; close DB/Redis connections.
  - Guardrails: catch exceptions per tick, don’t let one provider failure halt the loop, and mark problematic strategies error when evaluation is impossible.
  - Metrics/logging: instrument ticks, batch durations, triggers, cache hit rate, and errors for visibility.