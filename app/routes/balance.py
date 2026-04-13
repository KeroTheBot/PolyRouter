from fastapi import APIRouter

from app.clob_client import get_balance, get_position

router = APIRouter(tags=["balance"])


@router.get("/balance")
async def balance():
    return await get_balance()


@router.get("/position/{token_id}")
async def position(token_id: str):
    return await get_position(token_id=token_id)
