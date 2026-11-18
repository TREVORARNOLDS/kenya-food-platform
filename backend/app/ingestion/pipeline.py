import logging
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from flask import current_app
from geoalchemy2.elements import WKTElement
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.extensions import db
from app.ingestion.sources import wfp
from app.models import (
    Commodity,
    County,
    DataSource,
    IngestionRun,
    Market,
    PriceObservation,
)

log = logging.getLogger(__name__)
CHUNK_SIZE = 2000


def _none_if_nan(value):
    return None if pd.isna(value) else float(value)


def _get_or_create_source() -> DataSource:
    source = db.session.scalar(select(DataSource).where(DataSource.name == wfp.SOURCE_NAME))
    if source is None:
        source = DataSource(name=wfp.SOURCE_NAME, url=wfp.SOURCE_URL)
        db.session.add(source)
        db.session.commit()
    return source


def _ensure_counties(names) -> dict[str, int]:
    ids = dict(db.session.execute(select(County.name, County.id)).all())
    new = [County(name=n) for n in names if n not in ids]
    db.session.add_all(new)
    db.session.flush()
    ids.update({c.name: c.id for c in new})
    return ids


def _ensure_commodities(df: pd.DataFrame) -> dict[str, int]:
    ids = dict(db.session.execute(select(Commodity.name, Commodity.id)).all())
    new = [
        Commodity(name=row.commodity, category=row.category or None)
        for row in df.drop_duplicates("commodity").itertuples()
        if row.commodity not in ids
    ]
    db.session.add_all(new)
    db.session.flush()
    ids.update({c.name: c.id for c in new})
    return ids


def _ensure_markets(df: pd.DataFrame, county_ids: dict[str, int]) -> dict[tuple, int]:
    ids = {
        (name, county_id): mid
        for name, county_id, mid in db.session.execute(
            select(Market.name, Market.county_id, Market.id)
        ).all()
    }
    new = []
    for row in df.drop_duplicates(["market", "county"]).itertuples():
        county_id = county_ids[row.county]
        if (row.market, county_id) in ids:
            continue
        lat, lon = _none_if_nan(row.latitude), _none_if_nan(row.longitude)
        point = WKTElement(f"POINT({lon} {lat})", srid=4326) if lat is not None and lon is not None else None
        new.append(
            Market(name=row.market, county_id=county_id, latitude=lat, longitude=lon, location=point)
        )
    db.session.add_all(new)
    db.session.flush()
    ids.update({(m.name, m.county_id): m.id for m in new})
    return ids


def load_prices(df: pd.DataFrame, data_source_id: int, run_id: int) -> int:
    """Insert price rows, skipping any that already exist. Returns rows inserted."""
    if df.empty:
        return 0
    county_ids = _ensure_counties(df["county"].unique())
    commodity_ids = _ensure_commodities(df)
    market_ids = _ensure_markets(df, county_ids)

    rows = [
        {
            "market_id": market_ids[(r.market, county_ids[r.county])],
            "commodity_id": commodity_ids[r.commodity],
            "data_source_id": data_source_id,
            "ingestion_run_id": run_id,
            "observed_on": r.observed_on,
            "unit": r.unit,
            "price_type": r.price_type,
            "currency": r.currency,
            "price": float(r.price),
            "price_usd": _none_if_nan(r.price_usd),
        }
        for r in df.itertuples(index=False)
    ]

    loaded = 0
    for i in range(0, len(rows), CHUNK_SIZE):
        stmt = (
            pg_insert(PriceObservation)
            .values(rows[i : i + CHUNK_SIZE])
            .on_conflict_do_nothing(constraint="uq_price_observation")
            .returning(PriceObservation.id)
        )
        loaded += len(db.session.execute(stmt).all())
    return loaded


def run_wfp_prices(file_path: Path | None = None) -> IngestionRun:
    source = _get_or_create_source()
    run = IngestionRun(data_source_id=source.id, command="wfp-prices")
    db.session.add(run)
    db.session.commit()
    run_id = run.id

    try:
        if file_path is None:
            raw_dir = Path(current_app.root_path).parent / "data" / "raw" / "wfp"
            file_path = wfp.download_csv(raw_dir)
        run.raw_file_path = str(file_path)

        df, retrieved, failures = wfp.parse_prices(Path(file_path))
        run.records_retrieved = retrieved
        run.validation_failures = failures
        run.records_loaded = load_prices(df, source.id, run_id)
        run.status = "success"
        run.completed_at = datetime.now(UTC)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        failed = db.session.get(IngestionRun, run_id)
        failed.status = "failed"
        failed.error_message = str(exc)[:2000]
        failed.completed_at = datetime.now(UTC)
        db.session.commit()
        log.exception("Ingestion run %s failed", run_id)
        raise
    return run
