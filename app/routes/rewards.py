import logging

import httpx
from fastapi import APIRouter
from py_clob_client.clob_types import RequestArgs
from py_clob_client.headers.headers import create_level_2_headers

from app.clob_client import get_clob_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["rewards"])

CLOB_HOST = "https://clob.polymarket.com"


def _call_clob_authenticated_get(bare_path: str, query: str = "signature_type=1") -> dict:
    """Make an authenticated GET to the CLOB, signing the bare path."""
    client = get_clob_client()
    args = RequestArgs(method="GET", request_path=bare_path, body=None)
    headers = create_level_2_headers(client.signer, client.creds, args)
    url = f"{CLOB_HOST}{bare_path}" + (f"?{query}" if query else "")
    r = httpx.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()


@router.get("/rewards/markets")
async def get_reward_markets():
    try:
        client = get_clob_client()

        all_markets: list[dict] = []
        cursor = ""
        pages = 0
        MAX_PAGES = 100  # safety — 100 per page = up to 10000 markets

        while pages < MAX_PAGES:
            query_parts = ["signature_type=1"]
            if cursor and cursor != "LTE=":
                query_parts.append(f"next_cursor={cursor}")
            query = "&".join(query_parts)

            bare_path = "/rewards/user/markets"
            args = RequestArgs(method="GET", request_path=bare_path, body=None)
            headers = create_level_2_headers(client.signer, client.creds, args)
            url = f"{CLOB_HOST}{bare_path}?{query}"

            r = httpx.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            data = r.json()

            batch = data.get("data", data if isinstance(data, list) else [])
            all_markets.extend(batch)
            next_cursor = data.get("next_cursor", "LTE=")

            pages += 1
            if next_cursor == "LTE=" or not batch or next_cursor == cursor:
                break
            cursor = next_cursor

        logger.info("[rewards] /markets paginated %d pages, %d total", pages, len(all_markets))
        return {"data": all_markets}
    except Exception as exc:
        logger.error("[rewards] markets failed: %s", exc)
        return {"error": str(exc)}


@router.get("/rewards/percentages")
async def get_reward_percentages():
    try:
        return _call_clob_authenticated_get("/rewards/user/percentages")
    except Exception as exc:
        logger.error("[rewards] percentages failed: %s", exc)
        return {"error": str(exc)}


@router.get("/rewards/user/active")
async def get_user_active_rewards():
    try:
        return _call_clob_authenticated_get(
            "/rewards/user/markets",
            query="only_open_orders=true&signature_type=1&page_size=500",
        )
    except Exception as exc:
        logger.error("[rewards] user/active failed: %s", exc)
        return {"error": str(exc)}
