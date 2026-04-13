# PolyRouter

Lightweight order routing service for Polymarket CLOB API. Receives trade signals from a local dashboard and places orders on Polymarket.

## Architecture

- **Local (NUC/laptop):** Dashboard, market scanner, AI research agent
- **VPS (this service):** Receives trade signals, routes to Polymarket CLOB API

## Setup

```bash
cp .env.example .env
# 1. Set POLY_API_KEY (shared secret between dashboard and router)
# 2. Set POLY_PRIVATE_KEY (your Polymarket wallet private key)
# 3. Start the service, then POST /api/derive-creds to get CLOB credentials
# 4. Copy the returned api_key, api_secret, api_passphrase into .env
# 5. Restart the service
```

## Run

```bash
docker compose up -d
```

## API

All `/api/*` endpoints require `X-API-Key` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (no auth) |
| POST | `/api/order` | Place an order |
| DELETE | `/api/order` | Cancel an order |
| POST | `/api/derive-creds` | Derive CLOB API credentials from private key |

### Place Limit Order

```json
POST /api/order
{
  "token_id": "abc123...",
  "side": "BUY",
  "size": 10.0,
  "price": 0.55,
  "order_type": "LIMIT"
}
```

### Place Market Order

```json
POST /api/order
{
  "token_id": "abc123...",
  "side": "BUY",
  "size": 25.0,
  "order_type": "MARKET"
}
```

Note: For MARKET BUY, `size` is the USD amount. For MARKET SELL, `size` is the number of shares.

### Cancel Order

```json
DELETE /api/order
{
  "order_id": "xyz789..."
}
```

### Derive Credentials

```bash
curl -X POST https://your-vps:8080/api/derive-creds -H "X-API-Key: your-key"
```

Returns `api_key`, `api_secret`, `api_passphrase` — copy these into your `.env`.
