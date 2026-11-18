from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models import County, Market

from .pagination import paginate_select


def list_counties(page: int, page_size: int) -> dict:
    return paginate_select(select(County).order_by(County.name), page, page_size)


def list_markets(page, page_size, county_id=None, search=None) -> dict:
    stmt = select(Market).options(joinedload(Market.county)).order_by(Market.name, Market.id)
    if county_id is not None:
        stmt = stmt.where(Market.county_id == county_id)
    if search:
        stmt = stmt.where(Market.name.ilike(f"%{search}%"))
    return paginate_select(stmt, page, page_size)
