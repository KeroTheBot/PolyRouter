import asyncio
import logging

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds, OrderArgs, MarketOrderArgs, OrderType as ClobOrderType
from py_clob_client.order_builder.constants import BUY, SELL

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: ClobClient | None = None

SIDE_MAP = {"BUY": BUY, "SELL": SELL}


def get_clob_client() -> ClobClient:
    global _client
    if _client is None:
        settings = get_settings()
        creds = None
        if settings.clob_api_key and settings.clob_api_secret:
            creds = ApiCreds(
                api_key=settings.clob_api_key,
                api_secret=settings.clob_api_secret,
                api_passphrase=settings.clob_api_passphrase,
            )
        _client = ClobClient(
            host=settings.clob_api_url,
            key=settings.private_key,
            chain_id=settings.chain_id,
            creds=creds,
        )
    return _client


def derive_api_creds() -> dict:
    """Derive CLOB API credentials from the private key. Run once, then store in .env."""
    settings = get_settings()
    client = ClobClient(
        host=settings.clob_api_url,
        key=settings.private_key,
        chain_id=settings.chain_id,
    )
    creds = client.create_or_derive_api_creds()
    return {
        "api_key": creds.api_key,
        "api_secret": creds.api_secret,
        "api_passphrase": creds.api_passphrase,
    }


def _place_limit_order(token_id: str, side: str, size: float, price: float) -> dict:
    client = get_clob_client()
    order_args = OrderArgs(
        token_id=token_id,
        price=price,
        size=size,
        side=SIDE_MAP[side],
    )
    signed = client.create_order(order_args)
    resp = client.post_order(signed, orderType=ClobOrderType.GTC)
    logger.info("Limit order placed: %s", resp)
    return {"success": True, "order_id": resp.get("orderID", "")}


def _place_market_order(token_id: str, side: str, amount: float) -> dict:
    client = get_clob_client()
    order_args = MarketOrderArgs(
        token_id=token_id,
        amount=amount,
        side=SIDE_MAP[side],
    )
    signed = client.create_market_order(order_args)
    resp = client.post_order(signed, orderType=ClobOrderType.FOK)
    logger.info("Market order placed: %s", resp)
    return {"success": True, "order_id": resp.get("orderID", "")}


def _cancel_order(order_id: str) -> dict:
    client = get_clob_client()
    resp = client.cancel(order_id)
    logger.info("Order cancelled: %s", resp)
    return {"success": True, "order_id": order_id}


async def place_order(
    token_id: str, side: str, size: float, price: float | None, order_type: str
) -> dict:
    try:
        if order_type == "MARKET":
            return await asyncio.to_thread(
                _place_market_order, token_id, side, size
            )
        else:
            if price is None:
                return {"success": False, "error": "Price required for LIMIT orders"}
            return await asyncio.to_thread(
                _place_limit_order, token_id, side, size, price
            )
    except Exception as e:
        logger.exception("Failed to place order")
        return {"success": False, "error": str(e)}


async def cancel_order(order_id: str) -> dict:
    try:
        return await asyncio.to_thread(_cancel_order, order_id)
    except Exception as e:
        logger.exception("Failed to cancel order")
        return {"success": False, "error": str(e)}
