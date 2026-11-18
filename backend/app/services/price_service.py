from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models import Commodity, Market, PriceObservation

from .pagination import paginate_select

SORT_COLUMNS = {
    "observed_on": PriceObservation.observed_on,
    "price": PriceObservation.price,
}


def list_commodities(page, page_size, category=None, search=None) -> dict:
    stmt = select(Commodity).order_by(Commodity.name)
    if category:
        stmt = stmt.where(Commodity.category == category)
    if search:
        stmt = stmt.where(Commodity.name.ilike(f"%{search}%"))
    return paginate_select(stmt, page, page_size)


def list_prices(
    page,
    page_size,
    market_id=None,
    commodity_id=None,
    county_id=None,
    price_type=None,
    date_from=None,
    date_to=None,
    sort="observed_on",
    order="desc",
) -> dict:
    stmt = select(PriceObservation).options(
        joinedload(PriceObservation.market).joinedload(Market.county),
        joinedload(PriceObservation.commodity),
    )
    if county_id is not None:
        stmt = stmt.join(PriceObservation.market).where(Market.county_id == county_id)
    if market_id is not None:
        stmt = stmt.where(PriceObservation.market_id == market_id)
    if commodity_id is not None:
        stmt = stmt.where(PriceObservation.commodity_id == commodity_id)
    if price_type:
        stmt = stmt.where(PriceObservation.price_type == price_type)
    if date_from:
        stmt = stmt.where(PriceObservation.observed_on >= date_from)
    if date_to:
        stmt = stmt.where(PriceObservation.observed_on <= date_to)

    column = SORT_COLUMNS[sort]
    direction = column.asc() if order == "asc" else column.desc()
    # id as tie-breaker keeps page boundaries stable
    stmt = stmt.order_by(direction, PriceObservation.id)
    return paginate_select(stmt, page, page_size)
