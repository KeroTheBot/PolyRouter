import asyncio
import logging

from eth_abi import encode
from py_builder_relayer_client.client import RelayClient
from py_builder_relayer_client.models import SafeTransaction, OperationType
from py_builder_signing_sdk.config import BuilderConfig
from py_builder_signing_sdk.sdk_types import BuilderApiKeyCreds
from py_clob_client.clob_types import BalanceAllowanceParams, AssetType

from app.config import get_settings
from app.clob_client import get_clob_client

logger = logging.getLogger(__name__)

RELAYER_URL = "https://relayer-v2.polymarket.com"
MAX_APPROVAL = 2**256 - 1

# ERC-20 approve function selector: keccak256("approve(address,uint256)")[:4]
APPROVE_SELECTOR = bytes.fromhex("095ea7b3")


def _encode_approve(spender: str, amount: int) -> str:
    """Encode an ERC-20 approve(address, uint256) call."""
    spender_bytes = bytes.fromhex(spender.replace("0x", ""))
    encoded = APPROVE_SELECTOR + encode(["address", "uint256"], [spender, amount])
    return "0x" + encoded.hex()


def _get_relay_client() -> RelayClient:
    settings = get_settings()
    builder_config = BuilderConfig(
        local_builder_creds=BuilderApiKeyCreds(
            key=settings.builder_key,
            secret=settings.builder_secret,
            passphrase=settings.builder_passphrase,
        )
    )
    return RelayClient(
        RELAYER_URL,
        settings.chain_id,
        settings.private_key,
        builder_config,
    )


def _approve_and_update() -> dict:
    settings = get_settings()
    clob = get_clob_client()
    relay = _get_relay_client()

    # Ensure Safe wallet is deployed
    safe_address = relay.get_expected_safe()
    deployed = relay.get_deployed(safe_address)
    if not deployed:
        logger.info("Deploying Safe wallet: %s", safe_address)
        resp = relay.deploy()
        resp.wait()
        logger.info("Safe deployed")

    # Get contract addresses
    collateral_addr = clob.get_collateral_address()  # USDC
    exchange_addr = clob.get_exchange_address(neg_risk=False)
    exchange_neg_risk_addr = clob.get_exchange_address(neg_risk=True)

    results = []

    for spender_name, spender_addr in [
        ("exchange", exchange_addr),
        ("exchange_neg_risk", exchange_neg_risk_addr),
    ]:
        approve_data = _encode_approve(spender_addr, MAX_APPROVAL)

        tx = SafeTransaction(
            to=collateral_addr,
            operation=OperationType.Call,
            data=approve_data,
            value="0",
        )

        logger.info("Approving %s (%s) via relayer...", spender_name, spender_addr)
        resp = relay.execute([tx], f"Approve USDC for {spender_name}")
        result = resp.wait()
        logger.info("Approval %s complete: %s", spender_name, result)

        results.append({
            "spender": spender_name,
            "address": spender_addr,
            "status": "approved",
            "transaction_id": result.get("transactionID", "") if isinstance(result, dict) else str(result),
        })

    # Tell Polymarket to refresh the allowance
    clob.update_balance_allowance(
        BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
    )

    # Check updated balance
    balance = clob.get_balance_allowance(
        BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
    )

    return {
        "success": True,
        "safe_address": safe_address,
        "approvals": results,
        "balance_after": balance,
    }


async def approve_usdc() -> dict:
    try:
        return await asyncio.to_thread(_approve_and_update)
    except Exception as e:
        logger.exception("Failed to approve USDC")
        return {"success": False, "error": str(e)}
