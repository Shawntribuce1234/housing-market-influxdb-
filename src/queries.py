"""
running examples sql queries through influxdb client to show
different capability of the query language.
"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from influxdb_client_3 import InfluxDBClient3

# Config
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

INFLUX_HOST = os.getenv("INFLUX_HOST", "http://localhost:8181")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_DATABASE = os.getenv("INFLUX_DATABASE", "housing")


def get_client():
    """Open a client connection to the local InfluxDB 3 Core instance."""
    return InfluxDBClient3(host=INFLUX_HOST, token=INFLUX_TOKEN, database=INFLUX_DATABASE)


def run(client, sql):
    """executing a SQL query and return the result as a pd df"""
    return client.query(sql).to_pandas()


def example_select(client):
    """select ex: grabing the 5 most recent case_shiller points"""
    sql = """
        SELECT time, value
        FROM housing
        WHERE series = 'case_shiller'
        ORDER BY time DESC
        LIMIT 5
    """
    return run(client, sql)


def example_count_by_series(client):
    """aggregation w COUNT + GROUP BY and returning how many points loaded for each series"""
    sql = """
        SELECT series, COUNT(*) AS n
        FROM housing
        GROUP BY series
    """
    return run(client, sql)


def example_yearly_average(client):
    """time-bucketed downsampling w date_bin getting average mortgage rate per year"""
    sql = """
        SELECT date_bin(INTERVAL '1 year', time) AS year,
               AVG(value) AS avg_value
        FROM housing
        WHERE series = 'mortgage_30yr'
        GROUP BY year
        ORDER BY year
    """
    return run(client, sql)


def example_join_series(client):
    """self joining on time where we are puting case_shiller and mortgage_30yr side by side for comparison"""
    sql = """
        SELECT cs.time AS time,
               cs.value AS case_shiller,
               mr.value AS mortgage_30yr
        FROM housing AS cs
        JOIN housing AS mr
          ON cs.time = mr.time
        WHERE cs.series = 'case_shiller'
          AND mr.series = 'mortgage_30yr'
        ORDER BY time
        LIMIT 10
    """
    return run(client, sql)


def example_moving_average(client):
    """using window func ex: getitng 12-month moving average over the ordered case_shiller series"""
    sql = """
        SELECT time,
               value,
               AVG(value) OVER (
                   ORDER BY time
                   ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
               ) AS moving_avg_12mo
        FROM housing
        WHERE series = 'case_shiller'
        ORDER BY time
        LIMIT 20
    """
    return run(client, sql)


def example_inspect_schema(client):
    """schema inspection through information_schema and listing the housing tables columns and types"""
    sql = """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'housing'
    """
    return run(client, sql)


def query_all_joined(client):
    """pulling all 3 series into one df for analysis"""
    frames = {}
    for tag in ("case_shiller", "mortgage_30yr", "unemployment"):
        df = run(client, f"""
            SELECT time, value
            FROM housing
            WHERE series = '{tag}'
            ORDER BY time
        """)
        frames[tag] = df.set_index("time")["value"]
    wide = pd.DataFrame(frames).sort_index()
    return wide


def main():
    with get_client() as client:
        print("Example 1: basic select (latest 5 Case-Shiller)")
        print(example_select(client))

        print("Example 2: count by series")
        print(example_count_by_series(client))

        print("Example 3: yearly average mortgage rate")
        print(example_yearly_average(client))

        print("Example 4: join Case-Shiller + mortgage rate")
        print(example_join_series(client))

        print("Example 5: 12-month moving average")
        print(example_moving_average(client))

        print("Example 6: schema inspection")
        print(example_inspect_schema(client))


if __name__ == "__main__":
    main()