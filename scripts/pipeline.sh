#bash
#pipeline.sh
#Automation
#Menjalankan seluruh pipeline: extract -> transform -> load -> quality check
#Semua proses dicatat ke logs/pipeline.log dengan timestamp


set -e

LOG_FILE="./logs/pipeline.log"
mkdir -p logs

#Fungsi log dengan timestamp, menulis ke terminal & file sekaligus
log() {
    local message="$1"
    local timestamp
    timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "${timestamp} - ${message}" | tee -a "$LOG_FILE"
}

log "Starting pipeline"

python3 ./scripts/Extract_data.py >> "$LOG_FILE" 2>&1
log "Extract Berhasil"

python3 ./scripts/Transform_data.py >> "$LOG_FILE" 2>&1
log "Transform Berhasil"

python3 ./scripts/Load_data.py >> "$LOG_FILE" 2>&1
log "Load Berhasil"

python3 ./scripts/Validasi_Data_Quality.py >> "$LOG_FILE" 2>&1
log "Validasi Data quality check Berhasil"

log "Pipeline berjalan successfully"