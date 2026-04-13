from typing import Optional

from fastapi import APIRouter

from app.clob_client import get_market_price, get_trades

router = APIRouter(tags=["market"])


@router.get("/price/{token_id}")
async def price(token_id: str, side: Optional[str] = None):
    return await get_market_price(token_id=token_id, side=side)


@router.get("/trades")
async def trades(market: Optional[str] = None, asset_id: Optional[str] = None):
    return await get_trades(market=market, asset_id=asset_id)
