import asyncio
import logging

from py_clob_client.clob_types import BalanceAllowanceParams, AssetType

from app.clob_client import get_clob_client

logger = logging.getLogger(__name__)


def _approve_and_update() -> dict:
    client = get_clob_client()

    # update_balance_allowance tells Polymarket to set/refresh the USDC allowance.
    # With builder auth, this goes through the relayer (gasless).
    resp_collateral = client.update_balance_allowance(
        BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
    )

    # Verify the new state
    balance = client.get_balance_allowance(
        BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
    )

    return {
        "success": True,
        "collateral_update": resp_collateral,
        "balance_after": balance,
    }


async def approve_usdc() -> dict:
    try:
        return await asyncio.to_thread(_approve_and_update)
    except Exception as e:
        logger.exception("Failed to approve USDC")
        return {"success": False, "error": str(e)}
