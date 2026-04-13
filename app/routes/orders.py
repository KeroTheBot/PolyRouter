from typing import Optional

from fastapi import APIRouter

from app.schemas import OrderRequest, CancelRequest, OrderResponse
from app.clob_client import place_order, cancel_order, get_orders, get_order, cancel_all_orders

router = APIRouter(tags=["orders"])


@router.post("/order", response_model=OrderResponse)
async def create_order(req: OrderRequest):
    result = await place_order(
        token_id=req.token_id,
        side=req.side.value,
        size=req.size,
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
