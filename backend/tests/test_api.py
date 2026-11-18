from datetime import date

import pytest

from app.extensions import db
from app.models import Commodity, County, DataSource, Market, PriceObservation


@pytest.fixture()
def seeded(db_session):
    src = DataSource(name="test-source")
    mombasa, nairobi = County(name="Mombasa"), County(name="Nairobi")
    db.session.add_all([src, mombasa, nairobi])
    db.session.flush()

    m1 = Market(name="Mombasa", county_id=mombasa.id)
    m2 = Market(name="Wakulima", county_id=nairobi.id)
    maize = Commodity(name="Maize", category="cereals and tubers")
    beans = Commodity(name="Beans", category="pulses and nuts")
    db.session.add_all([m1, m2, maize, beans])
    db.session.flush()

    def price(market, commodity, month, value):
        return PriceObservation(
            market_id=market.id, commodity_id=commodity.id, data_source_id=src.id,
            observed_on=date(2024, month, 15), unit="KG", price_type="retail", price=value,
        )

    db.session.add_all([
        price(m1, maize, 1, 100), price(m1, maize, 2, 110), price(m1, maize, 3, 120),
        price(m2, beans, 1, 150), price(m2, beans, 2, 160),
    ])
    db.session.commit()
    return {"mombasa": mombasa.id, "maize": maize.id}


def test_counties_list(client, seeded):
    body = client.get("/api/v1/counties/").json
    assert body["total"] == 2
    assert [c["name"] for c in body["items"]] == ["Mombasa", "Nairobi"]


def test_markets_filter_by_county(client, seeded):
    body = client.get("/api/v1/markets/", query_string={"county_id": seeded["mombasa"]}).json
    assert body["total"] == 1
    assert body["items"][0]["county_name"] == "Mombasa"


def test_commodities_filter_by_category(client, seeded):
    body = client.get("/api/v1/commodities/", query_string={"category": "pulses and nuts"}).json
    assert [c["name"] for c in body["items"]] == ["Beans"]


def test_prices_filters_and_date_range(client, seeded):
    assert client.get("/api/v1/prices/").json["total"] == 5
    by_commodity = client.get("/api/v1/prices/", query_string={"commodity_id": seeded["maize"]})
    assert by_commodity.json["total"] == 3
    by_county = client.get("/api/v1/prices/", query_string={"county_id": seeded["mombasa"]})
    assert by_county.json["total"] == 3
    recent = client.get("/api/v1/prices/", query_string={"date_from": "2024-02-01"})
    assert recent.json["total"] == 3


def test_prices_sorting_and_pagination(client, seeded):
    body = client.get(
        "/api/v1/prices/", query_string={"sort": "price", "order": "asc", "page_size": 2}
    ).json
    assert body["total"] == 5
    assert body["pages"] == 3
    assert len(body["items"]) == 2
    assert body["items"][0]["price"] == 100.0
    assert body["items"][0]["commodity_name"] == "Maize"


@pytest.mark.parametrize(
    "params",
    [
        {"page_size": 1000},
        {"page": 0},
        {"sort": "nonsense"},
        {"date_from": "2024-03-01", "date_to": "2024-01-01"},
        {"date_from": "not-a-date"},
    ],
)
def test_prices_reject_invalid_query(client, params):
    assert client.get("/api/v1/prices/", query_string=params).status_code == 422
