# Energy Hub — 2024-Q1 Research Dataset

**기간**: 2024-01-01 ~ 2024-03-31 (열수요는 2023-Q1)

## 테이블 목록

| # | 테이블 | 단위 | 행수 | 출처 |
|---|---|---|---|---|
| 1 | `demand_5min` | 5분 | 26,171 | demand-postgres (원본) |
| 2 | `demand_1h` | 1시간 (5min→1h 집계) | 2,184 | demand-postgres |
| 3 | `demand_weather_1h` | 1시간 × 95개소 | 203,256 | demand-postgres (ASOS 실측) |
| 4 | `heat_demand_2023Q1` | 1시간 × 19지사 | 41,040 | demand-postgres (2023-Q1) |
| 5 | `nambu_generation` | 1시간 × 21개소 | 26,016 | pv-data-postgres |
| 6 | `namdong_generation` | 1시간 × 23개소 | 50,232 | pv-data-postgres |
| 7 | `wind_hangyoung` | 1시간 × 1개소 | 4,368 | pv-data-postgres |
| 8 | `wind_namdong` | 1시간 × 5개소 | 10,920 | pv-data-postgres |
| 9 | `nambu_plants` | 메타 | 58 | pv-data-postgres (좌표·용량) |
| 10 | `namdong_plants` | 메타 | 23 | pv-data-postgres (좌표·용량) |
| 11 | `weather_aws_seongnam` | 1시간 × 1개소 | 2,184 | NAS / KMA AWS (성남, 지점 572) |
| 12 | `fuel_price_hourly` | 1시간 (월값 broadcast) | 2,184 | NAS / EPSIS 5종 연료비 + LNG |

## 사용 예시

### Parquet (pandas/polars)
```python
import polars as pl
df = pl.read_parquet('parquet/demand_5min.parquet')
```

### DuckDB (SQL JOIN 한 번에)
```python
import duckdb
con = duckdb.connect('energy_q1_2024.duckdb')
con.sql('''
  SELECT d.timestamp, d.current_demand, w.temperature
  FROM demand_1h d
  JOIN demand_weather_1h w USING(timestamp)
  WHERE w.station_name = '서울'
''').show()
```