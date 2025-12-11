# spoon_ai/x402/context.py
from contextvars import ContextVar
from typing import Optional

# This creates a thread-safe variable that lives only for the duration of a request
_txn_hash_ctx: ContextVar[Optional[str]] = ContextVar("txn_hash", default=None)

def set_txn_hash(txn_hash: Optional[str]):
    return _txn_hash_ctx.set(txn_hash)

def get_txn_hash() -> Optional[str]:
    return _txn_hash_ctx.get()

def reset_txn_hash(token):
    _txn_hash_ctx.reset(token)