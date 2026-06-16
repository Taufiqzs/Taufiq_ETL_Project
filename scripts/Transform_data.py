from pathlib import Path
import pandas as pd
import numpy as np



class Transform_data:

    raw_dir_path = Path("./data/raw_data_pl")
    file_raw_trip = "yellow_tripdata_2026-01.parquet"
    file_raw_taxi = "taxi_zone_lookup.csv"

    transformed_dir = Path("./data/transformed_data")

    def __init__(self, n_process_cpu_cores: int = None)
        self.transformed_dir.mkdir(parents=True, exist_ok=True)
        # n_process_cpu_cores adalah jumlah cpu core yang akan di melakukan proses kerja atau memproses data
        self.n_process_cpu_cores = n_process_cpu_cores or cpu_count()
    
    def dataread(self) -> pd.DataFrame:
    
    def run(self)


if __name__ == "__main__":
    Transform_data().run()