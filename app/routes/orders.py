from fastapi import APIRouter

from app.schemas import OrderRequest, CancelRequest, OrderResponse
from app.clob_client import place_order, cancel_order

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
