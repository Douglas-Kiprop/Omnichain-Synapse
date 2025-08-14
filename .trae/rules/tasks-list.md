# Task List: Transforming OmnichainSynapseAgent into a World-Class Data Analyst Agent

This task list outlines the steps to enhance the OmnichainSynapseAgent into a sophisticated Data Analyst Agent with custom strategy execution, user-specific storage, real-time monitoring using the monitoring API, and an intuitive UI, integrating StrategyBuilder and routes.py. Mark each task as `[x]` when completed.

## 1. [ ] Setup Environment and Dependencies
   - [ ] Install required Python packages
     - [ ] Add `chromadb` (optional, for local testing), `qdrant-client`, and `fastapi` to `requirements.txt`
     - [ ] Run `pip install -r requirements.txt`
   - [ ] Configure environment variables
     - [ ] Add `OPENAI_API_KEY` to `.env` for embeddings
     - [ ] Add `TELEGRAM_CHAT_ID` and `TELEGRAM_BOT_TOKEN` to `.env`
     - [ ] Add `USER_ID` (e.g., from authentication) to `.env` for testing
   - [ ] Verify setup
     - [ ] Test QdrantClient initialization (primary focus)
     - [ ] Test ChromaClient initialization (optional, for local testing)
     - [ ] Test MonitoringTaskManager via `routes.py` endpoints

## 2. [ ] Enhance OmnichainSynapseAgent with Strategy Logic
   - [ ] Update `omnichain_synapse_agent.py`
     - [ ] Import necessary modules (`QdrantClient`, `ToolCallAgent`, `requests` for API calls)
     - [ ] Initialize `ToolCallAgent` and `QdrantClient` in `__init__`
     - [ ] Implement `_craft_strategy` method with `user_id` and UI-compatible format, ensuring a structured (e.g., JSON schema) approach for conditions to ensure safety and parseability.
     - [ ] Implement `load_strategies` method with `user_id` filtering and UI structure support
     - [ ] Implement `notify_telegram` method using `TelegramClient`
     - [ ] Update `process` method to handle strategy creation and modification, clearly differentiating between general chat commands and strategy management.
     - [ ] Add method to map `Strategy` to `MonitoringTaskCreate` and call `/monitoring/tasks`
     - [ ] Add method to monitor task status via `/monitoring/tasks/{task_id}`
   - [ ] Test strategy creation
     - [ ] Run agent with input "Create a strategy for NEO > $10"
     - [ ] Verify strategy is stored in Qdrant and a monitoring task is created
   - [ ] Test strategy loading and modification
     - [ ] Call `load_strategies` with different `user_id` values
     - [ ] Confirm only user-specific strategies are returned and modifiable
     - [ ] Test updating a strategy’s `status` via API

## 3. [ ] Configure Monitoring System
   - [ ] Integrate `routes.py` in `spoon_ai/monitoring/api`
     - [ ] Verify `MonitoringTaskManager` handles strategy-based tasks
     - [ ] Map `Strategy` conditions to `MonitoringTaskCreate` (e.g., `metric`, `threshold`)
     - [ ] Test creating tasks with diverse conditions (e.g., price, volume)
   - [ ] Update `tasks.py` (optional)
     - [ ] Align `monitor_strategies` with `MonitoringTaskManager` if needed
     - [ ] Remove redundant scheduling logic
   - [ ] Test monitoring
     - [ ] Activate a strategy and simulate metric data
     - [ ] Verify Telegram notification triggers via API
   - [ ] Handle edge cases
     - [ ] Test with unsupported metrics
     - [ ] Test with expired tasks

## 4. [ ] Enhance Telegram Notifications
   - [ ] Update `telegram.py` in `spoon_ai/social_media`
     - [ ] Ensure `send_proactive_message` uses `os.getenv("TELEGRAM_CHAT_ID")`
     - [ ] Verify compatibility with `OmnichainSynapseAgent` and API triggers
   - [ ] Test notifications
     - [ ] Trigger a task condition via `/monitoring/tasks/{task_id}/test`
     - [ ] Confirm message is sent to the correct chat ID
   - [ ] Add error handling
     - [ ] Log failures if Telegram API is unavailable
     - [ ] Provide fallback (e.g., console log)

## 5. [ ] Update UI Components
   - [ ] Modify `appsidebar.tsx`
     - [ ] Add `/strategies` NavLink below `/strategy-builder`
     - [ ] Import `List` icon from `lucide-react`
     - [ ] Test navigation to `/strategies` route
   - [ ] Enhance `chatpanel.tsx`
     - [ ] Add `strategies` state and fetch from `/api/strategies`
     - [ ] Update `handleApplyStrategy` to activate strategies from `StrategyBuilder`
     - [ ] Integrate with authentication token (e.g., from `useAuth` context)
     - [ ] Test strategy application and UI updates
   - [ ] Integrate `StrategyBuilder`
     - [ ] Ensure `onStrategyChange` syncs with `chatpanel.tsx`
     - [ ] Enhance `saveStrategy` to POST to `/api/strategies` with `user_id`
     - [ ] Test saving a strategy and verifying in `/strategies`
   - [ ] Create `/strategies` route component (new file)
     - [ ] Design a table to display `user_id`, `name`, `conditions`, `status`
     - [ ] Add buttons to pause/resume/extend tasks via `/monitoring/tasks/{task_id}`
     - [ ] Fetch data from `/api/strategies` and sync with `/monitoring/tasks`
     - [ ] Allow agent to modify strategies (e.g., update `status`)
     - [ ] Test route functionality

