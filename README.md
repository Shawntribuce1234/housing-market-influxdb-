# housing-market-influxdb
# U.S. Housing Market Analysis with InfluxDB

A Python and SQL project exploring U.S. housing and economic time series with InfluxDB 3 Core. The workflow retrieves three FRED series, aligns them to monthly timestamps, writes them to a time-series database, and produces visualizations of long-term trends.

Completed for **DS4300, Homework 5, at Northeastern University**, this group project demonstrates API ingestion, time-series data modeling, SQL queries, Pandas transformations, and Matplotlib visualization.

## Project Overview

The project examines the Case-Shiller National Home Price Index alongside 30-year mortgage rates and unemployment. Its focus is a working database and analysis workflow: retrieving observations, representing them as timestamped records, querying them, and comparing their historical patterns.

The included report and slides discuss the housing downturn following the mid-2000s peak, the subsequent recovery, and changes around the COVID period. The code provides descriptive visualizations; it does not fit predictive models, estimate causal effects, or calculate formal correlation statistics.

## Repository Structure

```text
housing-market-influxdb/
├── README.md
├── src/
│   ├── ingest.py
│   ├── queries.py
│   └── analysis.py
├── data/
│   └── housing_snapshot.parquet
├── report/
│   └── housing_market_report.pdf
└── presentation/
    └── housing_market_slides.pdf
```

The report is the original `Tracking_US_Housing_Market_Trends_with_InfluxDB.pdf`; the slides are the original `Houses_Prices_Overview_Slideshow.pdf`, renamed for readability.

The scripts resolve the project root as the parent of their containing directory. Keeping them in `src/` preserves that behavior. Generated charts are written to `outputs/figures/`.

## Data

The ingestion script requests observations beginning January 1, 2000, with no fixed end date.

| FRED identifier | Stored series tag | Description |
|---|---|---|
| `CSUSHPINSA` | `case_shiller` | Case-Shiller National Home Price Index |
| `MORTGAGE30US` | `mortgage_30yr` | 30-year fixed mortgage rate |
| `UNRATE` | `unemployment` | Unemployment rate |

Each series is resampled with `resample("MS").mean().dropna()`: observations are averaged within each month, labeled at the start of the month, and missing monthly values are removed. For the weekly mortgage series, this produces a monthly average of the available weekly observations.

The saved Parquet snapshot contains **318 rows and three numeric columns**, indexed by month from **January 2000 through June 2026**.

| Column | Non-null observations | Missing observations |
|---|---:|---:|
| `case_shiller` | 315 | 3 |
| `mortgage_30yr` | 318 | 0 |
| `unemployment` | 316 | 2 |

Series are aligned on the union of their timestamps. Missing values remain where a series has no observation for a month; the code does not interpolate or forward-fill them. A new API run may differ from this snapshot because the script has no fixed end date and does not preserve a historical data vintage.

## Pipeline and Database Model

### 1. Ingest from FRED

`src/ingest.py` loads connection settings, retrieves each series with `fredapi`, performs monthly resampling, and writes a batch of points for each series to InfluxDB.

Each point uses:

| Component | Value |
|---|---|
| Measurement | `housing` |
| Tag | `series` |
| Numeric field | `value` |
| Timestamp | Monthly observation timestamp |

After the database writes, the script combines the series into a wide Pandas DataFrame and saves `data/housing_snapshot.parquet`. This snapshot is built from the fetched series, not from a database read-back. Re-running ingestion overwrites the local snapshot.

### 2. Query with SQL

`src/queries.py` provides six examples:

1. Retrieve the five most recent Case-Shiller observations using filtering, ordering, and a limit.
2. Count observations by series with `COUNT` and `GROUP BY`.
3. Request annual mortgage-rate averages using `date_bin(INTERVAL '1 year', time)`.
4. Self-join Case-Shiller and mortgage rates on matching timestamps, returning the first ten matches.
5. Calculate a trailing average over the current row and eleven preceding Case-Shiller rows, returning the first twenty results.
6. Inspect the `housing` table through `information_schema.columns`.

The helper `query_all_joined` queries each series separately and aligns the results by timestamp in Pandas. It does not perform a three-series SQL join.

### 3. Visualize

`src/analysis.py` retrieves the wide table from InfluxDB and generates:

| Output | Contents |
|---|---|
| `outputs/figures/01_series_overview.png` | All three series divided by their first-row values and multiplied by 100. |
| `outputs/figures/02_example_analysis.png` | Case-Shiller index with a trailing 12-observation moving average. |

Both figures are saved at 150 DPI. The overview assumes the first row is January 2000 and has valid, nonzero values for all three series, as it does in the supplied snapshot.

The Pandas moving average requires twelve observations, leaving the first eleven moving-average values missing. The SQL window example averages the rows available in each window, including shorter initial windows. These two implementations therefore differ at the beginning of the series.

## Findings Supported by the Snapshot

- The Case-Shiller index rises from **100.000 in January 2000 to 329.938 in March 2026**, an increase of approximately **229.9%** between those observations.
- The price series shows a mid-2000s peak, a decline into the early 2010s, and a later recovery, consistent with the historical patterns discussed in the report.
- The unemployment series reaches **14.8% in April 2020**, creating a pronounced spike in the normalized comparison chart.

Case-Shiller is an index, not a median sale price in dollars. Its change does not establish the appreciation of a particular home. Likewise, indexing unemployment and mortgage rates to 100 shows relative changes from their starting values, not percentage-point changes or directly comparable economic effects.

## Setup and Execution

### Python dependencies

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pandas pyarrow matplotlib python-dotenv fredapi influxdb3-python
```

On Windows, activate the environment with `.venv\Scripts\activate`.

### Connection requirements

The live workflow requires a running InfluxDB 3 Core instance, a database, an authentication token, and a FRED API key. The supplied files do not install or start the database.

The scripts read the following environment variables and also load a `.env` file from the repository root when present:

| Variable | Purpose | Default in code |
|---|---|---|
| `FRED_API_KEY` | FRED API authentication for ingestion | None |
| `INFLUX_HOST` | InfluxDB connection address | `http://localhost:8181` |
| `INFLUX_TOKEN` | InfluxDB authentication | None |
| `INFLUX_DATABASE` | Database name | `housing` |

Configure the credentials locally before running the scripts. Keep `.env`, credentials, and local database storage out of the public repository.

### Run the live workflow

With the database running and the variables configured, execute these commands from the repository root:

```bash
python src/ingest.py
python src/queries.py
python src/analysis.py
```

Ingestion prints per-series counts and date ranges. The query script prints its six example results. The analysis script prints the retrieved table shape and saves the two figures.

### Inspect the included snapshot without a database

The existing analysis command always connects to InfluxDB; it has no automatic Parquet fallback. The saved data can be inspected independently:

```python
import pandas as pd

housing = pd.read_parquet("data/housing_snapshot.parquet")
print(housing.head())
print(housing.tail())
print(housing.isna().sum())
```

## Verification and Limitations

The supplied Python files were checked for syntax, and the Parquet snapshot was loaded to verify its dimensions, dates, columns, and missing values. Both plotting functions were exercised separately against the saved snapshot, without connecting to InfluxDB.

No automated test suite is included. Live FRED ingestion and InfluxDB query execution were not rerun during this review, so current server compatibility and end-to-end database behavior remain unverified. In particular, the annual time-bucketing SQL is documented as written in the source rather than presented as a newly verified query.

The scripts do not pin dependency versions, implement retry handling, or provide a snapshot-only command-line analysis mode. The latest monthly average may represent an incomplete month, and moving windows count observations rather than explicitly checking for missing calendar months.

This is a national descriptive analysis. It does not compare individual cities, measure household affordability directly, benchmark database performance, or demonstrate that changes in one economic series cause changes in another.

## Report and Presentation

- [Project report](report/housing_market_report.pdf) — database overview, setup tutorial, query examples, visualizations, and discussion.
- [Presentation slides](presentation/housing_market_slides.pdf) — project motivation, workflow, findings, and database discussion.

The PDFs are retained as original coursework artifacts. This README describes the supplied implementation and verified snapshot; broad platform comparisons in the coursework are not treated as measured project results.

## Contributors

- Abigail Eng
- Colin Hui
- Emily Quach
- Rau-Shawn Tribuce
- Tam Vu

**Course:** DS4300 — Homework 5  
**Institution:** Northeastern University  
**Report date:** June 15, 2026
