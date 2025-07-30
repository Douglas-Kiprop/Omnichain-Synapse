.\spoon-env\Scripts\activate

python -m spoon_ai.agents.omnichain_synapse_agent

python -m spoon_ai.agents.omnichain_synapse_agent | Select-String -NotMatch "DEBUG"