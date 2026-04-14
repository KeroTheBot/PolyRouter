from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Auth for NUC -> VPS channel
    api_key: str = ""

    # Polymarket CLOB API credentials (derive once via /api/derive-creds, then store)
    clob_api_url: str = "https://clob.polymarket.com"
    clob_api_key: str = ""
    clob_api_secret: str = ""
    clob_api_passphrase: str = ""

    # Builder API keys (gasless trading via Polymarket relayer)
    builder_key: str = ""
    builder_secret: str = ""
    builder_passphrase: str = ""

    # Relayer API keys (gasless on-chain transactions: approvals, transfers, etc.)
    relayer_key: str = ""
    relayer_address: str = ""

    # Wallet private key (hex string, with or without 0x prefix)
    private_key: str = ""

    # Polymarket proxy wallet address (your deposit address from the website)
    # Required for Magic Link wallets — set to your 0x... deposit address
    funder: str = ""

    # Chain: 137 = Polygon mainnet, 80002 = Amoy testnet
    chain_id: int = 137

    # Server
    host: str = "0.0.0.0"
    port: int = 8080

    model_config = {"env_file": ".env", "env_prefix": "POLY_"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
