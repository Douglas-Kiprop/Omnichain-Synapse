import jwt
from jwt import PyJWKClient
from typing import Dict, Any, Optional
from core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

class PrivyProvider:
    def __init__(self):
        self.jwks_client = PyJWKClient(settings.PRIVY_JWKS_URL)
        self.app_id = settings.PRIVY_APP_ID
        logger.info(f"PrivyProvider initialized with JWKS URL: {settings.PRIVY_JWKS_URL} and App ID: {self.app_id}")
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Privy JWT token and return claims
        """
        try:
            # Get signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            
            # Decode token header to inspect algorithm
            decoded_header = jwt.get_unverified_header(token)
            logger.info(f"JWT Token Header: {decoded_header}")

            # Decode and verify token
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256"],
                audience=self.app_id,
                issuer="privy.io"
            )
            
            logger.info(f"Successfully verified token for user: {claims.get('sub')}")
            return claims
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return None
    
    def extract_user_data(self, claims: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract user data from Privy token claims
        """
        return {
            "privy_user_id": claims.get("sub"),
            "email": claims.get("email"),
            "phone": claims.get("phone_number"),
            "wallet_address": claims.get("wallet", {}).get("address") if claims.get("wallet") else None,
            "identities": claims.get("custom", {}).get("identities", []),
        }
