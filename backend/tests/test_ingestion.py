from sqlalchemy import func, select

from app.ingestion.pipeline import run_wfp_prices
from app.ingestion.sources.wfp import parse_prices
from app.models import PriceObservation

SAMPLE = """date,admin1,admin2,market,latitude,longitude,category,commodity,unit,priceflag,pricetype,currency,price,usdprice
#date,#adm1+name,#adm2+name,#loc+market+name,#geo+lat,#geo+lon,#item+type,#item+name,#item+unit,#item+price+flag,#item+price+type,#currency,#value,#value+usd
2024-01-15,Coast,Mombasa,Mombasa,-4.05,39.67,cereals and tubers,Maize,KG,actual,Retail,KES,100,0.65
2024-02-15,Coast,Mombasa,Mombasa,-4.05,39.67,cereals and tubers,Maize,KG,actual,Retail,KES,105,0.68
2024-01-15,Nairobi,Nairobi,Wakulima,,,pulses and nuts,Beans,KG,actual,Retail,KES,150,0.97
2024-03-15,Coast,Mombasa,Mombasa,-4.05,39.67,cereals and tubers,Maize,KG,actual,Retail,KES,abc,
2024-01-15,Coast,Mombasa,Mombasa,-4.05,39.67,cereals and tubers,Maize,KG,actual,Retail,KES,100,0.65
"""


def _write(tmp_path):
    path = tmp_path / "sample.csv"
    path.write_text(SAMPLE)
    return path


def test_parse_drops_hxl_row_bad_prices_and_duplicates(tmp_path):
    df, retrieved, failures = parse_prices(_write(tmp_path))
    assert retrieved == 5
    assert failures == 1
    assert len(df) == 3


def test_rerun_does_not_create_duplicates(db_session, tmp_path):
    path = _write(tmp_path)
    first = run_wfp_prices(path)
    second = run_wfp_prices(path)
    assert first.status == "success"
    assert first.records_loaded == 3
    assert second.records_loaded == 0
    assert db_session.scalar(select(func.count()).select_from(PriceObservation)) == 3
