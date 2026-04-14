import asyncio
import logging

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from py_clob_client.clob_types import BalanceAllowanceParams, AssetType

from app.config import get_settings
from app.clob_client import get_clob_client

logger = logging.getLogger(__name__)

# ERC-20 minimal ABI
ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
]

# Max uint256 for unlimited approval
MAX_APPROVAL = 2**256 - 1

# Multiple Polygon RPCs for reliability
POLYGON_RPCS = [
    "https://polygon-bor-rpc.publicnode.com",
    "https://polygon-rpc.com",
    "https://rpc.ankr.com/polygon",
]


def _get_web3() -> Web3:
    for rpc in POLYGON_RPCS:
        w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 30}))
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        if w3.is_connected():
            logger.info("Connected to %s", rpc)
            return w3
    raise ConnectionError("Could not connect to any Polygon RPC")


def _approve_and_update() -> dict:
    settings = get_settings()
    client = get_clob_client()

    w3 = _get_web3()
    account = w3.eth.account.from_key(settings.private_key)

    collateral_addr = client.get_collateral_address()
    exchange_addr = client.get_exchange_address(neg_risk=False)
    exchange_neg_risk_addr = client.get_exchange_address(neg_risk=True)

    collateral = w3.eth.contract(
        address=Web3.to_checksum_address(collateral_addr),
        abi=ERC20_ABI,
    )

    results = []

    for spender_name, spender_addr in [
        ("exchange", exchange_addr),
        ("exchange_neg_risk", exchange_neg_risk_addr),
    ]:
        spender_cs = Web3.to_checksum_address(spender_addr)

        current = collateral.functions.allowance(account.address, spender_cs).call()
        if current >= MAX_APPROVAL // 2:
            results.append({
                "spender": spender_name,
                "address": spender_addr,
                "status": "already_approved",
            })
            continue

        nonce = w3.eth.get_transaction_count(account.address)
        tx = collateral.functions.approve(spender_cs, MAX_APPROVAL).build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": 60000,
            "gasPrice": w3.eth.gas_price,
            "chainId": settings.chain_id,
        })

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        results.append({
            "spender": spender_name,
            "address": spender_addr,
            "status": "approved",
            "tx_hash": receipt["transactionHash"].hex(),
        })
        logger.info("Approved %s: tx=%s", spender_name, receipt["transactionHash"].hex())

    # Tell Polymarket to refresh the allowance
    client.update_balance_allowance(
        BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
    )

    return {"success": True, "approvals": results}


async def approve_usdc() -> dict:
    try:
        return await asyncio.to_thread(_approve_and_update)
    except Exception as e:
        logger.exception("Failed to approve USDC")
        return {"success": False, "error": str(e)}
