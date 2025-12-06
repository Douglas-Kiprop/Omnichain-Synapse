.\spoon-env\Scripts\activate

pip install --upgrade fastmcp

python -m spoon_ai.agents.omnichain_synapse_agent

python -m spoon_ai.agents.omnichain_synapse_agent | Select-String -NotMatch "DEBUG"

python "spoon_ai\agents\run_omnichain_mcp_server.py"

python "spoon_ai\agents\run_agent_server.py"

pytest tests\test_strategy_manager.py

docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant






SYNAPSE BACKEND

.\.venv\Scripts\Activate.ps1

python run_synapse.py
uvicorn app:app --reload --host 0.0.0.0 --port 8000


MONITORING SERVICE

.\venv\Scripts\activate

python run_app.py
uvicorn app:app --host 0.0.0.0 --port 9000

pytest tests/integration/