from pydantic import BaseModel
from enum import Enum
from typing import Optional


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class Outcome(str, Enum):
    YES = "Yes"
    NO = "No"


class OrderRequest(BaseModel):
    token_id: Optional[str] = None  # direct token ID (takes priority)
    condition_id: Optional[str] = None  # market condition ID (resolved to token_id via outcome)
    outcome: Optional[Outcome] = None  # required when using condition_id
    side: Side
    size: Optional[float] = None  # shares (LIMIT) or USD amount (MARKET BUY)
    dollars: Optional[float] = None  # USD amount — auto-converts to shares using price
    price: Optional[float] = None  # required for LIMIT, ignored for MARKET
    order_type: OrderType = OrderType.LIMIT


class CancelRequest(BaseModel):
    order_id: str


class OrderResponse(BaseModel):
    success: bool
    order_id: Optional[str] = None
    error: Optional[str] = None
