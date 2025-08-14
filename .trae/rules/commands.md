.\spoon-env\Scripts\activate

pip install --upgrade fastmcp

python -m spoon_ai.agents.omnichain_synapse_agent

python -m spoon_ai.agents.omnichain_synapse_agent | Select-String -NotMatch "DEBUG"

python "spoon_ai\agents\run_omnichain_mcp_server.py"

python "spoon_ai\agents\run_agent_server.py"

pytest tests\test_strategy_manager.py

docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant