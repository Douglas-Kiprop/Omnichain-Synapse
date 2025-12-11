# spoon-core/spoon_ai/utils/auth.py

from typing import Optional
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

def extract_privy_token(request: Request) -> Optional[str]:
    """
    Extracts the Privy JWT token from the Authorization header of the request.
    Expected format: "Bearer <token>"
    """
    authorization_header = request.headers.get("Authorization")
    
    if not authorization_header:
        logger.warning("Authorization header missing in request.")
        return None
        
    try:
        scheme, token = authorization_header.split()
        if scheme.lower() == "bearer" and token:
            logger.info("Successfully extracted Privy token from request.")
            return token
    except ValueError:
        logger.warning("Authorization header format invalid.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error extracting token: {e}")
        return None
        
    return None