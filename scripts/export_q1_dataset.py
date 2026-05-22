"""
연구용 통합 데이터 추출 — 2024-Q1 (열수요만 2023-Q1)

출처
----
- demand-postgres  (host=localhost port=5433)  — 전국 수급·기상실측·열수요
- pv-data-postgres (host=localhost port=5436)  — 발전량 + plant 메타
- NAS              (/home/dlwhdtmd/seri-data/Oil+weather/...)  — AWS 기온·연료비

출력
----
~/db/
├── energy_q1_2024.duckdb      # 12개 테이블 통합
└── parquet/                   # 테이블별 12개 .parquet

사용
----
uv run python scripts/export_q1_dataset.py
uv run python scripts/export_q1_dataset.py --skip-duckdb
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path

import duckdb
import polars as pl
import psycopg2

# ───────────────────────────────────────────────────────────────────────────
# 경로
# ───────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]   # ~/db
PARQUET_DIR = PROJECT_ROOT / "parquet"
DUCKDB_PATH = PROJECT_ROOT / "energy_q1_2024.duckdb"

PERIOD_START = "2024-01-01"
PERIOD_END = "2024-04-01"
HEAT_START = "2023-01-01"
HEAT_END = "2023-04-01"

DEMAND_DSN = "host=localhost port=5433 user=demand password=demand dbname=demand"
PV_DSN = "host=localhost port=5436 user=pv password=pv dbname=pv"

NAS_ROOT = Path("/home/dlwhdtmd/seri-data/Oil+weather")
WEATHER_AWS_PATH = NAS_ROOT / "Oil+weather" / "weather_all.csv"
FUEL_HOURLY_PATH = NAS_ROOT / "EPSIS_FuelPrice" / "FuelPRICE_byHOUR.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("export")


# ───────────────────────────────────────────────────────────────────────────
# 추출기
# ───────────────────────────────────────────────────────────────────────────

def fetch_pg(dsn: str, query: str, params: tuple = ()) -> pl.DataFrame:
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
    return pl.DataFrame(rows, schema=cols, orient="row")


def extract_demand_postgres() -> dict[str, pl.DataFrame]:
    log.info("demand-postgres 추출 시작")
    tables = {}

    tables["demand_5min"] = fetch_pg(
        DEMAND_DSN,
        """
        SELECT timestamp, current_demand, current_supply, supply_capacity,
               supply_reserve, reserve_rate, operation_reserve, is_holiday, day_type
        FROM demand_5min
        WHERE timestamp >= %s AND timestamp < %s
        ORDER BY timestamp
        """,
        (PERIOD_START, PERIOD_END),
    )
    log.info("  demand_5min: %d행", tables["demand_5min"].height)

    tables["demand_1h"] = fetch_pg(
        DEMAND_DSN,
        """
        SELECT date_trunc('hour', timestamp) AS timestamp,
               AVG(current_demand)    AS current_demand,
               AVG(current_supply)    AS current_supply,
               AVG(supply_capacity)   AS supply_capacity,
               AVG(supply_reserve)    AS supply_reserve,
               AVG(reserve_rate)      AS reserve_rate,
               AVG(operation_reserve) AS operation_reserve,
               BOOL_OR(is_holiday)    AS is_holiday,
               MAX(day_type)          AS day_type
        FROM demand_5min
        WHERE timestamp >= %s AND timestamp < %s
        GROUP BY 1
        ORDER BY 1
        """,
        (PERIOD_START, PERIOD_END),
    )
    log.info("  demand_1h (5min→1h): %d행", tables["demand_1h"].height)

    tables["demand_weather_1h"] = fetch_pg(
        DEMAND_DSN,
        """
        SELECT timestamp, station_name, temperature, humidity,
               demand_avg, is_holiday, day_type
        FROM demand_weather_1h
        WHERE timestamp >= %s AND timestamp < %s
        ORDER BY timestamp, station_name
        """,
        (PERIOD_START, PERIOD_END),
    )
    log.info("  demand_weather_1h: %d행", tables["demand_weather_1h"].height)

    tables["heat_demand_2023Q1"] = fetch_pg(
        DEMAND_DSN,
        """
        SELECT timestamp, branch, wind_direction, wind_speed,
               rain_daily, rain_1h, humidity, temperature_chill, temperature,
               year, month, day, hour, heat_demand
        FROM heat_demand
        WHERE timestamp >= %s AND timestamp < %s
        ORDER BY timestamp, branch
        """,
        (HEAT_START, HEAT_END),
    )
    log.info("  heat_demand (23Q1): %d행", tables["heat_demand_2023Q1"].height)

    return tables


def extract_pv_postgres() -> dict[str, pl.DataFrame]:
    log.info("pv-data-postgres 추출 시작")
    tables = {}

    tables["nambu_generation"] = fetch_pg(
        PV_DSN,
        """
        SELECT datetime, gencd, plant_name, hogi, generation,
               daily_total, daily_avg, daily_max, daily_min
        FROM nambu_generation
        WHERE datetime >= %s AND datetime < %s
        ORDER BY datetime, plant_name
        """,
        (PERIOD_START, PERIOD_END),
    )
    log.info("  nambu_generation: %d행", tables["nambu_generation"].height)

    tables["namdong_generation"] = fetch_pg(
        PV_DSN,
        """
        SELECT datetime, plant_name, hour, generation
        FROM namdong_generation
        WHERE datetime >= %s AND datetime < %s
        ORDER BY datetime, plant_name
        """,
        (PERIOD_START, PERIOD_END),
    )
    log.info("  namdong_generation: %d행", tables["namdong_generation"].height)

    tables["wind_hangyoung"] = fetch_pg(
        PV_DSN,
        """
        SELECT timestamp, plant_name, generation
        FROM wind_hangyoung
        WHERE timestamp >= %s AND timestamp < %s
        ORDER BY timestamp
        """,
        (PERIOD_START, PERIOD_END),
    )
    log.info("  wind_hangyoung: %d행", tables["wind_hangyoung"].height)

    tables["wind_namdong"] = fetch_pg(
        PV_DSN,
        """
        SELECT timestamp, plant_name, generation
        FROM wind_namdong
        WHERE timestamp >= %s AND timestamp < %s
        ORDER BY timestamp, plant_name
        """,
        (PERIOD_START, PERIOD_END),
    )
    log.info("  wind_namdong: %d행", tables["wind_namdong"].height)

    tables["nambu_plants"] = fetch_pg(
        PV_DSN,
        "SELECT plant_name, address, capacity, install_angle, latitude, longitude FROM nambu_plants",
    )
    log.info("  nambu_plants: %d행", tables["nambu_plants"].height)

    tables["namdong_plants"] = fetch_pg(
        PV_DSN,
        "SELECT plant_name, base_name, latitude, longitude FROM namdong_plants",
    )
    log.info("  namdong_plants: %d행", tables["namdong_plants"].height)

    return tables


def extract_nas() -> dict[str, pl.DataFrame]:
    log.info("NAS 추출 시작")
    tables = {}

    # 1) 성남 AWS 기온 (datetime: YYYYMMDDHHMM)
    df = pl.read_csv(WEATHER_AWS_PATH, schema_overrides={"datetime": pl.Utf8})
    df = df.with_columns(
        pl.col("datetime").str.strptime(pl.Datetime, "%Y%m%d%H%M").alias("ts")
    ).filter(
        (pl.col("ts") >= datetime(2024, 1, 1)) & (pl.col("ts") < datetime(2024, 4, 1))
    ).select(["ts", "temperature", "ta_avg", "ta_max", "ta_min"])
    tables["weather_aws_seongnam"] = df.sort("ts")
    log.info("  weather_aws_seongnam: %d행", df.height)

    # 2) 시간별 연료비 (LNG 포함)
    df = pl.read_csv(FUEL_HOURLY_PATH)
    df = df.with_columns(
        pl.col("time").str.strptime(pl.Datetime, "%Y-%m-%dT%H:%M:%SZ").alias("ts")
    ).filter(
        (pl.col("ts") >= datetime(2024, 1, 1)) & (pl.col("ts") < datetime(2024, 4, 1))
    ).select(["ts", "nuclear", "soft_fuel", "hard_fuel", "oil", "LNG"])
    tables["fuel_price_hourly"] = df.sort("ts")
    log.info("  fuel_price_hourly: %d행", df.height)

    return tables


# ───────────────────────────────────────────────────────────────────────────
# 출력
# ───────────────────────────────────────────────────────────────────────────

def write_parquet(tables: dict[str, pl.DataFrame]) -> None:
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        path = PARQUET_DIR / f"{name}.parquet"
        df.write_parquet(path, compression="zstd")
        log.info("  → %s (%d행, %.1f KB)", path.name, df.height, path.stat().st_size / 1024)


def write_duckdb(tables: dict[str, pl.DataFrame]) -> None:
    if DUCKDB_PATH.exists():
        DUCKDB_PATH.unlink()
    con = duckdb.connect(str(DUCKDB_PATH))
    for name, df in tables.items():
        con.register("tmp_df", df.to_arrow())
        con.execute(f'CREATE TABLE "{name}" AS SELECT * FROM tmp_df')
        con.unregister("tmp_df")
        log.info("  → duckdb.%s", name)
    con.close()
    log.info("  duckdb 파일: %.1f KB", DUCKDB_PATH.stat().st_size / 1024)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-duckdb", action="store_true")
    parser.add_argument("--skip-parquet", action="store_true")
    args = parser.parse_args()

    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)

    tables: dict[str, pl.DataFrame] = {}
    tables.update(extract_demand_postgres())
    tables.update(extract_pv_postgres())
    tables.update(extract_nas())

    log.info("총 %d개 테이블, %d행", len(tables), sum(df.height for df in tables.values()))

    if not args.skip_parquet:
        log.info("Parquet 출력")
        write_parquet(tables)
    if not args.skip_duckdb:
        log.info("DuckDB 출력")
        write_duckdb(tables)
    log.info("완료 — %s", PROJECT_ROOT)


if __name__ == "__main__":
    main()
