import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.schemas import OrderRequest, CancelRequest, OrderResponse
from app.clob_client import place_order, cancel_order, get_orders, get_order, cancel_all_orders, resolve_token_id

router = APIRouter(tags=["orders"])


@router.post("/order", response_model=OrderResponse)
async def create_order(req: OrderRequest):
    token_id = req.token_id

    if not token_id:
        if not req.condition_id or not req.outcome:
            raise HTTPException(
                status_code=400,
                detail="Provide either token_id, or condition_id + outcome",
            )
        try:
            token_id = await asyncio.to_thread(
                resolve_token_id, req.condition_id, req.outcome.value
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Resolve size: accept either `size` (shares) or `dollars` (USD amount)
    size = req.size
    if req.dollars is not None:
        if req.order_type.value == "MARKET":
            # For MARKET BUY, size IS the dollar amount already
            size = req.dollars
        else:
            # For LIMIT, convert dollars to shares: shares = dollars / price
            if req.price is None or req.price <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Price required to convert dollars to shares for LIMIT orders",
                )
            size = req.dollars / req.price

    if size is None or size <= 0:
        raise HTTPException(
            status_code=400,
            detail="Provide either size (shares) or dollars (USD amount)",
        )

    result = await place_order(
        token_id=token_id,
        side=req.side.value,
        size=size,
        price=req.price,
        order_type=req.order_type.value,
    )
    return OrderResponse(**result)


@router.delete("/order", response_model=OrderResponse)
async def delete_order(req: CancelRequest):
    result = await cancel_order(order_id=req.order_id)
    return OrderResponse(**result)


@router.get("/orders")
async def list_orders(market: Optional[str] = None, asset_id: Optional[str] = None):
    return await get_orders(market=market, asset_id=asset_id)


@router.get("/order/{order_id}")
async def get_single_order(order_id: str):
    return await get_order(order_id=order_id)


@router.delete("/orders", response_model=OrderResponse)
async def cancel_all():
    result = await cancel_all_orders()
    return OrderResponse(**result)
