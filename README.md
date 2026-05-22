# Energy Hub — 2024-Q1 Research Dataset

전국 전력수급 · 기상 · 발전량(PV/풍력) · 열수요 · 연료비를 한곳에 모은 연구용 데이터셋.
**2024-01-01 ~ 2024-03-31** 기간 (열수요만 데이터 가용 사유로 **2023-Q1**).

---

## 📦 무엇이 들어있나

```
~/db/
├── README.md                  ← 지금 보고 있는 파일
├── DATA_README.md             ← 테이블/컬럼 상세 명세
├── pyproject.toml             ← uv 프로젝트 정의 (의존성 명세)
├── uv.lock                    ← 고정된 패키지 버전
│
├── energy_q1_2024.duckdb      ← 12개 테이블 통합 DB (5 MB) ★권장
├── parquet/                   ← 테이블별 12개 .parquet (2 MB)
├── csv/                       ← 테이블별 12개 .csv (23 MB, 엑셀용)
│
└── scripts/
    ├── export_q1_dataset.py   ← DB/NAS → parquet+duckdb 재생성
    └── export_to_csv.py       ← duckdb → csv 재생성
```

### 데이터 12개 테이블 한눈에

| # | 테이블 | 행수 | 단위 / 출처 |
|---|---|---:|---|
| 1 | `demand_5min` | 26,171 | 5분 전국 전력수급 |
| 2 | `demand_1h` | 2,184 | 1시간 집계본 |
| 3 | `demand_weather_1h` | 203,256 | 1시간 × 95개 ASOS 관측소 (기온·습도) |
| 4 | `heat_demand_2023Q1` | 41,040 | 1시간 × 19지사 열수요 (**2023-Q1**) |
| 5 | `nambu_generation` | 26,016 | 1시간 × 21개소 남부발전 PV |
| 6 | `namdong_generation` | 50,232 | 1시간 × 23개소 남동발전 PV |
| 7 | `wind_hangyoung` | 4,368 | 1시간 한경풍력 1개소 |
| 8 | `wind_namdong` | 10,920 | 1시간 남동풍력 5개소 |
| 9 | `weather_aws_seongnam` | 2,184 | 1시간 성남 AWS 기온 |
| 10 | `fuel_price_hourly` | 2,184 | 1시간 5종 연료비 (LNG 포함) |
| 11 | `nambu_plants` | 58 | PV 메타 (좌표·용량) |
| 12 | `namdong_plants` | 23 | PV 메타 (좌표·용량) |

---

## 🚀 빠른 시작 — 5분 안에 데이터 보기

### 가장 간단한 방법: CSV를 엑셀에서 바로 열기

`csv/` 폴더 안 12개 `.csv` 파일을 더블클릭. utf-8-sig BOM 적용돼 있어서 **한글 깨짐 없음**.

### Python으로 보고 싶다면 → 아래 "환경 설정" 으로

---

## 🛠️ 환경 설정 (Python/SQL 분석용)

