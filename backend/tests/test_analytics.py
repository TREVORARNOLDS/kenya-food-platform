from datetime import date

import pytest

from app.analytics.volatility import volatility_stats
from app.extensions import db
from app.models import Commodity, County, DataSource, Market, PriceObservation


def test_volatility_constant_series_is_zero():
    series = [(date(2024, m, 15), 100.0) for m in (1, 2, 3, 4)]
    stats = volatility_stats(series)
    assert stats["months"] == 4
    assert stats["coefficient_of_variation_pct"] == pytest.approx(0)
    assert stats["mean_abs_monthly_change_pct"] == pytest.approx(0)


def test_volatility_steady_growth():
    series = [(date(2024, 1, 1), 100.0), (date(2024, 2, 1), 110.0), (date(2024, 3, 1), 121.0)]
    stats = volatility_stats(series)
    assert stats["mean_abs_monthly_change_pct"] == pytest.approx(10)
    assert stats["monthly_change_std_pct"] == pytest.approx(0, abs=1e-9)
    assert stats["coefficient_of_variation_pct"] > 0


def test_volatility_ignores_gaps_between_months():
    series = [(date(2024, 1, 1), 100.0), (date(2024, 2, 1), 110.0), (date(2024, 4, 1), 200.0)]
    stats = volatility_stats(series)
    assert stats["mean_abs_monthly_change_pct"] == pytest.approx(10)  # Jan->Feb only
    assert stats["monthly_change_std_pct"] is None  # a single valid change


def test_volatility_needs_enough_data():
    assert volatility_stats([])["mean_price"] is None
    short = volatility_stats([(date(2024, 1, 1), 100.0), (date(2024, 2, 1), 110.0)])
    assert short["mean_price"] == pytest.approx(105)
    assert short["coefficient_of_variation_pct"] is None


@pytest.fixture()
def maize(db_session):
    src = DataSource(name="test-source")
    county = County(name="Mombasa")
    db.session.add_all([src, county])
    db.session.flush()
    m1 = Market(name="Mombasa", county_id=county.id)
    m2 = Market(name="Kongowea", county_id=county.id)
    commodity = Commodity(name="Maize")
    db.session.add_all([m1, m2, commodity])
    db.session.flush()

    def add(market, month, value, unit="KG", price_type="retail"):
        db.session.add(
            PriceObservation(
                market_id=market.id, commodity_id=commodity.id, data_source_id=src.id,
                observed_on=date(2024, month, 15), unit=unit, price_type=price_type,
                price=value,
            )
        )

    add(m1, 1, 100)
    add(m2, 1, 120)       # same month, other market: January average is 110
    add(m1, 2, 130)
    add(m1, 3, 150)
    add(m1, 1, 9000, unit="90 KG")
    add(m1, 1, 50, price_type="wholesale")
    db.session.commit()
    return {"commodity": commodity.id, "county": county.id, "market": m1.id}


def test_trend_averages_by_month_and_picks_main_unit(client, maize):
    body = client.get("/api/v1/prices/trends/", query_string={"commodity_id": maize["commodity"]}).json
    assert body["unit"] == "KG"
    assert body["available_units"] == ["KG", "90 KG"]
    assert [p["avg_price"] for p in body["points"]] == [110.0, 130.0, 150.0]
    assert body["points"][0]["observations"] == 2
    assert body["points"][0]["month"] == "2024-01-01"


def test_trend_unit_price_type_and_market_filters(client, maize):
    base = {"commodity_id": maize["commodity"]}
    big = client.get("/api/v1/prices/trends/", query_string={**base, "unit": "90 KG"}).json
    assert [p["avg_price"] for p in big["points"]] == [9000.0]
    wholesale = client.get("/api/v1/prices/trends/", query_string={**base, "price_type": "wholesale"}).json
    assert [p["avg_price"] for p in wholesale["points"]] == [50.0]
    one_market = client.get("/api/v1/prices/trends/", query_string={**base, "market_id": maize["market"]}).json
    assert one_market["points"][0]["avg_price"] == 100.0
    by_county = client.get("/api/v1/prices/trends/", query_string={**base, "county_id": maize["county"]}).json
    assert len(by_county["points"]) == 3


def test_trend_with_no_data_is_empty(client, maize):
    body = client.get("/api/v1/prices/trends/", query_string={"commodity_id": 99999}).json
    assert body["points"] == []
    assert body["unit"] is None


def test_volatility_endpoint(client, maize):
    body = client.get("/api/v1/prices/volatility/", query_string={"commodity_id": maize["commodity"]}).json
    assert body["stats"]["months"] == 3
    assert body["stats"]["mean_price"] == pytest.approx(130)


@pytest.mark.parametrize(
    "params",
    [{}, {"commodity_id": "abc"}, {"commodity_id": 1, "price_type": "bogus"},
     {"commodity_id": 1, "date_from": "2024-03-01", "date_to": "2024-01-01"}],
)
def test_trend_rejects_invalid_query(client, params):
    assert client.get("/api/v1/prices/trends/", query_string=params).status_code == 422
