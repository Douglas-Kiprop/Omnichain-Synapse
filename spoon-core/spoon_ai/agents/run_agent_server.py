# run_agent_server.py - PRODUCTION READY
import asyncio
import logging
import uvicorn
import traceback
from typing import Optional, Any 
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from contextvars import Token # Import Token for context management

from spoon_ai.agents.omnichain_synapse_agent import OmnichainSynapseAgent
# Import the context setter and the exception for txn_hash
from spoon_ai.x402.context import set_txn_hash, reset_txn_hash
from spoon_ai.tools.premium_chainbase_tool import PaymentRequiredException
# Import verification logic (moved from endpoint)
from spoon_ai.x402.verifier import verify_payment

# --- NEW IMPORTS for Authentication Context ---
from spoon_ai.utils.auth import extract_privy_token # <--- Task 1.1: NEW UTILITY
from spoon_ai.x402.context import tool_context # <--- Task 1.2: CONTEXT UTILITY (FIXED IMPORT)
# ---------------------------------------------

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Models ---
class ChatRequest(BaseModel):
    message: str
    txn_hash: Optional[str] = None

class ChatResponse(BaseModel):
    response: str

# --- App Setup ---
app = FastAPI(
    title="OmnichainSynapseAgent Server",
    description="API server for chatting with OmnichainSynapseAgent with x402 payment support",
    version="1.0.0",
)

# --- Middleware/Exception Handlers ---

# This handles the 402 logic GLOBALLY. 
# Anytime a tool raises PaymentRequiredException, this runs.
@app.exception_handler(PaymentRequiredException)
async def payment_required_handler(request: Request, exc: PaymentRequiredException):
    logger.info(f"💳 Payment required intercepted: {exc.payment_details}")
    
    # This JSONResponse returns the 402 status code and the payment info.
    return JSONResponse(
        status_code=402,
        content={
            "error": "payment_required",
            "payment": exc.payment_details,
            "message": f"Payment required to access {exc.payment_details.get('tool_name', 'premium tool')}"
        }
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
agent: Optional[OmnichainSynapseAgent] = None

@app.on_event("startup")
async def startup_event():
    global agent
    logger.info("🚀 Starting OmnichainSynapseAgent Server...")
    try:
        agent = OmnichainSynapseAgent()
        logger.info("✅ Agent initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize agent: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    global agent
    agent = None

# --- Endpoints ---

@app.get("/")
async def root():
    return {"status": "online", "service": "OmnichainSynapseAgent"}

@app.get("/health")
async def health_check():
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return {"status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: Request, # <-- Need to inject Request to read headers
    chat_request: ChatRequest # <-- Rename to avoid conflict with `Request`
):
    """
    Main chat endpoint. 
    Sets the transaction context AND the user authentication context, runs the agent.
    If the agent hits a premium tool without valid payment, it bubbles PaymentRequiredException.
    """
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    # --- CONTEXT MANAGEMENT ---
    
    # 1. AUTH CONTEXT: Extract the user's Privy token from the header
    privy_token = extract_privy_token(request)
    
    # 2. PAYMENT CONTEXT: Set the txn_hash context
    txn_token: Token = set_txn_hash(chat_request.txn_hash)
    
    # 3. COMBINED CONTEXT: Manually manage the tool_context for the Privy Token
    # We use a combined dictionary to hold both context pieces for the run
    current_context = tool_context.get()
    
    if privy_token:
        current_context["privy_token"] = privy_token
        logger.info("🔑 Injected Privy Token into Agent context for authentication.")
    
    context_token: Token = tool_context.set(current_context)
    
    try:
        if chat_request.txn_hash:
            logger.info(f"💳 Context set with hash: {chat_request.txn_hash}")
        
        # 4. RUN AGENT: This line will use the context variables
        response = await agent.process(input_text=chat_request.message)
        
        return ChatResponse(response=response)
        
    except PaymentRequiredException:
        # Re-raise it so the @app.exception_handler can catch it for 402 response
        raise 

    except Exception as e:
        logger.error(f"❌ Error processing request: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # 5. CLEANUP: Always reset ALL contexts to prevent leaks between requests
        reset_txn_hash(txn_token)
        tool_context.reset(context_token) # Reset the combined context

@app.post("/verify-payment")
async def verify_payment_endpoint(txn_hash: str):
    """Check payment status directly"""
    try:
        is_valid = verify_payment(txn_hash)
        return {"valid": is_valid, "txn_hash": txn_hash}
    except Exception as e:
        logger.error(f"Error verifying payment: {e}")
        return {"valid": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="info")