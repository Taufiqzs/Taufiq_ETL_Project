# Capstone project NYC Taxi Data Pipeline

Data pipeline untuk mengalirkan dan mengolah data perjalanan taxi New York
bulan Januari 2026, dari ETL(Ekstraksi Transformasi dan Load) sampai validasi kualitas data.

# Tahapan Pipeline

Extract -> Transform -> Load -> Data Quality Check
(download) (bersihkan) (CSV) (validasi + karantina)

# Struktur Folder Project

```
taufiq_nyt_pipeline/
├── data/
│ ├── raw_data_pl/ # data mentah hasil download
│ ├── transformed_data/ # hasil transformasi (parquet)
│ ├── mart_data/ # data mart final (CSV)
│ └── mart_clean/ # data tervalidasi + karantina + report
├── logs/
│ └── pipeline.log # log proses dengan timestamp
├── scripts/
│ ├── Extract_data.py # Tahap 1: download data
│ ├── Transform_data.py # Tahap 2: transformasi
│ ├── Load_data.py # Tahap 3: load ke CSV
│ ├── Validasi_Data_Quality.py # Tahap 4: validasi kualitas
│ └── run_pipeline.sh # automation seluruh pipeline
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
└── README.md
```

# Tahapan

# 1. Extract (`Extract_data.py`)

Mengunduh dua file menggunakan library `requests`:

- Data taxi (parquet, ~61 MiB)
- Taxi Zone Lookup (CSV)

URL diambil dari environment variable `DATA_URL` dan `ZONE_LOOKUP_URL`
(diset lewat Docker), dengan fallback ke URL default.

## Input

| File                              | Lokasi                                  | Keterangan |
| --------------------------------- | --------------------------------------- | ---------- |
| `taxi_zone_lookup.csv`            | `taufiq_nyt_pipeline/data/raw_data_pl/` | raw data   |
| `yellow_tripdata_2026-01.parquet` | `taufiq_nyt_pipeline/data/raw_data_pl/` | raw data   |

# 2. Transform (`Transform_data.py`)

- **Standarisasi skema(standarisasi_schema)**: rename kolom ke snake_case, casting datetime & float
- **Transformasi datetime(transform_parallel)**: `trip_duration_minutes`, `pickup_date`, `pickup_hour`,
  `pickup_day_name`, `is_weekend`, `time_period`
- **Categorical mapping(transform_parallel)**: `payment_type` & `store_and_fwd_flag` jadi label
- **Mapping lokasi(transform_map_location)**: join `pu_location_id` & `do_location_id` ke zona/borough

**Multiprocessing**: method transform_parallel yaitu method transformasi per-baris (datetime & categorical) dijalankan paralel atau berbarengan di beberapa CPU core menggunakan `multiprocessing.Pool`. DataFrame dibagi
menjadi chunk, tiap chunk diproses di core terpisah, lalu digabung kembali.
Mapping lokasi tetap single-process karena `merge` pandas sudah dioptimasi.

# 3. Load (`Load_data.py`)

Mengubah hasil transformasi menjadi format CSV di `taufiq_nyt_pipeline/data/mart_data/`.

# 4. Data Quality Check (`Validasi_Data_Quality.py`)

Memvalidasi data. Baris bermasalah tidak dihapus, tapi dikarantina ke file
terpisah dengan kolom `error_type`:

- Durasi <= 0 → `duration invalid`
- Jarak <= 0 → `distance invalid`

Menghasilkan `data_quality_report.txt`.

# Cara Menjalankan

pip install -r requirements.txt
bash scripts/pipeline.sh

# Docker

docker compose up --build

Hasil pipeline tersimpan di folder `./data` dan log di `./logs/pipeline.log`
melalui volume mount.

# Output

| File                        | Lokasi                                       | Keterangan                   |
| --------------------------- | -------------------------------------------- | ---------------------------- |
| `taxi_transformed.parquet`  | `taufiq_nyt_pipeline/data/transformed_data/` | Hasil transformasi           |
| `taxi_mart.csv`             | `taufiq_nyt_pipeline/data/mart_data/`        | Data mart final              |
| `taxi_clean.csv`            | `taufiq_nyt_pipeline/data/mart_clean/`       | Data lolos validasi          |
| `taxi_data_problematik.csv` | `taufiq_nyt_pipeline/data/mart_clean/`       | Data bermasalah + error_type |
| `data_quality_report.txt`   | `taufiq_nyt_pipeline/data/mart_clean/`       | Ringkasan kualitas data      |
| `pipeline.log`              | `taufiq_nyt_pipeline/logs/`                  | Log proses dengan timestamp  |
