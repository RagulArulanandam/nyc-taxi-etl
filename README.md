# NYC Taxi ETL Pipeline

An end-to-end data engineering project built on NYC Yellow Taxi trip records. Covers the full pipeline from automated data extraction through transformation, storage, dashboarding, orchestration, containerisation, and CI/CD.

---

## Pipeline

```
NYC TLC Source (CloudFront)
        ↓
Automated Extraction       src/extract/
        ↓
Polars Transformations     src/transform/
        ↓
PostgreSQL                 src/load/
        ↓
Analytics Tables           sql/
        ↓
Power BI Dashboard         dashboards/
        ↓
Airflow Scheduling         airflow/dags/
        ↓
Docker Deployment          Dockerfile + docker-compose.yml
        ↓
GitHub Actions CI/CD       .github/workflows/
```

---

## Project structure

```
nyc-taxi-etl/
│
├── data/                         # gitignored — downloaded at runtime
│   ├── raw/
│   └── processed/
│
├── src/
│   ├── extract/
│   │   ├── config.py             # URLs, paths, years, settings
│   │   ├── logger.py             # Rotating file + console logger
│   │   ├── helpers.py            # Pure utility functions
│   │   ├── downloader.py         # Stream-download a single file
│   │   └── main.py               # Orchestration entry point
│   │
│   ├── transform/
│   │   └── clean.py              # Polars cleaning + feature engineering
│   │
│   └── load/
│       └── load_postgres.py      # Bulk COPY into PostgreSQL
│
├── sql/
│   ├── schema.sql                # Table + index definitions
│   └── analytics.sql             # Materialized views
│
├── dashboards/
│   └── nyc_taxi.pbix             # Power BI report
│
├── tests/
│   ├── test_helpers.py
│   ├── test_transform.py
│   └── test_load.py
│
├── airflow/
│   └── dags/
│       └── nyc_taxi_etl.py       # Monthly ETL DAG
│
├── .github/
│   └── workflows/
│       └── ci.yml                # Lint + test on every push
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Tech stack

| Layer | Tool | Purpose |
|---|---|---|
| Language | Python 3.12 | Core ETL logic |
| Data transformation | Polars | Fast DataFrame processing |
| Database | PostgreSQL 16 | Storage and analytics |
| Dashboard | Power BI Desktop | Visualisation |
| Orchestration | Apache Airflow 2.9 | Monthly scheduling |
| Containerisation | Docker + Compose | Reproducible deployment |
| CI/CD | GitHub Actions | Automated testing |
| Testing | pytest + ruff | Unit tests and linting |

---

## Dataset

| Property | Detail |
|---|---|
| Source | [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) |
| Format | Parquet |
| URL pattern | `https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_YYYY-MM.parquet` |
| Loaded years | 2023, 2024 |
| Approx. rows | ~50 million per year |
| Key columns | pickup/dropoff time, trip distance, fare, tip, payment type, location IDs |

---

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 16 running locally or via Docker
- Power BI Desktop (Windows only, for the dashboard step)

### 1. Clone the repo

```bash
git clone https://github.com/your-username/nyc-taxi-etl.git
cd nyc-taxi-etl
```

### 2. Create virtual environment and install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 3. Configure environment

```bash
copy .env.example .env
# Edit .env and fill in POSTGRES_URL
```

### 4. Download the dataset

```bash
python -m src.extract.main
# Downloads 2023 and 2024 Yellow Taxi parquet files into data/raw/
```

### 5. Transform

```bash
python -m src.transform.clean
```

### 6. Load to PostgreSQL

```bash
python -m src.load.load_postgres
```

### 7. Run with Docker (optional)

```bash
docker-compose up -d
```

---

## Running tests

```bash
pytest tests/ -v
```

---

## Topics covered and learning resources

### Python
- Modules, packages, and imports — [Real Python: Python Modules and Packages](https://realpython.com/python-modules-packages/)
- Logging best practices — [Python docs: logging HOWTO](https://docs.python.org/3/howto/logging.html)
- Pathlib for file handling — [Real Python: pathlib](https://realpython.com/python-pathlib/)

### Data engineering
- ETL vs ELT patterns — [Airbyte: ETL vs ELT](https://airbyte.com/blog/etl-vs-elt)
- Apache Parquet format — [Apache Parquet docs](https://parquet.apache.org/docs/)

### Polars
- Official user guide — [Polars user guide](https://docs.pola.rs/)
- Polars vs pandas — [Polars blog: Polars vs pandas](https://pola.rs/posts/polars-vs-pandas-memory/)

### PostgreSQL
- Getting started — [PostgreSQL official tutorial](https://www.postgresql.org/docs/current/tutorial.html)
- COPY for bulk inserts — [PostgreSQL COPY docs](https://www.postgresql.org/docs/current/sql-copy.html)
- Indexes and performance — [Use the Index, Luke](https://use-the-index-luke.com/)

### Apache Airflow
- Core concepts — [Airflow docs: concepts](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/index.html)
- Writing your first DAG — [Airflow tutorial](https://airflow.apache.org/docs/apache-airflow/stable/tutorial/fundamentals.html)

### Docker
- Docker getting started — [Docker official docs](https://docs.docker.com/get-started/)
- Docker Compose — [Compose getting started](https://docs.docker.com/compose/gettingstarted/)

### GitHub Actions
- Quickstart — [GitHub Actions docs](https://docs.github.com/en/actions/quickstart)
- Python CI example — [GitHub: building and testing Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)

### Power BI
- Getting started — [Microsoft Learn: Power BI](https://learn.microsoft.com/en-us/power-bi/fundamentals/power-bi-overview)
- Connect to PostgreSQL — [Power BI PostgreSQL connector](https://learn.microsoft.com/en-us/power-bi/connect-data/desktop-connect-postgresql)

---

## Progress

| Step | Status |
|---|---|
| Automated extraction | Complete |
| Polars transformations | In progress |
| PostgreSQL loading | Pending |
| Analytics tables | Pending |
| Power BI dashboard | Pending |
| Airflow scheduling | Pending |
| Docker deployment | Pending |
| GitHub Actions CI | Pending |

---

## License

MIT
