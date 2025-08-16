start server: python -m spoon_ai.agents.run_agent_server


start qdrant: docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant



run agent: python -m spoon_ai.agents.omnichain_synapse_agent
