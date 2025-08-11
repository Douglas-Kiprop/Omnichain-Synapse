# task-list.md

## Project: Omnichain Synapse - Onchain Data Analyst AI Agent

**Objective**: Build a SpoonOS-based AI agent on Trae AI for the SpoonOS dev call hackathon, acting as an onchain data analyst that processes blockchain data using spoon-toolkit’s chainbase_tool.py and coingecko_tool.py, executes user-defined strategies, and presents insights via an interactive React dashboard with Chart.js charts, D3.js diagrams, and a React Chat Widget, incorporating sentiment analysis and DeFi yield optimization, following spoon-core README.md and spoon-examples (wallet_tracker.py, defi_yield_analyzer.py).

**Tech Stack**:
- SpoonOS (ReAct Intelligent Agent, Model Context Protocol (MCP), BeVec, Spoon Toolkit with chainbase_tool.py, coingecko_tool.py)
- Trae AI for agent development and deployment
- APIs: Chainbase, CoinGecko (MVP); LunarCrush (secondary, if supported)
- Python libraries: pandas, numpy, requests, websocket-client, python-dotenv, pytest
- UI: React, Chart.js, D3.js, React Chat Widget
- Data storage: SpoonOS BeVec vector database

**Estimated Duration**: 10 weeks for MVP (hackathon-ready)

---

## Phase 1: Setup and Environment Configuration
**Goal**: Clone spoon-core, set up Trae AI and SpoonOS environment, configure API keys, following spoon-core README.md.
**Duration**: 1 week

- [ ] **Task 1.1: Clone spoon-core and Set up Environment**
  - Clone repository: `git clone https://github.com/XSpoonAi/spoon-core.git; cd spoon-core` (spoon-core README.md).
  - Create virtual environment: `python -m venv spoon-env; source spoon-env/bin/activate` (macOS/Linux).
  - Verify Python 3.10+: `python --version`.
  - *Estimated Time*: 2 hours
  - *Dependencies*: Git, Python 3.10+.

- [ ] **Task 1.2: Install SpoonOS and Toolkit Dependencies**
  - Install dependencies: `pip install -r requirements.txt` (includes spoonos, chainbase_tool.py, coingecko_tool.py, requests, websocket-client).
  - Verify installation: `python -c "import spoonos; print(spoonos.__version__)"`.
  - *Estimated Time*: 2 hours
  - *Dependencies*: Virtual environment.

- [ ] **Task 1.3: Configure Trae AI Integration**
  - Initialize Trae AI project: `trae init omnichain-synapse` (https://docs.trae.ai/).
  - Copy `spoon-core` contents to Trae AI project directory.
  - Test Trae AI CLI: `trae --version`.
  - *Estimated Time*: 3 hours
  - *Dependencies*: Trae AI CLI/IDE.

- [ ] **Task 1.4: Obtain and Configure API Keys**
  - Sign up for Chainbase API (https://www.chainbase.com/), set `CHAINBASE_API_KEY` in `.env` (spoon-core/docs/setup.md).
  - Get CoinGecko API key (https://www.coingecko.com/en/api), set `COINGECKO_API_KEY`.
  - Check LunarCrush API support via SpoonOS Discord (https://discord.gg/G6y3ZCFK4h); set `LUNARCRUSH_API_KEY` if supported, else plan CoinGecko fallback.
  - *Estimated Time*: 3 hours
  - *Dependencies*: Internet access, API accounts.

- [ ] **Task 1.5: Install Additional Python Libraries**
  - Install: `pip install pandas numpy python-dotenv pytest`.
  - Test imports: `python -c "import pandas, numpy, pytest"`.
  - *Estimated Time*: 2 hours
  - *Dependencies*: Virtual environment.

---

## Phase 2: Build Core Agent Functionality
**Goal**: Develop ReAct agent with MCP-integrated chainbase_tool.py and coingecko_tool.py, following wallet_tracker.py and defi_yield_analyzer.py from spoon-examples.
**Duration**: 3.5 weeks

- [ ] **Task 2.1: Initialize ReAct Agent**
  - Create `agent.py` in `spoon-core/src` based on spoon-core/src/spoon_core/agent.py.
  - Configure ReAct loop: `agent.process(input)` for parsing, reasoning, tool calls, output.
  - Set up DeepSeek LLM for natural language parsing (spoon-core README.md).
  - Test query: “Get $pump price” using coingecko_tool.py (inspired by spoon-examples/examples/price_alert_agent.py).
  - *Estimated Time*: 6 hours
  - *Dependencies*: SpoonOS, Trae AI.

- [ ] **Task 2.2: Register Toolkit Tools with MCP**
  - Register `chainbase_tool.py`: `mcp.register_tool("chainbase_wallet", ChainbaseTool())` (spoon-core/src/spoon_core/mcp.py).
  - Register `coingecko_tool.py`: `mcp.register_tool("coingecko_price", CoinGeckoTool())`.
  - Test tools: Query $pump wallet activity (Chainbase) and price (CoinGecko).
  - *Estimated Time*: 6 hours
  - *Dependencies*: SpoonOS toolkit, API keys.

- [ ] **Task 2.3: Implement Data Processing Logic**
  - Build PnL calculator (based on spoon-examples/examples/wallet_tracker.py):
    - Use `chainbase_tool.py` to fetch transactions.
    - Calculate: `pnl = (sell_price - buy_price) * volume - gas_fees` with pandas.
  - Filter top 5 wallets by PnL, exclude bots (trades > 100/day).
  - Analyze holding times, profit-taking with pandas/numpy.
  - *Estimated Time*: 10 hours
  - *Dependencies*: chainbase_tool.py, pandas.

- [ ] **Task 2.4: Enable Strategy Parsing and Execution**
  - Implement parsing (based on spoon-examples/examples/price_alert_agent.py):
    - Natural language: “Alert when top wallets buy $pump > $10,000” → JSON: `{ "token": "pump", "condition": "buy_volume > 10000", "action": "alert" }`.
    - Support JSON inputs.
  - Create rule engine to evaluate conditions (e.g., `if buy_volume > threshold`).
  - Test strategies: “Follow top 5 wallets,” “Inverse worst traders.”
  - *Estimated Time*: 14 hours
  - *Dependencies*: ReAct agent, LLM.

- [ ] **Task 2.5: Implement Novel Use Cases**
  - DeFi Yield Optimization (based on spoon-examples/examples/defi_yield_analyzer.py):
    - Query `chainbase_tool.py` for DeFi data (e.g., Aave APY).
    - Recommend: “Stake in Protocol X for 12% APY.”
    - Test with Uniswap/Aave pools.
  - Sentiment Analysis:
    - Confirm LunarCrush support via Discord; if supported, create `lunarcrush_tool.py` (spoon-toolkit/src/tools/template_tool.py).
    - If unsupported, use CoinGecko sentiment data.
    - Correlate sentiment with wallet buys using pandas.
    - Output: “Bullish sentiment + buys → buy signal.”
  - *Estimated Time*: 12 hours
  - *Dependencies*: chainbase_tool.py, LunarCrush API (optional), pandas.

- [ ] **Task 2.6: Configure BeVec for Data Storage**
  - Initialize BeVec (spoon-core/src/spoon_core/bevec.py).
  - Cache $pump prices (coingecko_tool.py), transactions (chainbase_tool.py), sentiment data.
  - Implement retrieval: `bevec.query({"token": "pump"})`.
  - Test caching/retrieval.
  - *Estimated Time*: 6 hours
  - *Dependencies*: SpoonOS SDK, BeVec.

---

## Phase 3: Develop Interactive Dashboard UI
**Goal**: Build React dashboard inspired by spoon-examples/examples/ui_example.py, using Chart.js, D3.js, and React Chat Widget.
**Duration**: 3 weeks

- [ ] **Task 3.1: Set up React UI Framework**
  - Initialize: `npx create-react-app omnichain-synapse-ui`.
  - Install: `npm install chart.js d3 react-chat-widget`.
  - *Estimated Time*: 4 hours
  - *Dependencies*: Node.js, npm.

- [ ] **Task 3.2: Design Dashboard Layout**
  - Create components (inspired by ui_example.py):
    - Header: Branding, navigation (Home, Strategy Builder, History).
    - Main Panel:
      - Visualization Area (60%): Charts, graphs.
      - Strategy Input Area (20%): Chat, form.
      - Results Summary (20%): Text insights, buttons.
    - Sidebar: Saved strategies, query history, API status.
  - Use CSS Grid for responsive layout.
  - *Estimated Time*: 8 hours
  - *Dependencies*: React setup.

- [ ] **Task 3.3: Implement Data Visualizations**
  - Create Chart.js charts:
    - Line chart: $pump prices (coingecko_tool.py).
    - Bar chart: Wallet PnL (chainbase_tool.py).
    - Line chart: Sentiment scores (LunarCrush/CoinGecko).
  - Create D3.js network graph for wallet interactions.
  - Add interactivity: Zoom, filters (1h/24h/7d).
  - *Estimated Time*: 14 hours
  - *Dependencies*: Chart.js, D3.js, API data.

- [ ] **Task 3.4: Integrate Chat Interface**
  - Embed React Chat Widget for queries (e.g., “Show $pump top traders”).
  - Connect to agent via WebSocket (spoon-core/src/spoon_core/mcp.py).
  - Display responses in chat and visualization areas.
  - Support follow-ups with SpoonOS session state.
  - *Estimated Time*: 8 hours
  - *Dependencies*: React Chat Widget, agent API.

- [ ] **Task 3.5: Build Strategy Input Form**
  - Create form: Dropdowns for token, condition (e.g., “buy_volume > 10000”), action.
  - Parse into JSON for agent.
  - Add save/export buttons.
  - *Estimated Time*: 6 hours
  - *Dependencies*: React, agent API.

- [ ] **Task 3.6: Connect UI to Agent**
  - Set up WebSocket server in Trae AI for agent-UI communication.
  - Define JSON schema: `{ "token": "pump", "insights": { "top_wallets": [{ "address": "0x123", "pnl": 15000 }], "sentiment": "bullish" } }`.
  - Test: Input strategy → agent processes → UI updates.
  - *Estimated Time*: 8 hours
  - *Dependencies*: Agent, UI components.

---

## Phase 4: Testing and Refinement
**Goal**: Test agent and UI using spoon-examples/tests/test_examples.py, refine for accuracy.
**Duration**: 1 week

- [ ] **Task 4.1: Test Agent Functionality**
  - Write pytest tests (based on spoon-examples/tests/test_examples.py) for chainbase_tool.py, coingecko_tool.py.
  - Validate PnL, bot filtering, sentiment correlation, DeFi yield suggestions.
  - Test strategy: “Alert when top wallets buy $pump > $5,000 and sentiment is bullish.”
  - *Estimated Time*: 8 hours
  - *Dependencies*: Agent tools, pytest.

- [ ] **Task 4.2: Test UI Responsiveness**
  - Test dashboard on desktop/mobile.
  - Verify real-time chart updates (WebSocket).
  - Check chat/form error handling (e.g., CoinGecko rate limits).
  - *Estimated Time*: 6 hours
  - *Dependencies*: Dashboard UI.

- [ ] **Task 4.3: Refine Based on Feedback**
  - Share on SpoonOS Discord (https://discord.gg/G6y3ZCFK4h).
  - Fix bugs (e.g., API errors, UI glitches).
  - Optimize BeVec caching.
  - *Estimated Time*: 6 hours
  - *Dependencies*: Community access, test results.

---

## Phase 5: Deployment and Hackathon Prep
**Goal**: Deploy on Trae AI, prepare demo for SpoonOS dev call (https://github.com/XSpoonAi/spoon-devcall-s1).
**Duration**: 1 week

- [ ] **Task 5.1: Deploy Agent and UI**
  - Deploy agent on Trae AI cloud (https://docs.trae.ai/).
  - Host UI on Vercel: `vercel deploy`.
  - Verify API/BeVec connectivity.
  - *Estimated Time*: 5 hours
  - *Dependencies*: Trae AI account, UI build.

- [ ] **Task 5.2: Prepare Hackathon Demo**
  - Create demo script: Show $pump signals, sentiment analysis, DeFi yield optimization.
  - Record 5-minute video (spoon-devcall-s1 guidelines).
  - Prepare slides: Problem, solution, SpoonOS integration.
  - *Estimated Time*: 8 hours
  - *Dependencies*: Deployed agent/UI.

- [ ] **Task 5.3: Submit to SpoonOS Dev Call**
  - Create GitHub repository with README, code, tests.
  - Submit proposal/demo: https://github.com/XSpoonAi/spoon-devcall-s1.
  - Share on Discord for $2m ecosystem fund visibility (https://cryptonews.net/news/finance/30828126/).
  - *Estimated Time*: 3 hours
  - *Dependencies*: Demo, GitHub account.

---

## Notes
- **Total Estimated Time**: ~116 hours (~10 weeks part-time).
- **Dependencies**: Trae AI, SpoonOS, API keys, GitHub, Discord.
- **Risks**:
  - CoinGecko rate limits (30 calls/min): Cache in BeVec.
  - LunarCrush support: Confirm via Discord; fallback to CoinGecko.
  - SpoonOS newness: Follow wallet_tracker.py, defi_yield_analyzer.py.
- **Success Criteria**: Agent executes strategies using provided tools, supports DeFi/sentiment use cases, UI displays real-time insights, demo aligns with dev call goals.



Implement orderbooks - where have people placed their stop loss so you dont  put it there 

