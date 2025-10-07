import asyncio
import logging
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
import uvicorn
from spoon_ai.agents.omnichain_synapse_agent import OmnichainSynapseAgent
from spoon_ai.schema import Strategy

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str

app = FastAPI(
    title="OmnichainSynapseAgent Server",
    description="API server for chatting with OmnichainSynapseAgent",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "https://synapse-ui.vercel.app"],  # Your frontend origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, OPTIONS, etc.
    allow_headers=["*"],  # Allows Content-Type, etc.
)

# Initialize the agent once at startup
agent: OmnichainSynapseAgent = None

@app.on_event("startup")
async def startup_event():
    global agent
    logger.info("Initializing OmnichainSynapseAgent...")
    agent = OmnichainSynapseAgent()
    logger.info("Agent initialized successfully.")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Placeholder for user authentication (replace with actual token validation)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # In a real application, you would decode the token and validate it
    # For now, we'll just return a dummy user_id
    # You might want to implement a proper authentication service here
    # For example, if using JWT, you would decode and verify the token
    # try:
    #     payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    #     user_id: str = payload.get("sub")
    #     if user_id is None:
    #         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    # except JWTError:
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    
    # For demonstration, assuming a fixed user_id or extracting from a simple token
    if token:
        return "test_user_id" # Replace with actual user ID extraction
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.post("/chat")
async def chat_with_agent(request: ChatRequest):
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    try:
        response = await agent.process(request.message)
        return JSONResponse({"response": response})
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategies", response_model=dict)
async def create_strategy_endpoint(
    strategy: Strategy,
    current_user_id: str = Depends(get_current_user)
):
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    try:
        strategy.owner_id = current_user_id
        # agent.create_strategy returns a dictionary: {'status': 'success', 'strategy': Strategy_object}
        response_from_agent = await agent.create_strategy(strategy.model_dump())
        
        # Ensure the returned dictionary is JSON serializable
        # The nested Strategy object is already a JSON-serializable dictionary from agent.create_strategy.
        # This 'if' block is no longer necessary as the data is already in the correct format.
        # if response_from_agent.get("status") == "success" and "strategy" in response_from_agent:
        #     response_from_agent["strategy"] = response_from_agent["strategy"].model_dump(mode='json')
        
        return JSONResponse(response_from_agent)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/strategies", response_model=dict)
async def get_all_strategies_endpoint(current_user: str = Depends(get_current_user)):
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    try:
        # Pass the user_id to retrieve strategies specific to the current user
        response = await agent.get_strategy(strategy_id=None, user_id=current_user) # Assuming get_strategy can return all if ID is None
        if response.get("status") == "success":
            return JSONResponse(response)
        else:
            raise HTTPException(status_code=404, detail=response.get("message", "Strategies not found"))
    except Exception as e:
        logger.error(f"Error retrieving strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategies/{strategy_id}", response_model=dict)
async def get_strategy_by_id_endpoint(strategy_id: str, current_user: str = Depends(get_current_user)):
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    try:
        response = await agent.get_strategy(strategy_id=strategy_id, user_id=current_user)
        if response.get("status") == "success":
            return JSONResponse(response)
        else:
            raise HTTPException(status_code=404, detail=response.get("message", "Strategy not found"))
    except Exception as e:
        logger.error(f"Error retrieving strategy {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/strategies/{strategy_id}", response_model=dict)
async def update_strategy_endpoint(strategy_id: str, strategy: Strategy, current_user: str = Depends(get_current_user)):
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    try:
        response = await agent.update_strategy(strategy_id=strategy_id, updated_data=strategy.model_dump(), user_id=current_user)
        if response.get("status") == "success":
            return JSONResponse(response)
        else:
            raise HTTPException(status_code=400, detail=response.get("message", "Failed to update strategy"))
    except Exception as e:
        logger.error(f"Error updating strategy {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/strategies/{strategy_id}", response_model=dict)
async def delete_strategy_endpoint(strategy_id: str, current_user: str = Depends(get_current_user)):
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    try:
        response = await agent.delete_strategy(strategy_id=strategy_id, user_id=current_user)
        if response.get("status") == "success":
            return JSONResponse(response)
        else:
            raise HTTPException(status_code=404, detail=response.get("message", "Failed to delete strategy"))
    except Exception as e:
        logger.error(f"Error deleting strategy {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="info")
