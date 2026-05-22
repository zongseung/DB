"""
energy_q1_2024.duckdb → 테이블별 CSV 변환 (utf-8-sig, 엑셀 한글 호환)

사용
----
uv run python scripts/export_to_csv.py
uv run python scripts/export_to_csv.py --only demand_5min,demand_1h
uv run python scripts/export_to_csv.py --gzip
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]   # ~/db
DUCKDB_PATH = PROJECT_ROOT / "energy_q1_2024.duckdb"
CSV_DIR = PROJECT_ROOT / "csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("csv")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="콤마구분 테이블 (기본: 전체)")
    parser.add_argument("--gzip", action="store_true", help="gzip 압축")
    args = parser.parse_args()

    if not DUCKDB_PATH.exists():
        raise SystemExit(
            f"DuckDB 파일 없음: {DUCKDB_PATH}\n"
            f"먼저 'uv run python scripts/export_q1_dataset.py' 실행하세요."
        )

    CSV_DIR.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    all_tables = [r[0] for r in con.sql("SHOW TABLES").fetchall()]

    if args.only:
        targets = [t.strip() for t in args.only.split(",")]
        unknown = set(targets) - set(all_tables)
        if unknown:
            raise SystemExit(f"존재하지 않는 테이블: {sorted(unknown)}\n사용 가능: {all_tables}")
    else:
        targets = all_tables

    log.info("%d개 테이블 CSV 변환 (gzip=%s)", len(targets), args.gzip)
    total_bytes = 0
    for tbl in targets:
        rows = con.sql(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()[0]
        out = CSV_DIR / (f"{tbl}.csv.gz" if args.gzip else f"{tbl}.csv")
        df = con.sql(f'SELECT * FROM "{tbl}"').df()
        df.to_csv(
            out,
            index=False,
            encoding="utf-8-sig",
            date_format="%Y-%m-%d %H:%M:%S",
            compression="gzip" if args.gzip else None,
        )
        size_kb = out.stat().st_size / 1024
        total_bytes += out.stat().st_size
        log.info("  → %-30s %8d행  %7.1f KB", out.name, rows, size_kb)

    con.close()
    log.info("완료 — %s (합계 %.1f MB)", CSV_DIR, total_bytes / 1024 / 1024)


if __name__ == "__main__":
    main()
