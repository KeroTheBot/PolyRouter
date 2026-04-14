import asyncio

from fastapi import APIRouter

from app.clob_client import derive_api_creds
from app.approval import approve_usdc

router = APIRouter(tags=["setup"])


@router.post("/derive-creds")
async def derive_credentials():
    """Derive CLOB API credentials from the configured private key.

    Run this once after initial setup. Copy the returned values into your .env file
    as POLY_CLOB_API_KEY, POLY_CLOB_API_SECRET, and POLY_CLOB_API_PASSPHRASE.
    """
    result = await asyncio.to_thread(derive_api_creds)
    return result


@router.post("/approve")
async def approve():
    """One-time USDC approval for the Polymarket exchange contracts.

    Sends on-chain ERC-20 approve transactions on Polygon, then tells
    Polymarket to refresh your allowance. Requires a small amount of
    MATIC in your wallet for gas.
    """
    return await approve_usdc()
