from pydantic import BaseModel
from enum import Enum
from typing import Optional


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class OrderRequest(BaseModel):
    token_id: str
    side: Side
    size: float  # shares for LIMIT, USD amount for MARKET BUY, shares for MARKET SELL
    price: Optional[float] = None  # required for LIMIT, ignored for MARKET
    order_type: OrderType = OrderType.LIMIT


class CancelRequest(BaseModel):
    order_id: str


class OrderResponse(BaseModel):
    success: bool
    order_id: Optional[str] = None
    error: Optional[str] = None
