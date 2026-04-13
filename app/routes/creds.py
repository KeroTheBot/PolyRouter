import asyncio

from fastapi import APIRouter

from app.clob_client import derive_api_creds

router = APIRouter(tags=["credentials"])


@router.post("/derive-creds")
async def derive_credentials():
    """Derive CLOB API credentials from the configured private key.

    Run this once after initial setup. Copy the returned values into your .env file
    as POLY_CLOB_API_KEY, POLY_CLOB_API_SECRET, and POLY_CLOB_API_PASSPHRASE.
    """
    result = await asyncio.to_thread(derive_api_creds)
    return result
