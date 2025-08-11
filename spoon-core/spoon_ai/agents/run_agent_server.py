import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
import uvicorn
from spoon_ai.agents.omnichain_synapse_agent import OmnichainSynapseAgent

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
    allow_origins=["http://localhost:8080"],  # Your frontend origin
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

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")