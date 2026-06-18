from pathlib import Path
import pandas as pd
import numpy as np
from multiprocessing import Pool, cpu_count

# Multiprocessing adalah teknik pembagian pekerjaan atau menjalankan proses per core di cpu
# Python punya keterbatasan bernama GIL (Global Interpreter Lock) 
# — hanya boleh ada 1 thread Python yang berjalan di satu waktu
# meskipun komputer punya banyak core.

#Pool adalah kumpulan CPU core yang siap menerima pekerjaan atau proses
#cpu_count adalah deteksi otomatis berapa core yang tersedia

#Fungsi worker untuk multiprocessing. Menerima satu potongan (chunk) DataFrame 
#dan melakukan transformasi datetime serta categorical mapping pada chunk tersebut. 
#Fungsi ini dijalankan paralel di banyak CPU core sekaligus.


def process_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    
    # Memproses transformasi per-baris untuk satu potongan (chunk) data:
    # - transformasi datetime
    # - categorical mapping
    # Dijalankan berparalel di beberapa CPU core sekaligus.

    payment_type_map = {
        0: "Unknown", 1: "Credit Card", 2: "Cash",
        3: "No Charge", 4: "Dispute",
    }
    store_fwd_map = {"Y": "Store and Forward", "N": "Normal"}

    pickup = chunk["tpep_pickup_datetime"]
    dropoff = chunk["tpep_dropoff_datetime"]

    # Transformasi datetime
    chunk["trip_duration_minutes"] = (dropoff - pickup).dt.total_seconds() / 60
    chunk["pickup_date"] = pickup.dt.date
    chunk["pickup_hour"] = pickup.dt.hour
    chunk["pickup_day_name"] = pickup.dt.day_name()
    chunk["is_weekend"] = pickup.dt.dayofweek.isin([5, 6])

    # Kategori waktu berdasarkan jam (vektorisasi pakai pd.cut lebih cepat)
    bins = [-1, 5, 10, 15, 19, 23]
    labels = ["Late Night", "Morning", "Afternoon", "Evening Rush", "Night"]
    chunk["time_period"] = pd.cut(chunk["pickup_hour"], bins=bins, labels=labels)

    # mapping per katagori atau categorial mapping
    if "payment_type" in chunk.columns:
        chunk["payment_type"] = chunk["payment_type"].map(payment_type_map).fillna("Unknown")
    if "store_and_fwd_flag" in chunk.columns:
        chunk["store_and_fwd_flag"] = (
            chunk["store_and_fwd_flag"].map(store_fwd_map).fillna(chunk["store_and_fwd_flag"])
        )

    return chunk


