from web3 import Web3
from spoon_ai.utils.config import AVALANCHE_RPC, TREASURY_ADDRESS, PREMIUM_TOOL_FEE_WEI

w3 = Web3(Web3.HTTPProvider(AVALANCHE_RPC))

def verify_payment(txn_hash: str) -> bool:
    try:
        receipt = w3.eth.get_transaction_receipt(txn_hash)
        if not receipt or receipt.status != 1:
            return False
        tx = w3.eth.get_transaction(txn_hash)
        return (
            tx['to'].lower() == TREASURY_ADDRESS.lower() and
            tx['value'] >= PREMIUM_TOOL_FEE_WEI
        )
    except Exception as e:
        logger.error(f"Verification error: {e}")
        return False