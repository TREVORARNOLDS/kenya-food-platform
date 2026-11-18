"""WFP Kenya food prices (via HDX): download, save raw file, validate."""
import logging
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)

HDX_PACKAGE_URL = "https://data.humdata.org/api/3/action/package_show"
DATASET_ID = "wfp-food-prices-for-kenya"
SOURCE_NAME = "WFP Food Prices for Kenya (HDX)"
SOURCE_URL = "https://data.humdata.org/dataset/wfp-food-prices-for-kenya"

REQUIRED_COLUMNS = {
    "date", "admin1", "admin2", "market", "latitude", "longitude", "category",
    "commodity", "unit", "pricetype", "currency", "price", "usdprice",
}


# admin2 holds counties, except a few old districts that sit inside a county.
COUNTY_ALIASES = {
    "Meru North": "Meru",
    "Meru South": "Meru",
    "Moyale": "Marsabit",
    "Ijara": "Garissa",
}


def _session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def find_csv_url(session: requests.Session) -> str:
    resp = session.get(HDX_PACKAGE_URL, params={"id": DATASET_ID}, timeout=60)
    resp.raise_for_status()
    resources = resp.json()["result"]["resources"]
    candidates = []
    for res in resources:
        url = res.get("download_url") or res.get("url") or ""
        name = (res.get("name") or "").lower()
        is_csv = (res.get("format") or "").lower() == "csv"
        is_quickcharts = "quickcharts" in name or Path(url).name.startswith("qc_")
        if is_csv and url and not is_quickcharts:
            candidates.append(url)
    if not candidates:
        raise RuntimeError("No full CSV resource found in the HDX dataset listing")
    return candidates[0]


def download_csv(dest_dir: Path) -> Path:
    """Download the CSV into dest_dir, keeping the original file (timestamped)."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    session = _session()
    url = find_csv_url(session)
    log.info("Downloading %s", url)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    target = dest_dir / f"wfp_food_prices_ken_{stamp}.csv"
    partial = target.with_suffix(".part")
    with session.get(url, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        with open(partial, "wb") as fh:
            fh.writelines(resp.iter_content(chunk_size=1 << 16))
    partial.rename(target)
    return target


def parse_prices(path: Path) -> tuple[pd.DataFrame, int, int]:
    """Return (clean rows, records retrieved, validation failures)."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing expected columns: {sorted(missing)}")

    # WFP files carry a second row of HXL tags (#date, #value ...). Drop it.
    df = df[~df["date"].str.startswith("#")].copy()
    retrieved = len(df)

    for col in df.columns:
        df[col] = df[col].str.strip()

    dates = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    price = pd.to_numeric(df["price"], errors="coerce")
    usd = pd.to_numeric(df["usdprice"], errors="coerce")
    valid = (
        dates.notna()
        & price.gt(0)
        & (df["market"] != "")
        & (df["commodity"] != "")
        & (df["unit"] != "")
    )
    failures = int((~valid).sum())

    # A blank admin2 sometimes has the county in brackets in the market name,
    # e.g. "Hola (Tana River)".
    in_brackets = df["market"].str.extract(r"\(([^)]+)\)", expand=False).fillna("")
    county = df["admin2"].where(df["admin2"] != "", in_brackets).replace(COUNTY_ALIASES)
    county = county.where(county != "", "Unknown")

    out = pd.DataFrame(
        {
            "county": county,
            "market": df["market"],
            "latitude": pd.to_numeric(df["latitude"], errors="coerce"),
            "longitude": pd.to_numeric(df["longitude"], errors="coerce"),
            "category": df["category"],
            "commodity": df["commodity"],
            "unit": df["unit"],
            "price_type": df["pricetype"].str.lower().replace("", "retail"),
            "currency": df["currency"].str.upper().replace("", "KES"),
            "observed_on": dates.dt.date,
            "price": price.round(4),
            "price_usd": usd.round(4),
        }
    )[valid]

    out = out.drop_duplicates(
        subset=["county", "market", "commodity", "observed_on", "unit", "price_type"],
        keep="last",
    )
    return out.reset_index(drop=True), retrieved, failures
