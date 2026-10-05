r"""
pulling FRED housing/macro series and writing them into InfluxDB 3 Core

to start server: C:\influxdb3\influxdb3.exe serve --node-id=local01 --object-store=file --data-dir C:\Users\colin\influxdb3-data
this needs to run in its own terminal

to drop and recreate db to not create dupe points:
C:\influxdb3\influxdb3.exe delete database housing --host http://localhost:8181 --token apiv3_YOUR_ACTUAL_TOKEN_HERE
C:\influxdb3\influxdb3.exe create database housing --host http://localhost:8181 --token apiv3_YOUR_ACTUAL_TOKEN_HERE
"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from fredapi import Fred
from influxdb_client_3 import InfluxDBClient3, Point

# Config
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# u need to make ur own .env file w these keys 
FRED_API_KEY = os.getenv("FRED_API_KEY")
INFLUX_HOST = os.getenv("INFLUX_HOST", "http://localhost:8181")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_DATABASE = os.getenv("INFLUX_DATABASE", "housing")

SERIES = {
    "CSUSHPINSA": "case_shiller",
    "MORTGAGE30US": "mortgage_30yr",
    "UNRATE": "unemployment",
}

START_DATE = "2000-01-01"

DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


def fetch_series(fred, series_id):
    """pulling a single FRED series and resampling to monthly"""
    raw = fred.get_series(series_id, observation_start=START_DATE)
    monthly = raw.resample("MS").mean().dropna()
    monthly.name = series_id
    return monthly


def write_to_influx(client, series_tag, monthly):
    """
    writing one monthly series to InfluxDB as points
    returns the number of points written
    """
    points = []
    for ts, val in monthly.items():
        point = (
            Point("housing")
            .tag("series", series_tag)
            .field("value", float(val))
            .time(ts)
        )
        points.append(point)

    client.write(record=points)
    return len(points)


def main():
    fred = Fred(api_key=FRED_API_KEY)

    snapshot = {}

    with InfluxDBClient3(
        host=INFLUX_HOST,
        token=INFLUX_TOKEN,
        database=INFLUX_DATABASE,
    ) as client:
        for fred_id, tag in SERIES.items():
            print(f"fetching {fred_id} ({tag})", end=" ", flush=True)
            series = fetch_series(fred, fred_id)
            n = write_to_influx(client, tag, series)
            snapshot[tag] = series
            print(f"wrote {n} points from ({series.index.min().date()} to {series.index.max().date()})")

    wide = pd.DataFrame(snapshot)
    snapshot_path = DATA_DIR / "housing_snapshot.parquet"
    wide.to_parquet(snapshot_path)
    print(f"\nSaved snapshot: {snapshot_path}  shape={wide.shape}")


if __name__ == "__main__":
    main()