## 6. [ ] Update API Endpoints
   - [ ] Modify `run_agent_server.py`
     - [ ] Add `OAuth2PasswordBearer` for authentication
     - [ ] Implement `/api/strategies` POST endpoint to save `StrategyBuilder` output and create monitoring tasks
     - [ ] Implement `/api/strategies` GET endpoint for strategy listing
     - [ ] Add PUT endpoint to modify strategies and sync with `/monitoring/tasks`
     - [ ] Pass `user_id` from token to `process` and `load_strategies`
   - [ ] Test API endpoints
     - [ ] Send POST request with a `StrategyBuilder` strategy
     - [ ] Send GET request with valid token
     - [ ] Send PUT request to update a strategy
     - [ ] Verify responses are user-specific and tasks are created
   - [ ] Secure endpoints
     - [ ] Add JWT validation (e.g., using `pyjwt`)
     - [ ] Handle unauthorized access with 401 errors

## 7. [ ] Test End-to-End Workflow
   - [ ] Simulate multi-user scenario
     - [ ] Create strategies for two `user_id` values via `StrategyBuilder`
     - [ ] Verify isolation in UI and API
   - [ ] Test real-time monitoring
     - [ ] Activate a strategy with conditions and update metric data
     - [ ] Confirm notification delivery via `/monitoring/tasks`
   - [ ] Validate UI integration
     - [ ] Build a strategy in `StrategyBuilder`, save it, and view in `/strategies`
     - [ ] Apply a strategy from `chatpanel.tsx`
     - [ ] Pause/resume/extend a task in `/strategies`
   - [ ] Debug issues
     - [ ] Check logs for errors
     - [ ] Resolve any tool or API failures

## 8. [ ] Optimize and Future-Proof
   - [ ] Improve performance
     - [ ] Add caching to `load_strategies` (e.g., LRU cache)
     - [ ] Optimize task check intervals in `MonitoringTaskManager`
   - [ ] Plan for scalability
     - [ ] Ensure `QdrantClient` is fully integrated and tested with sample data as the primary vector database.
   - [ ] Add documentation
     - [ ] Update `README.md` with new features
     - [ ] Add comments in code for key changes

## 9. [ ] Deploy and Monitor
   - [ ] Deploy to test environment
     - [ ] Run on `127.0.0.1:8765` with Docker (if applicable)
     - [ ] Verify all endpoints and UI
   - [ ] Monitor performance
     - [ ] Check CPU/memory usage
     - [ ] Log task execution times
   - [ ] Gather feedback
     - [ ] Test with sample users
     - [ ] Refine based on input

---

### Notes
- **Dependencies**: Ensure `qdrant-client`, `fastapi`, and `pyjwt` are installed. `chromadb` is optional for local testing. Configure `.env` with API keys and tokens.
- **Authentication**: Placeholder `user_id` from token; implement a real auth system (e.g., OAuth2) for production.
- **Scalability Path**: `QdrantClient` is the primary vector database for scalability. Ensure the `StrategyManager` is abstracted to allow for potential future changes.
- **Testing**: Use a separate `user_id` for each test to verify isolation.
- **StrategyBuilder Integration**: Ensure `conditions` are mappable to `MonitoringTaskCreate` using a structured format (e.g., JSON schema); add new tools if needed.
- **Monitoring API**: Use `/monitoring/tasks` for task management; align with `Strategy` structure.

### Implementation Phasing Guidance
To ensure a smooth and secure development process, adhere to the following phased implementation approach:

1.  **Prioritize Core Backend Logic (Phases 1 & 2):**
    *   Define the `Strategy` Data Model precisely using Pydantic, with a structured approach for conditions (e.g., JSON schema) to ensure safety and parseability.
    *   Implement `StrategyManager` focusing on CRUD operations for strategies, integrating with Qdrant.
    *   Enhance `OmnichainSynapseAgent` to correctly `_craft_strategy`, `load_strategies`, and interact with the `StrategyManager` and the monitoring API.
    *   Ensure secure condition parsing and evaluation, avoiding `eval()` at all costs.

2.  **Build Out API Endpoints (Phase 6):**
    *   Once the core agent logic and strategy management are stable, expose these functionalities via FastAPI endpoints in `run_agent_server.py`. This allows for testing the backend independently of the UI.
    *   Implement authentication early, even if simplified for development, to ensure the `user_id` flow is correct.

3.  **Integrate Monitoring & Notifications (Phases 3 & 4):**
    *   Ensure the mapping from your `Strategy` model to `MonitoringTaskCreate` is seamless. Test this integration thoroughly.
    *   Refine Telegram notifications to be informative and reliable.

4.  **Develop UI Components (Phase 5):**
    *   This can run somewhat in parallel with backend development, but it's best to have stable API endpoints to consume. Focus on a user-friendly experience for defining and managing strategies.

5.  **Continuous Testing (Phase 7):**
    *   Integrate unit and integration tests from the very beginning. Don't wait until the end. This will catch issues early and ensure stability.