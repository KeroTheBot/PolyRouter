from fastapi import APIRouter

from app.clob_client import get_balance, get_position, get_positions

router = APIRouter(tags=["balance"])


@router.get("/balance")
async def balance():
    return await get_balance()


@router.get("/positions")
async def positions(limit: int = 100, size_threshold: float = 0):
    return await get_positions(limit=limit, size_threshold=size_threshold)


@router.get("/position/{token_id}")
async def position(token_id: str):
    return await get_position(token_id=token_id)
