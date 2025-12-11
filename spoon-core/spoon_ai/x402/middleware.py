from fastapi import HTTPException, Request
from spoon_ai.x402.verifier import verify_payment
from spoon_ai.utils.config import AVALANCHE_RPC, TREASURY_ADDRESS, PREMIUM_TOOL_FEE

def x402_middleware(request: Request, premium_tool: str = "premium_coingecko"):
    if not is_premium_tool(premium_tool):
        return  # Not gated
    # Return 402 response with payment details
    payment_info = {
        "status": 402,
        "payment": {
            "scheme": "exact",
            "amount": str(int(PREMIUM_TOOL_FEE * 1e18)),  # Wei
            "token": "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7",  # WAVAX on Fuji
            "recipient": TREASURY_ADDRESS,
            "description": f"Access {premium_tool}"
        }
    }
    raise HTTPException(status_code=402, detail=payment_info)

def is_premium_tool(tool_name: str) -> bool:
    return tool_name.startswith("premium_")  # Customize as needed