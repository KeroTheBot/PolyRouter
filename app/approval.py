import asyncio
import logging

from py_clob_client_v2.clob_types import BalanceAllowanceParams, AssetType

from app.clob_client import get_clob_client

logger = logging.getLogger(__name__)


def _approve_and_update() -> dict:
    clob = get_clob_client()

    # Refresh USDC (collateral) allowance — needed for BUY orders
    resp_collateral = clob.update_balance_allowance(
        BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
    )

    # Check collateral balance
    balance = clob.get_balance_allowance(
        BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
    )

    return {
        "success": True,
        "collateral_update": resp_collateral,
        "balance": balance,
    }


async def approve_usdc() -> dict:
    try:
        return await asyncio.to_thread(_approve_and_update)
    except Exception as e:
        logger.exception("Failed to approve")
        return {"success": False, "error": str(e)}
