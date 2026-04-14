import asyncio
from typing import Optional

from fastapi import APIRouter

from app.clob_client import get_market_price, get_trades, get_clob_client

router = APIRouter(tags=["market"])


@router.get("/market/{condition_id}")
async def market(condition_id: str):
    """Get market info including YES/NO token IDs for a condition_id."""
    client = get_clob_client()
    return await asyncio.to_thread(client.get_market, condition_id)


@router.get("/price/{token_id}")
async def price(token_id: str, side: Optional[str] = None):
    return await get_market_price(token_id=token_id, side=side)


@router.get("/trades")
async def trades(market: Optional[str] = None, asset_id: Optional[str] = None):
    return await get_trades(market=market, asset_id=asset_id)
