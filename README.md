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

| # | 테이블 | 행수 | 단위 / 출처 | 기간 |
|---|---|---:|---|---|
| 1 | `demand_5min` | 26,171 | 5분 전국 전력수급 (KPX) | 24-01-01 ~ 24-03-31 |
| 2 | `demand_1h` | 2,184 | 1시간 집계본 (5분 → 시간 평균) | 24-01-01 ~ 24-03-31 |
| 3 | `demand_weather_1h` | 203,256 | 1시간 × 95개 ASOS 관측소 (기온·습도) | 24-01-01 ~ 24-03-31 |
| 4 | `heat_demand_2023Q1` | 41,040 | 1시간 × 19지사 열수요 | **23-01-01 ~ 23-03-31** |
| 5 | `nambu_generation` | 26,016 | 1시간 × 11개 남부발전 PV 사이트 | 24-01-01 ~ 24-03-31 |
| 6 | `namdong_generation` | 50,232 | 1시간 × 23개 남동발전 PV 사이트 | 24-01-01 ~ 24-03-31 |
| 7 | `wind_hangyoung` | 4,368 | 1시간 한경풍력 1개소 | 24-01-01 ~ 24-03-31 |
| 8 | `wind_namdong` | 10,920 | 1시간 남동풍력 5개소 | 24-01-01 ~ 24-03-31 |
| 9 | `weather_aws_seongnam` | 2,184 | 1시간 성남(지점 572) AWS 기온 | 24-01-01 ~ 24-03-31 |
| 10 | `fuel_price_hourly` | 2,184 | 1시간 5종 연료비 (원자력·유연탄·무연탄·유류·**LNG**) | 24-01-01 ~ 24-03-31 |
| 11 | `nambu_plants` | 58 | 남부발전 PV 사이트 메타 (좌표·용량·각도) | — |
| 12 | `namdong_plants` | 23 | 남동발전 PV 사이트 메타 (좌표) | — |

> 모든 시간 컬럼은 KST(Asia/Seoul) 로컬타임 기준. JOIN 키는 `timestamp` 또는 `ts` (1시간 단위 정렬).

---

## 📚 데이터 상세

### 1. `demand_5min` / `demand_1h` — 전국 전력수급

**출처**: KPX 전력거래소 5분 단위 수급 데이터
**기간**: 2024-01-01 00:00 ~ 2024-03-31 23:55 (5분), 23:00 (1시간 집계)

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `timestamp` | TIMESTAMP | 시각 (KST) |
| `current_demand` | DOUBLE | 현재 수요 (MW) |
| `current_supply` | DOUBLE | 현재 공급 (MW) |
| `supply_capacity` | DOUBLE | 공급능력 (MW) |
| `supply_reserve` | DOUBLE | 공급예비력 (MW) |
| `reserve_rate` | DOUBLE | 예비율 (%) |
| `operation_reserve` | DOUBLE | 운영예비력 (MW) |
| `is_holiday` | BOOLEAN | 휴일 여부 |
| `day_type` | BIGINT | 요일 타입 (0=평일, 1=토, 2=일/공휴일) |

`demand_1h`는 5분 데이터를 시간 단위로 평균 집계한 것 — 다른 1시간 테이블과 JOIN하기 편하라고 추가.

---

### 2. `demand_weather_1h` — 시간별 기상 실측 (95개 ASOS)

**출처**: 기상청 ASOS 종관관측소 95개소 시간별 자료
**행수**: 203,256 (= 95 × 24 × 91일, 결측 일부 포함)

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `timestamp` | TIMESTAMP | 시각 (KST) |
| `station_name` | VARCHAR | 관측소명 (한글) |
| `temperature` | DOUBLE | 기온 (°C) |
| `humidity` | DOUBLE | 상대습도 (%) |
| `demand_avg` | DOUBLE | 같은 시각 전국수요 평균 (조인 편의용) |
| `is_holiday`, `day_type` | — | 동일 |

**관측소 95개소**: 서울 · 인천 · 수원 · 강릉 · 대전 · 대구 · 부산 · 광주 · 제주 · 울릉도 · 백령도 · 흑산도 · 강진군 · 거제 · 거창 · 경주시 · 고산 · 고창 · 고창군 · 고흥 · 광양시 · 구미 · 군산 · 금산 · 김해시 · 남원 · 남해 · 대관령 · 동두천 · 동해 · 목포 · 문경 · 밀양 · 보령 · 보성군 · 보은 · 봉화 · 부안 · 부여 · 북강릉 · 북창원 · 북춘천 · 산청 · 상주 · 서귀포 · 서산 · 성산 · 세종 · 속초 · 순창군 · 순천 · 안동 · 양산시 · 양평 · 여수 · 영광군 · 영덕 · 영월 · 영주 · 영천 · 완도 · 울산 · 울진 · 원주 · 의령군 · 의성 · 이천 · 임실 · 장수 · 장흥 · 전주 · 정선군 · 정읍 · 제천 · 진도군 · 진주 · 창원 · 천안 · 철원 · 청송군 · 청주 · 추풍령 · 춘천 · 충주 · 태백 · 통영 · 파주 · 포항 · 함양군 · 합천 · 해남 · 홍성 · 홍천 · 강화

---

### 3. `heat_demand_2023Q1` — 시간별 지역난방 열수요 (19개 지사)

**출처**: 한국지역난방공사 19개 지사
**기간**: ⚠️ **2023-01-01 ~ 2023-03-31** (2024년 데이터는 미적재 상태라 23년 동기로 대체)
**행수**: 41,040 (= 19 × 24 × 90일)

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `timestamp` | TIMESTAMP | 시각 (KST) |
| `branch` | VARCHAR | 지사명 |
| `wind_direction`, `wind_speed` | DOUBLE | 풍향·풍속 (해당 지사 인근) |
| `rain_daily`, `rain_1h` | DOUBLE | 일·시간 강수 (mm) |
| `humidity` | DOUBLE | 습도 (%) |
| `temperature_chill` | DOUBLE | 체감온도 (°C) |
| `temperature` | DOUBLE | 기온 (°C) |
| `year`, `month`, `day`, `hour` | BIGINT | 분리 컬럼 (편의용) |
| `heat_demand` | DOUBLE | **열수요 (Gcal/h)** ← 타깃 변수 |

**19개 지사**: 강남 · 고양 · 광교 · 광주전남 · 김해 · 대구 · 동탄 · 분당 · 삼송 · 세종 · 수원 · 양산 · 용인 · 중앙 · 청주 · 파주 · 판교 · 평택 · 화성

---

### 4. `nambu_generation` — 남부발전 PV 시간별 발전량

**출처**: 한국남부발전 자체 모니터링 시스템
**사이트 수**: 11개 (`hogi` 호기까지 합치면 21개 단위)
**행수**: 26,016

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `datetime` | TIMESTAMP | 시각 |
| `gencd` | VARCHAR | 발전기 코드 |
| `plant_name` | VARCHAR | 발전소명 |
| `hogi` | BIGINT | 호기 번호 |
| `generation` | DOUBLE | 발전량 (kWh) |
| `daily_total/avg/max/min` | DOUBLE | 일별 합/평/최대/최소 |

**11개 PV 사이트**: 남제주소내 · 부산복합 자재창고 · 신인천 1·2단계주차장 · 신인천 북측부지 · 신인천 소내 · 신인천 주차장 · 부산본부 · 부산수처리장 · 부산운동장 · 신인천전망대 · 신인천해수구취수구

→ 좌표·용량은 `nambu_plants` 참조 (58행 — 회사 본부 외 다른 발전소도 포함)

---

### 5. `namdong_generation` — 남동발전 PV 시간별 발전량

**출처**: 한국남동발전 자체 모니터링 시스템
**사이트 수**: 23개
**행수**: 50,232

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `datetime` | TIMESTAMP | 날짜 (시각 부분은 00:00, 시간은 `hour` 컬럼) |
| `plant_name` | VARCHAR | 발전소명 |
| `hour` | BIGINT | 0~23 시간 |
| `generation` | DOUBLE | 발전량 (kWh) |

⚠️ **datetime + hour 분리 구조** — 다른 테이블과 시간 매칭하려면:
```sql
SELECT datetime + INTERVAL (hour) HOUR AS ts, generation FROM namdong_generation
```

**23개 PV 사이트**: 경상대 · 고흥만 수상 · 광양항세방 · 구미 · 두산엔진MG · 삼천포(#5_1, #5_2, #6, _1~_4) · 여수 · 영동 · 영흥(#3_1~3_3, #5, _1, _2) · 예천 · 탑선(_1, _3)

→ 좌표는 `namdong_plants` 참조 (23행, plant_name 키)

---

### 6. `wind_hangyoung`, `wind_namdong` — 풍력 시간별 발전량

| 테이블 | 발전소 | 행수 |
|---|---|---:|
| `wind_hangyoung` | 한경풍력 (제주) | 4,368 |
| `wind_namdong` | 군위 화산풍력 1 · 삼천포풍력 1 · 어음풍력 1 · 영흥풍력 1 · 영흥풍력 2 | 10,920 |

공통 컬럼: `timestamp`, `plant_name`, `generation` (kWh)

> 요청 5개소 중 4개가 남동, 1개가 한경 → 도합 6개소. `wind_seobu`는 2023-06에서 데이터 끊겨 제외됨.

---

### 7. `weather_aws_seongnam` — 성남 AWS 기온 (단일 지점)

**출처**: 기상청 KMA AWS API (지점 572 — 성남)
**용도**: ASOS와 별개로 AWS 측정값이 필요한 경우

| 컬럼 | 설명 |
|---|---|
| `ts` | 시각 |
| `temperature` | 측정 시각 기온 |
| `ta_avg/max/min` | 시간 평균/최고/최저 |

---

### 8. `fuel_price_hourly` — 시간별 발전 연료비 (LNG 포함)

**출처**: EPSIS 전력통계정보시스템 (월 단위 값을 시간 단위로 broadcast)

| 컬럼 | 설명 | 단위 |
|---|---|---|
| `ts` | 시각 | — |
| `nuclear` | 원자력 | 원/kWh |
| `soft_fuel` | 유연탄 | 원/kWh |
| `hard_fuel` | 무연탄 | 원/kWh |
| `oil` | 유류 | 원/kWh |
| **`LNG`** | LNG (액화천연가스) | 원/kWh |

⚠️ 실제는 **월 단위 정산단가**가 시간으로 broadcast된 값 — 같은 월 내 시간별 차이는 없음. 시계열 변동이 아닌 월 평균 비용을 보는 용도.

---

### 9. `nambu_plants`, `namdong_plants` — PV 발전소 메타

| 테이블 | 행수 | 주요 컬럼 |
|---|---:|---|
| `nambu_plants` | 58 | `plant_name`, `address`, `capacity`(string), `install_angle`, `latitude`, `longitude` |
| `namdong_plants` | 23 | `plant_name`, `base_name`, `latitude`, `longitude` |

⚠️ `capacity`/`install_angle`은 문자열 (예: `"196kW 모듈 :250W x 784 인버터 : 100kW x 2EA"`). 숫자 파싱은 사용자가 처리.

`namdong_plants`는 `namdong_generation.plant_name`과 1:1 매칭 가능.
`nambu_plants`는 발전소가 58개로 더 많아 `nambu_generation.plant_name`(11개)의 슈퍼셋 — LEFT JOIN 권장.

---

## ⚠️ 알려진 제약

| 항목 | 상태 |
|---|---|
| **풍력 SCADA 5분 2개소** | 미포함 — DB·NAS 어디에도 없음 (별도 소스 필요) |
| **단기예보 기온·습도** | 미포함 — KMA SHRT-FCST API 별도 호출 필요 |
| **PV 53개소 (요청)** | 보유 44개소 (남부 11 + 남동 23 + 메타 58/23 차이) — 일부 미일치 |
| **풍력 5개소 (요청)** | 보유 6개소 (한경 1 + 남동 5) — `wind_seobu`는 23-06에서 끊김 |

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