이 프로젝트는 [`uv`](https://docs.astral.sh/uv/)를 패키지 매니저로 씁니다. pip/conda보다 10~100배 빠르고, `pyproject.toml` 하나로 환경이 완전히 복원됩니다.

### Step 1 — uv 설치 (처음 한 번만)

#### macOS / Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
설치 후 쉘 재시작 또는:
```bash
source $HOME/.local/bin/env       # bash/zsh
# 또는
exec $SHELL
```

#### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 이미 brew/pipx가 있다면
```bash
brew install uv             # macOS
pipx install uv             # 어디서나
```

#### 설치 확인
```bash
uv --version
# uv 0.5.x  → 설치 OK
```

### Step 2 — 이 프로젝트 환경 만들기

```bash
cd ~/db
uv sync
```

이 한 줄이 하는 일:
1. `pyproject.toml`에서 필요한 Python 버전(3.12) 자동 다운로드 (없으면)
2. `.venv/` 가상환경 생성
3. duckdb, polars, pandas, pyarrow, psycopg2-binary 설치

**30초 안에 끝남.** `pip install`처럼 한참 안 기다림.

### Step 3 — 실행

```bash
# 방법 A: uv run으로 매번 실행 (가상환경 활성화 불필요)
uv run python -c "import duckdb; print(duckdb.connect('energy_q1_2024.duckdb').sql('SHOW TABLES').df())"

# 방법 B: 가상환경 켜고 평소처럼
source .venv/bin/activate         # macOS/Linux
.venv\Scripts\activate            # Windows
python                            # 또는 jupyter, ipython 등
```

---

## 📊 사용 예시

### ① DuckDB로 SQL 쿼리 (가장 추천)

```python
import duckdb
con = duckdb.connect("energy_q1_2024.duckdb", read_only=True)

# 1) 테이블 목록
con.sql("SHOW TABLES").show()

# 2) 시간별 수요 + 서울 기온 + LNG 가격 JOIN
con.sql("""
  SELECT d.timestamp,
         d.current_demand              AS demand_mw,
         w.temperature                 AS seoul_temp_c,
         w.humidity                    AS seoul_humid,
         f.LNG                         AS lng_price
  FROM demand_1h d
  LEFT JOIN demand_weather_1h w
    ON w.timestamp = d.timestamp AND w.station_name = '서울'
  LEFT JOIN fuel_price_hourly f
    ON f.ts = d.timestamp
  ORDER BY d.timestamp
  LIMIT 10
""").show()

# 3) PV 발전소별 일평균 (메타와 조인)
con.sql("""
  SELECT g.plant_name, p.latitude, p.longitude,
         AVG(g.generation) AS avg_gen_mw
  FROM nambu_generation g
  LEFT JOIN nambu_plants p USING(plant_name)
  GROUP BY 1, 2, 3
  ORDER BY avg_gen_mw DESC
  LIMIT 5
""").show()
```

### ② Polars (NumPy/pandas보다 빠른 데이터프레임)

```python
import polars as pl

demand = pl.read_parquet("parquet/demand_1h.parquet")
weather = pl.read_parquet("parquet/demand_weather_1h.parquet")

# 서울만 필터링 후 demand와 join
seoul = weather.filter(pl.col("station_name") == "서울")
merged = demand.join(seoul, on="timestamp", how="left")
print(merged.head())
```

### ③ Pandas (익숙한 API)

```python
import pandas as pd

df = pd.read_parquet("parquet/demand_5min.parquet")
df["timestamp"] = pd.to_datetime(df["timestamp"])
df.set_index("timestamp")["current_demand"].plot()
```

### ④ R / Excel / 기타 도구

- **R**: `arrow::read_parquet("parquet/demand_1h.parquet")` 또는 `read.csv("csv/demand_1h.csv", fileEncoding="UTF-8")`
- **Excel**: `csv/*.csv` 더블클릭 (BOM 적용돼서 한글 OK)
- **Tableau / Power BI**: parquet 또는 csv 그대로 import

---

## 🔁 데이터 재생성 (옵션)

### CSV만 다시 만들기 (duckdb만 있으면 됨)

```bash
# 전체 12개 다시
uv run python scripts/export_to_csv.py

# 일부만
uv run python scripts/export_to_csv.py --only demand_5min,demand_weather_1h

# gzip 압축 (23 MB → ~5 MB)
uv run python scripts/export_to_csv.py --gzip
```

### DB 처음부터 재추출 (서버에서만 가능)

```bash
uv run python scripts/export_q1_dataset.py
```

**주의**: 이 스크립트는 같은 호스트(`192.9.66.97`)에서 아래에 접근 가능해야 동작합니다.
- Docker 컨테이너: `demand-postgres:5433`, `pv-data-postgres:5436`
- NAS 마운트: `/home/dlwhdtmd/seri-data/Oil+weather/`

타 머신(맥북 등)에 옮겨서 쓸 때는 **재추출 불가**. 이미 있는 duckdb/parquet/csv만 읽으세요.

---

## 🆘 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `uv: command not found` | 설치 후 쉘 재시작 안 함 → `source ~/.local/bin/env` 또는 새 터미널 |
| `uv sync` 시 Python 3.12 다운로드가 느림 | 첫 실행만 그럼. 한 번 받으면 캐시됨 |
| `psycopg2-binary` 설치 실패 (Mac M1) | `brew install postgresql` 후 재시도, 또는 `uv add psycopg2-binary --no-binary` |
| 엑셀에서 한글이 깨짐 | CSV는 utf-8-sig라 정상. 엑셀이 utf-8 모드면 OK. 안 되면 Numbers/LibreOffice로 시도 |
| DuckDB가 "database is locked" | 같은 파일을 다른 프로세스가 쓰기 모드로 열고 있음. `read_only=True` 사용 |
| 스크립트 실행 시 `connection refused` | Docker DB 컨테이너가 안 떠 있거나 다른 머신에서 실행 중. 서버에서만 동작 |

---

## 📋 디렉토리 / 파일 권한

- 데이터 파일: **read-only로 사용 권장**. 변경하지 마세요 (다음 재생성 때 덮어쓰여짐).
- 스크립트 수정 OK. 새 추출 기간/소스 추가하시려면 `scripts/export_q1_dataset.py`의 `PERIOD_START`/`PERIOD_END` 등 변수 수정.

---

## 📞 문의 / 다음 단계

- 데이터 명세 자세히: `DATA_README.md`
- 결손 데이터 (풍력 SCADA 5분, 단기예보 등) 추가 요청은 별도 협의

작성: 2026-05-22 (자동 생성)