class Transform_data:
    #Lokasi direktori file raw data berada
    raw_dir_path = Path("taufiq_nyt_pipeline/data/raw_data_pl")
    file_raw_trip = "yellow_tripdata_2026-01.parquet"
    file_raw_taxi = "taxi_zone_lookup.csv"

    transformed_dir = Path("taufiq_nyt_pipeline/data/transformed_data")

    #Konstruktor class Transform. standar oop
    #Menyiapkan folder output data/transformed_data/ dan menentukan berapa banyak worker process yang akan dijalankan.
    def __init__(self, n_process_cpu_cores: int = None):
        self.transformed_dir.mkdir(parents=True, exist_ok=True)
      # n_process_cpu_cores menyimpan jumlah logical CPU/core yang tersedia.
      # Nilai digunakan untuk menentukan jumlah worker process multiprocessing.
      # Dengan cpu_count(), pipeline otomatis menyesuaikan jumlah worker
      # berdasarkan kapasitas CPU komputer tanpa perlu setting manual.
        self.n_process_cpu_cores = n_process_cpu_cores or cpu_count()
   
    #Menyimpan DataFrame hasil transformasi ke file Parquet di folder data/transformed_data/. 
    #Format Parquet lebih efisien untuk data besar dibanding CSV.
    def save_data(self) ->Path:
        res = self.transformed_dir / "taxi_transformed.parquet"
        self.df.to_parquet(res, index=False)
        print(f"[SAVE] Hasil transformasi disimpan ke {res}")
        return res


    #Membaca file parquet taxi dan CSV zone lookup
    #dari folder data/raw_data_pl/ ke dalam dua 
    #DataFrame pandas: self.df (data taxi) dan self.zone (zona lookup).
    def dataread(self) -> pd.DataFrame:
        # bisa menggunakan os.path.join("data/raw_data_pl", "yellow_tripdata_2026-01.parquet") tapi cara yang baru pakai Path()

        path_trip = self.raw_dir_path / self.file_raw_trip
        path_taxi = self.raw_dir_path / self.file_raw_taxi
        print(f"[READ] {path_trip}")
        self.df = pd.read_parquet(path_trip)
        print(f"[READ] {path_taxi}")
        self.zone = pd.read_csv(path_taxi)
        print(f"  Baris awal : {len(self.df):,}")
        print(f"  Kolom awal : {len(self.df.columns)}")
        return self.df

    # mengubah atau menstandarkan nama kolom menjadi snake_case,
    # memastikan kolom datetime bertipe datetime, dan kolom fee bertipe float64. 
    def standarisasi_schema(self):
        #Melakukan rename kolom ke snake_case, pastikan tipe data benar
        print("[TRANSFORM] Standarisasi skema...")
        explicit_rename = {
            "VendorID": "vendor_id",
            "RatecodeID": "ratecode_id",
            "PULocationID": "pu_location_id",
            "DOLocationID": "do_location_id",
            "Airport_fee": "airport_fee",
        }
        self.df = self.df.rename(columns=explicit_rename)
        self.df.columns = [c.lower() for c in self.df.columns]

        for col in ["tpep_pickup_datetime", "tpep_dropoff_datetime"]:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(self.df[col], errors="coerce")

        fee_cols = ["fare_amount", "tip_amount", "total_amount", "extra",
                    "mta_tax", "tolls_amount", "improvement_surcharge",
                    "congestion_surcharge", "airport_fee"]
        for col in fee_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce").astype("float64")

    # Menggabungkan/join data taxi dengan tabel zona lookup dua kali: 
    # yang pertama untuk lokasi pickup (pu_location_id), dan kedua untuk lokasi dropoff (do_location_id). 
    # Menghasilkan kolom baru: pickup_borough, pickup_zone, dropoff_borough, dropoff_zone.
    def transform_map_location(self):
        # Join PULocationID & DOLocationID ke nama zona/borough.
        # Dilakukan sekali (single process) karena merge pandas sudah cepat.
        print("[TRANSFORM] Mapping lokasi...")
        zone = self.zone.rename(columns={
            "LocationID": "location_id", "Borough": "borough",
            "Zone": "zone", "service_zone": "service_zone",
        })
        pu = zone.rename(columns={
            "location_id": "pu_location_id", "borough": "pickup_borough", "zone": "pickup_zone",
        })[["pu_location_id", "pickup_borough", "pickup_zone"]]
        self.df = self.df.merge(pu, on="pu_location_id", how="left")

        do = zone.rename(columns={
            "location_id": "do_location_id", "borough": "dropoff_borough", "zone": "dropoff_zone",
        })[["do_location_id", "dropoff_borough", "dropoff_zone"]]
        self.df = self.df.merge(do, on="do_location_id", how="left")
   
    # ketika run code Method ini menjalankan Transform_data.py
    # menjalankan 5 sub-tahap berurutan: read_data → standardize_schema → transform_parallel → map_location → save.
    def run(self) -> Path:
        print("TRANSFORMASI DATA")
        self.dataread()
        self.standarisasi_schema()
       
        self.transform_map_location()
        res = self.save_data()
        print(f"\n[TRANSFORMASI]  telah selesai")
        print(f"  Baris akhir : {len(self.df):,}")
        print(f"  Kolom akhir : {len(self.df.columns)}")
        return res


if __name__ == "__main__":
    Transform_data().run()