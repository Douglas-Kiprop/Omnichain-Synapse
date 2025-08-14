import pytest
import asyncio
from spoon_ai.strategy.strategy_manager import StrategyManager
from spoon_ai.schema import Strategy
from spoon_ai.agents.omnichain_synapse_agent import OmnichainSynapseAgent

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def strategy_manager():
    # Initialize StrategyManager for testing
    manager = StrategyManager()
    # Ensure a clean collection for each test
    max_retries = 5
    base_delay = 1
    for i in range(max_retries):
        try:
            if manager.client.collection_exists(collection_name=manager.collection_name):
                manager.client.delete_collection(collection_name=manager.collection_name)
            break
        except Exception as e:
            print(f"Error during strategy_manager setup cleanup: {e}")
            if i < max_retries - 1:
                delay = base_delay * (2 ** i)
                print(f"Retrying cleanup in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                raise

    manager._create_collection_if_not_exists()
    yield manager
    # Clean up after tests
    for i in range(max_retries):
        try:
            if manager.client.collection_exists(collection_name=manager.collection_name):
                manager.client.delete_collection(collection_name=manager.collection_name)
            break
        except Exception as e:
            print(f"Error during strategy_manager teardown cleanup: {e}")
            if i < max_retries - 1:
                delay = base_delay * (2 ** i)
                print(f"Retrying cleanup in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                raise

@pytest.fixture(scope="function")
async def omnichain_agent():
    agent = OmnichainSynapseAgent()
    # Ensure the agent's strategy manager has a clean collection
    max_retries = 5
    base_delay = 1
    for i in range(max_retries):
        try:
            if agent.strategy_manager.client.collection_exists(collection_name=agent.strategy_manager.collection_name):
                agent.strategy_manager.client.delete_collection(collection_name=agent.strategy_manager.collection_name)
            break
        except Exception as e:
            print(f"Error during omnichain_agent setup cleanup: {e}")
            if i < max_retries - 1:
                delay = base_delay * (2 ** i)
                print(f"Retrying cleanup in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                raise

    agent.strategy_manager._create_collection_if_not_exists()
    yield agent
    # Clean up after tests
    for i in range(max_retries):
        try:
            if agent.strategy_manager.client.collection_exists(collection_name=agent.strategy_manager.collection_name):
                agent.strategy_manager.client.delete_collection(collection_name=agent.strategy_manager.collection_name)
            break
        except Exception as e:
            print(f"Error during omnichain_agent teardown cleanup: {e}")
            if i < max_retries - 1:
                delay = base_delay * (2 ** i)
                print(f"Retrying cleanup in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                raise

@pytest.mark.asyncio
async def test_create_strategy(strategy_manager):
    strategy_data = {
        "name": "Test Strategy 1",
        "description": "A simple test strategy",
        "conditions": ["price > 100"],
        "actions": ["notify_telegram"]
    }
    strategy_obj = Strategy(**strategy_data)
    strategy = strategy_manager.create_strategy(strategy_obj) # Removed await
    assert strategy.name == "Test Strategy 1"
    assert strategy.id is not None

    retrieved_strategy = strategy_manager.get_strategy(strategy.id) # Removed await
    assert retrieved_strategy.name == "Test Strategy 1"

@pytest.mark.asyncio
async def test_get_strategy(strategy_manager):
    strategy_data = {
        "name": "Test Strategy 2",
        "description": "Another test strategy",
        "conditions": ["volume > 1000"],
        "actions": ["log_event"]
    }
    strategy_obj = Strategy(**strategy_data)
    created_strategy = strategy_manager.create_strategy(strategy_obj) # Removed await
    retrieved_strategy = strategy_manager.get_strategy(created_strategy.id) # Removed await
    assert retrieved_strategy.id == created_strategy.id
    assert retrieved_strategy.name == "Test Strategy 2"

@pytest.mark.asyncio
async def test_update_strategy(strategy_manager):
    strategy_data = {
        "name": "Test Strategy 3",
        "description": "Strategy to update",
        "conditions": ["price < 50"],
        "actions": ["send_email"]
    }
    strategy_obj = Strategy(**strategy_data)
    created_strategy = strategy_manager.create_strategy(strategy_obj) # Removed await
    
    # Create a new Strategy object with updates
    updated_strategy_data = created_strategy.model_dump()
    updated_strategy_data["description"] = "Updated description"
    updated_strategy_data["is_active"] = False
    updated_strategy_obj = Strategy(**updated_strategy_data)

    updated_strategy = strategy_manager.update_strategy(updated_strategy_obj) # Removed await
    assert updated_strategy.description == "Updated description"
    assert updated_strategy.is_active is False

    retrieved_strategy = strategy_manager.get_strategy(created_strategy.id) # Removed await
    assert retrieved_strategy.description == "Updated description"
    assert retrieved_strategy.is_active is False

@pytest.mark.asyncio
async def test_delete_strategy(strategy_manager):
    strategy_data = {
        "name": "Test Strategy 4",
        "description": "Strategy to delete",
        "conditions": ["time > 10pm"],
        "actions": ["do_nothing"]
    }
    strategy_obj = Strategy(**strategy_data)
    created_strategy = strategy_manager.create_strategy(strategy_obj) # Removed await
    strategy_manager.delete_strategy(created_strategy.id) # Removed await
    # The original test expected an exception, but get_strategy now returns None if not found
    retrieved_strategy = strategy_manager.get_strategy(created_strategy.id) # Removed await
    assert retrieved_strategy is None

@pytest.mark.asyncio
async def test_omnichain_agent_create_strategy(omnichain_agent):
    strategy_data = {
        "name": "Agent Created Strategy",
        "description": "Created via OmnichainSynapseAgent",
        "conditions": ["eth_price > 3000"],
        "actions": ["alert_user"]
    }
    # OmnichainSynapseAgent's create_strategy expects a dict, so no change here
    response = await omnichain_agent.create_strategy(strategy_data)
    assert response["status"] == "success"
    assert response["strategy"]["name"] == "Agent Created Strategy"

    retrieved_response = await omnichain_agent.get_strategy(response["strategy"]["id"])
    assert retrieved_response["status"] == "success"
    assert retrieved_response["strategy"]["name"] == "Agent Created Strategy"

@pytest.mark.asyncio
async def test_omnichain_agent_craft_strategy(omnichain_agent):
    strategy_data = {
        "name": "Crafted Strategy",
        "description": "Crafted via OmnichainSynapseAgent",
        "parameters": {"key": "value"},
        "conditions": ["btc_price < 20000"],
        "actions": ["buy_btc"]
    }
    # OmnichainSynapseAgent's _craft_strategy expects a dict, so no change here
    response = await omnichain_agent._craft_strategy(strategy_data)
    assert response["status"] == "success"
    assert response["strategy"]["name"] == "Crafted Strategy"

    # Test missing required field
    invalid_strategy_data = {
        "name": "Invalid Strategy",
        "description": "Missing parameters"
    }
    response_invalid = await omnichain_agent._craft_strategy(invalid_strategy_data)
    assert response_invalid["status"] == "error"
    assert "Missing required field: parameters" in response_invalid["message"]

@pytest.mark.asyncio
async def test_omnichain_agent_get_strategy(omnichain_agent):
    strategy_data = {
        "name": "Agent Get Strategy",
        "description": "Get via OmnichainSynapseAgent",
        "conditions": ["sol_price > 100"],
        "actions": ["sell_sol"]
    }
    created_response = await omnichain_agent.create_strategy(strategy_data)
    strategy_id = created_response["strategy"]["id"]

    retrieved_response = await omnichain_agent.get_strategy(strategy_id)
    assert retrieved_response["status"] == "success"
    assert retrieved_response["strategy"]["id"] == strategy_id

@pytest.mark.asyncio
async def test_omnichain_agent_update_strategy(omnichain_agent):
    strategy_data = {
        "name": "Agent Update Strategy",
        "description": "Update via OmnichainSynapseAgent",
        "conditions": ["ada_price < 0.5"],
        "actions": ["buy_ada"]
    }
    created_response = await omnichain_agent.create_strategy(strategy_data)
    strategy_id = created_response["strategy"]["id"]

    updates = {"description": "Updated by agent", "is_active": False}
    # OmnichainSynapseAgent's update_strategy expects a dict for updates, so no change here
    updated_response = await omnichain_agent.update_strategy(strategy_id, updates)
    assert updated_response["status"] == "success"
    assert updated_response["strategy"]["description"] == "Updated by agent"
    assert updated_response["strategy"]["is_active"] is False

@pytest.mark.asyncio
async def test_omnichain_agent_delete_strategy(omnichain_agent):
    strategy_data = {
        "name": "Agent Delete Strategy",
        "description": "Delete via OmnichainSynapseAgent",
        "conditions": ["dot_price > 10"],
        "actions": ["sell_dot"]
    }
    created_response = await omnichain_agent.create_strategy(strategy_data)
    strategy_id = created_response["strategy"]["id"]

    delete_response = await omnichain_agent.delete_strategy(strategy_id)
    assert delete_response["status"] == "success"

    get_response = await omnichain_agent.get_strategy(strategy_id)
    assert get_response["status"] == "error"
    assert "not found" in get_response["message"]