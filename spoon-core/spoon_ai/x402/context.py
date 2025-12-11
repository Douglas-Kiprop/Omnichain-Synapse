# spoon-core/spoon_ai/x402/context.py (CONSOLIDATED & FIXED)

from contextvars import ContextVar, Token
from typing import Optional, Dict, Any

# --- 1. SHARED CONTEXT VARIABLE (The fix for the ImportError) ---
# This single dictionary holds all request-specific data (txn_hash, privy_token)
# It is exported so run_agent_server.py can set/reset it.
tool_context: ContextVar[Dict[str, Any]] = ContextVar("tool_context", default={})

# --- 2. x402 Payment Context Functions (Rewritten to use tool_context) ---

def get_txn_hash() -> Optional[str]:
    """Retrieves the transaction hash from the current context."""
    context = tool_context.get()
    return context.get("txn_hash")

def set_txn_hash(txn_hash: Optional[str]) -> Token:
    """
    Sets the transaction hash in the current context, returning the token 
    to be used for cleanup in run_agent_server.py.
    """
    current_context = tool_context.get()
    new_context = {**current_context, "txn_hash": txn_hash}
    
    # Return the token associated with setting the entire dictionary
    return tool_context.set(new_context)

def reset_txn_hash(token: Token):
    """
    This function is now a no-op as the combined context is reset in 
    run_agent_server.py's finally block, but kept for backward compatibility.
    """
    pass

# --- 3. Privy Authentication Context Functions (Simplified & Corrected) ---

def get_user_privy_token() -> Optional[str]:
    """Retrieves the authenticated user's Privy token from the current context."""
    context = tool_context.get()
    return context.get("privy_token")

# NOTE: The setter for privy_token is handled in run_agent_server.py 
# where it extracts the token and combines it with txn_hash before calling tool_context.set().
# We don't need a standalone setter here if run_agent_server.py handles the extraction and merging.