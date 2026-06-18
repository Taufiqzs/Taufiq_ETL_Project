import pandas as pd
from pathlib import Path


class Validasi_Data_Quality:

    Dir_Transformed_data = Path("taufiq_nyt_pipeline/data/transformed_data")
    Dir_Mart_Cleaned = Path("taufiq_nyt_pipeline/data/mart_clean")

    Transformed_taxi_file = "taxi_transformed.parquet" #data yang sudah di transform
    Taxi_transformed_clean_file = "taxi_clean.csv" #data mart yang sudah bersih dan siap digunakan
    Taxi_data_problem = "taxi_data_problematik.csv" #data yang di quarantine
    Report_validation_data_file = "data_quality_report.txt"# laporan ringkas kualitas data

    def __init__(self):
        self.Dir_Mart_Cleaned.mkdir(parents=True, exist_ok=True)

    def read_transformed_data(self) -> pd.DataFrame:
        in_path = self.Dir_Transformed_data / self.Transformed_taxi_file
        print(f"[READ] {in_path}")
        self.df = pd.read_parquet(in_path)
        print(f"  Baris : {len(self.df):,}")
        return self.df

    def save(self):
        clean_path = self.Dir_Mart_Cleaned / self.Taxi_transformed_clean_file
        quarantine_path = self.Dir_Mart_Cleaned / self.Taxi_data_problem
        self.valid_df.to_csv(clean_path, index=False)
        self.quarantine_df.to_csv(quarantine_path, index=False)
        print(f"[SAVE] Data bersih   : {clean_path}")
        print(f"[SAVE] Data karantina: {quarantine_path}")

# Method validasi: 
# Untuk mengecek setiap baris terhadap tiga aturan kualitas 
# dan menandai baris bermasalah dengan kolom error_type. 
# Satu baris bisa punya lebih dari satu error (multi-error).
    def Validasi(self):
        #Menandai baris bermasalah dengan error_type, lalu pisah ke karantina
        print("[Validasi] Memeriksa kualitas data")
        df = self.df.copy()
        df["error_type"] = ""

        #Aturan 1: durasi harus > 0 (pickup >= dropoff = invalid)
        df.loc[df["trip_duration_minutes"] <= 0, "error_type"] += "duration invalid;"
        #Aturan 2: jarak harus > 0
        df.loc[df["trip_distance"] <= 0, "error_type"] += "distance invalid;"
 

        self.valid_df = df[df["error_type"] == ""].drop(columns=["error_type"])
        self.quarantine_df = df[df["error_type"] != ""].copy()
        self.quarantine_df["error_type"] = self.quarantine_df["error_type"].str.rstrip(";")

        print(f"  Valid      : {len(self.valid_df):,}")
        print(f"  Karantina  : {len(self.quarantine_df):,}")

# Untuk membuat laporan ringkas data quality dalam file data_quality_report.txt. 
# Berisi total baris, persentase valid vs karantina, dan rincian jumlah tiap jenis error.
    def Create_report(self):
        total = len(self.df)
        valid = len(self.valid_df)
        quarantine = len(self.quarantine_df)

        error_counts = {}
        for errors in self.quarantine_df["error_type"]:
            for e in errors.split(";"):
                e = e.strip()
                if e:
                    error_counts[e] = error_counts.get(e, 0) + 1

        lines = [
            "=" * 50, "DATA QUALITY REPORT", "=" * 50,
            f"Total baris        : {total:,}",
            f"Baris valid        : {valid:,} ({valid/total*100:.2f}%)",
            f"Baris karantina    : {quarantine:,} ({quarantine/total*100:.2f}%)",
            "", "Rincian jenis error:",
        ]
        if error_counts:
            for err, count in error_counts.items():
                lines.append(f"  - {err}: {count:,}")
        else:
            lines.append("  (tidak ada error ditemukan)")
        lines.append("=" * 50)

        report_text = "\n".join(lines)
        report_path = self.Dir_Mart_Cleaned / self.Report_validation_data_file
        report_path.write_text(report_text)
        print("\n" + report_text)
        print(f"\n[REPORT] Disimpan ke {report_path}")

    def run(self):
  
        print("VALIDASI DATA QUALITY")
        self.read_transformed_data()
        self.Validasi()
        self.save()
        self.Create_report()
        print(f"\n[QUALITY CHECK] Berhasil diselesaikan!")


if __name__ == "__main__":
    Validasi_Data_Quality().run()