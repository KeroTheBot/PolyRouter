import logging

from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

from app.auth import verify_api_key
from app.routes import orders, health, creds

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="PolyRouter",
    description="Lightweight order router for Polymarket CLOB API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(orders.router, prefix="/api", dependencies=[Depends(verify_api_key)])
app.include_router(creds.router, prefix="/api", dependencies=[Depends(verify_api_key)])
