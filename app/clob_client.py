import asyncio
import logging

import httpx
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import (
    ApiCreds, OrderArgs, MarketOrderArgs, OrderType as ClobOrderType,
    BalanceAllowanceParams, AssetType, OpenOrderParams, TradeParams,
)
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


def resolve_token_id(condition_id: str, outcome: str) -> str:
    """Resolve a condition_id + outcome ('Yes'/'No') to a token_id."""
    client = get_clob_client()
    market = client.get_market(condition_id)
    tokens = market.get("tokens", [])
    for token in tokens:
        if token.get("outcome", "").lower() == outcome.lower():
            return token["token_id"]
    raise ValueError(f"No '{outcome}' token found for condition_id={condition_id}")


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


def _get_balance_allowance() -> dict:
    client = get_clob_client()
    collateral = client.get_balance_allowance(
        BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
    )
    return collateral


async def get_balance() -> dict:
    try:
        return await asyncio.to_thread(_get_balance_allowance)
    except Exception as e:
        logger.exception("Failed to get balance")
        return {"error": str(e)}


# --- Positions (conditional token balances) ---

def _get_position(token_id: str) -> dict:
    client = get_clob_client()
    return client.get_balance_allowance(
        BalanceAllowanceParams(asset_type=AssetType.CONDITIONAL, token_id=token_id)
    )


async def get_position(token_id: str) -> dict:
    try:
        return await asyncio.to_thread(_get_position, token_id)
    except Exception as e:
        logger.exception("Failed to get position")
        return {"error": str(e)}


async def cancel_order(order_id: str) -> dict:
    try:
        return await asyncio.to_thread(_cancel_order, order_id)
    except Exception as e:
        logger.exception("Failed to cancel order")
        return {"success": False, "error": str(e)}


# --- Open orders ---

def _get_orders(market: str | None, asset_id: str | None) -> dict:
    client = get_clob_client()
    params = OpenOrderParams(market=market, asset_id=asset_id)
    return client.get_orders(params)


async def get_orders(market: str | None = None, asset_id: str | None = None) -> dict:
    try:
        return await asyncio.to_thread(_get_orders, market, asset_id)
    except Exception as e:
        logger.exception("Failed to get orders")
        return {"error": str(e)}


# --- Single order ---

def _get_order(order_id: str) -> dict:
    client = get_clob_client()
    return client.get_order(order_id)


async def get_order(order_id: str) -> dict:
    try:
        return await asyncio.to_thread(_get_order, order_id)
    except Exception as e:
        logger.exception("Failed to get order")
        return {"error": str(e)}


# --- Cancel all ---

def _cancel_all() -> dict:
    client = get_clob_client()
    resp = client.cancel_all()
    logger.info("All orders cancelled: %s", resp)
    return {"success": True}


async def cancel_all_orders() -> dict:
    try:
        return await asyncio.to_thread(_cancel_all)
    except Exception as e:
        logger.exception("Failed to cancel all orders")
        return {"success": False, "error": str(e)}


# --- Price ---

def _get_price(token_id: str, side: str | None) -> dict:
    client = get_clob_client()
    midpoint = client.get_midpoint(token_id)
    result = {"midpoint": midpoint, "token_id": token_id}
    if side:
        price = client.get_price(token_id, SIDE_MAP[side])
        result["price"] = price
        result["side"] = side
    return result


async def get_market_price(token_id: str, side: str | None = None) -> dict:
    try:
        return await asyncio.to_thread(_get_price, token_id, side)
    except Exception as e:
        logger.exception("Failed to get price")
        return {"error": str(e)}


# --- Trades ---

def _get_trades(market: str | None, asset_id: str | None) -> dict:
    client = get_clob_client()
    params = TradeParams(market=market, asset_id=asset_id)
    return client.get_trades(params)


async def get_trades(market: str | None = None, asset_id: str | None = None) -> dict:
    try:
        return await asyncio.to_thread(_get_trades, market, asset_id)
    except Exception as e:
        logger.exception("Failed to get trades")
        return {"error": str(e)}


# --- Positions (all, via Data API) ---

DATA_API_URL = "https://data-api.polymarket.com"


async def get_positions(limit: int = 100, size_threshold: float = 0) -> list | dict:
    try:
        client = get_clob_client()
        wallet = client.get_address()
        async with httpx.AsyncClient() as http:
            resp = await http.get(
                f"{DATA_API_URL}/positions",
                params={
                    "user": wallet,
                    "limit": limit,
                    "sizeThreshold": size_threshold,
                    "sortBy": "CURRENT",
                    "sortDirection": "DESC",
                },
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.exception("Failed to get positions")
        return {"error": str(e)}
