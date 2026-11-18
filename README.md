# Kenya Food Security & Market Intelligence Platform

Flask + PostgreSQL/PostGIS backend, Next.js frontend. Data: WFP Kenya food prices (via HDX).

## Prerequisites (Ubuntu)

Python 3.10+, Node 20.9+, Docker with the compose plugin.

## First-time setup

    docker compose up -d

    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env
    flask db upgrade
    flask ingest wfp-prices

    cd ../frontend
    npm install
    echo "NEXT_PUBLIC_API_URL=http://localhost:5000" > .env.local

## Run

    # database (project root)
    docker compose up -d

    # backend, http://localhost:5000  (API docs: /api/docs/swagger)
    cd backend && source .venv/bin/activate && flask run --port 5000

    # frontend, http://localhost:3000
    cd frontend && npm run dev

Pages: `/` (system status), `/prices` (price explorer), `/trends` (trends and volatility).

## Test and lint

Tests use the separate `kfs_test` database and never touch `kfs_dev`.

    cd backend && source .venv/bin/activate
    pytest -v
    ruff check .

## API (all under /api/v1)

    GET /health/
    GET /counties/   /markets/   /commodities/
    GET /prices/            list with filters, sorting, pagination
    GET /prices/trends/     monthly average/min/max, one commodity and unit
    GET /prices/volatility/ volatility of the monthly averages
    GET /prices/compare/    rank counties or markets by average price

## Ingestion

    flask ingest wfp-prices                 # download from HDX and load
    flask ingest wfp-prices --file x.csv    # load a local CSV

Re-running is safe: existing rows are skipped. Raw files are kept in `backend/data/raw/`.

## Notes

- Prices are compared per commodity and per unit, never mixed across units.
- Database credentials in `docker-compose.yml` are for local development only.
