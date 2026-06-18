
# Dockerfile untuk Taufiq NYC Taxi Data Pipeline

FROM python:3.12-slim

#Set folder kerja di dalam container
WORKDIR /app

#Copy file requirements dulu (agar layer cache efisien)
COPY requirements.txt .

#Install library yang dibutuhkan
RUN pip install --no-cache-dir -r requirements.txt

#Copy semua isi project ke dalam container
COPY . .

#Beri izin eksekusi pada shell script
RUN chmod +x scripts/pipeline.sh

#Perintah default ketika container dijalankan: jalankan pipeline
CMD ["bash", "scripts/pipeline.sh"]