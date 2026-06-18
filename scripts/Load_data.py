import pandas as pd
from pathlib import Path


class Load_data:
    BASE_DIR = Path(__file__).resolve().parents[1]
    transformed_dir = BASE_DIR / Path("./data/transformed_data")
    mart_dir = BASE_DIR / Path("./data/mart_data")

    Transformed_file = "taxi_transformed.parquet"
    Mart_file = "taxi_mart.csv"
    #Konstruktor. Membuat folder output data/mart_data/ jika belum ada.
    def __init__(self):
        self.mart_dir.mkdir(parents= True, exist_ok=True)


    # untuk simpan DataFrame ke format CSV di folder data/mart_data/.
    # output untuk data analyst
    def save_datamart_csv(self) -> Path:
        path_save = self.mart_dir / self.Mart_file
        self.df.to_csv(path_save, index=False)
        print(f"[Save] Data mart disimpan ke {path_save}")
        return path_save

    #untuk membaca file taxi_transformed.parquet
    #dari folder data/transformed_data/ ke dalam DataFrame pandas.
    def read_transformed(self) ->pd.DataFrame:
        path_read = self.transformed_dir/self.Transformed_file
        print(f"[Read] {path_read}")
        self.df = pd.read_parquet(path_read)
        print(f"  Baris : {len(self.df):,}")
        print(f"  Kolom : {len(self.df.columns)}")
        return self.df


    #ketika run code atau menjalankan pengubahan parquet menjadi csv
    #method read_transformed() -> save_datamart_csv()
    def run(self):
        print("=" * 10)
        print("TAHAP LOAD DATA")
        print("=" * 10)
        self.read_transformed()
        path_save = self.save_datamart_csv()
        print(f"\n[Load] Berhasil!")
        print(f"  Output: {path_save}")
        return path_save



if __name__ == "__main__":
    Load_data().run()
