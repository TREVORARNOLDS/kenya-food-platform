from sqlalchemy import Date, DateTime, cast, func, literal_column, select

from app.analytics.volatility import volatility_stats
from app.extensions import db
from app.models import Market, PriceObservation


def _conditions(commodity_id, price_type, market_id, date_from, date_to) -> list:
    conditions = [
        PriceObservation.commodity_id == commodity_id,
        PriceObservation.price_type == price_type,
    ]
    if market_id is not None:
        conditions.append(PriceObservation.market_id == market_id)
    if date_from:
        conditions.append(PriceObservation.observed_on >= date_from)
    if date_to:
        conditions.append(PriceObservation.observed_on <= date_to)
    return conditions


def _with_county(stmt, county_id):
    if county_id is not None:
        stmt = stmt.join(Market, Market.id == PriceObservation.market_id).where(
            Market.county_id == county_id
        )
    return stmt


def monthly_trend(
    commodity_id,
    unit=None,
    price_type="retail",
    county_id=None,
    market_id=None,
    date_from=None,
    date_to=None,
) -> dict:
    """Monthly average/min/max price for one commodity in one unit."""
    conditions = _conditions(commodity_id, price_type, market_id, date_from, date_to)

    unit_stmt = _with_county(
        select(PriceObservation.unit)
        .where(*conditions)
        .group_by(PriceObservation.unit)
        .order_by(func.count().desc(), PriceObservation.unit),
        county_id,
    )
    available = list(db.session.scalars(unit_stmt))
    chosen = unit or (available[0] if available else None)

    result = {
        "commodity_id": commodity_id,
        "unit": chosen,
        "price_type": price_type,
        "available_units": available,
        "points": [],
    }
    if chosen is None:
        return result

    # literal_column keeps 'month' inline so SELECT and GROUP BY expressions match
    month = cast(
        func.date_trunc(literal_column("'month'"), cast(PriceObservation.observed_on, DateTime)),
        Date,
    )
    stmt = _with_county(
        select(
            month.label("month"),
            func.avg(PriceObservation.price).label("avg_price"),
            func.min(PriceObservation.price).label("min_price"),
            func.max(PriceObservation.price).label("max_price"),
            func.count().label("observations"),
        )
        .where(*conditions, PriceObservation.unit == chosen)
        .group_by(month)
        .order_by(month),
        county_id,
    )
    result["points"] = [
        {
            "month": row.month,
            "avg_price": float(row.avg_price),
            "min_price": float(row.min_price),
            "max_price": float(row.max_price),
            "observations": row.observations,
        }
        for row in db.session.execute(stmt)
    ]
    return result


def price_volatility(**filters) -> dict:
    trend = monthly_trend(**filters)
    series = [(p["month"], p["avg_price"]) for p in trend["points"]]
    return {
        "commodity_id": trend["commodity_id"],
        "unit": trend["unit"],
        "price_type": trend["price_type"],
        "stats": volatility_stats(series),
    }
