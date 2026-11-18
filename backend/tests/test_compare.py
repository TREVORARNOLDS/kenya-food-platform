from datetime import date

import pytest

from app.extensions import db
from app.models import Commodity, County, DataSource, Market, PriceObservation


@pytest.fixture()
def maize(db_session):
    src = DataSource(name="test-source")
    mombasa, nairobi = County(name="Mombasa"), County(name="Nairobi")
    db.session.add_all([src, mombasa, nairobi])
    db.session.flush()
    m1 = Market(name="Mombasa", county_id=mombasa.id)
    m2 = Market(name="Kongowea", county_id=mombasa.id)
    m3 = Market(name="Wakulima", county_id=nairobi.id)
    commodity = Commodity(name="Maize")
    db.session.add_all([m1, m2, m3, commodity])
    db.session.flush()

    def add(market, when, value, unit="KG"):
        db.session.add(
            PriceObservation(
                market_id=market.id, commodity_id=commodity.id, data_source_id=src.id,
                observed_on=when, unit=unit, price_type="retail", price=value,
            )
        )

    add(m1, date(2024, 1, 15), 100)
    add(m2, date(2024, 1, 15), 120)
    add(m3, date(2024, 1, 15), 200)
    add(m1, date(2023, 6, 15), 9999)           # older than the default 90-day window
    add(m1, date(2024, 1, 15), 5000, unit="90 KG")  # different unit
    db.session.commit()
    return {"commodity": commodity.id}


def test_compare_counties_uses_default_window(client, maize):
    body = client.get("/api/v1/prices/compare/", query_string={"commodity_id": maize["commodity"]}).json
    assert body["unit"] == "KG"
    assert body["date_to"] == "2024-01-15"
    assert body["date_from"] == "2023-10-17"
    assert [(i["name"], i["avg_price"]) for i in body["items"]] == [
        ("Nairobi", pytest.approx(200)),
        ("Mombasa", pytest.approx(110)),
    ]
    assert body["overall_avg_price"] == pytest.approx(140)


def test_compare_markets(client, maize):
    body = client.get(
        "/api/v1/prices/compare/",
        query_string={"commodity_id": maize["commodity"], "group_by": "market"},
    ).json
    assert [(i["name"], i["county_name"]) for i in body["items"]] == [
        ("Wakulima", "Nairobi"),
        ("Kongowea", "Mombasa"),
        ("Mombasa", "Mombasa"),
    ]


def test_compare_explicit_date_range_includes_older_prices(client, maize):
    body = client.get(
        "/api/v1/prices/compare/",
        query_string={"commodity_id": maize["commodity"], "date_from": "2023-01-01"},
    ).json
    mombasa = next(i for i in body["items"] if i["name"] == "Mombasa")
    assert mombasa["observations"] == 3


def test_compare_with_no_data_is_empty(client, maize):
    body = client.get("/api/v1/prices/compare/", query_string={"commodity_id": 99999}).json
    assert body["items"] == []
    assert body["unit"] is None


@pytest.mark.parametrize(
    "params",
    [{}, {"commodity_id": 1, "group_by": "bogus"}, {"commodity_id": 1, "limit": 0}],
)
def test_compare_rejects_invalid_query(client, params):
    assert client.get("/api/v1/prices/compare/", query_string=params).status_code == 422
