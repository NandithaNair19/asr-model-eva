#!/bin/bash

# End-to-end test script for cross-lingual-asr-eval

LOG="e2e_test_log.txt"
echo "" > $LOG

log() {
    echo "$1" | tee -a $LOG
}

run() {
    log ""
    log "$ $1"
    eval "$1" 2>&1 | tee -a $LOG
}

log " cross-lingual-asr-eval — End-to-End Test"
log " Date: $(date)"

# Step 1 - Clone repo
log ""
log "Step 1: Clone repository"
run "git clone https://github.com/NandithaNair19/asr-model-eva.git ~/Downloads/cross-lingual-asr-eval"
cd ~/Downloads/cross-lingual-asr-eval
log "$ cd ~/Downloads/cross-lingual-asr-eval"

# Step 2 — Python version
log ""
log "Step 2: Python version"
run "python3.11 --version"

# Step 3 — Create and activate venv
log ""
log "Step 3: Create virtual environment"
run "python3.11 -m venv venv"
source venv/bin/activate
log "$ source venv/bin/activate"
log " venv activated"

# Step 4 — Install dependencies
log ""
log "Step 4: Install dependencies"
run "pip install -r requirements.txt"

# Step 5 — Generate audio files
log ""
log "Step 5: Generate audio files"
run "python3 generate_audio.py"

# Step 6 — Run in MOCK mode
log ""
log "Step 6: Run evaluation in MOCK mode"
run "USE_MOCK=true python3 asr_eval.py"

# Step 7 — Setup .env for real mode
log ""
log "Step 7: Setup .env for REAL ASR mode"
run "cp .env.example .env"
log ""
read -p "Enter your ASR endpoint IP (press Enter to skip and run mock mode only): " ASR_IP

if [ -z "$ASR_IP" ]; then
    log "  No IP provided — skipping real ASR mode"
    log "   To run in real mode later, set your IP in .env and run: python3 asr_eval.py"
else
    echo "ASR_ENDPOINT=http://$ASR_IP:5000/v2/models/asr_am_ensemble/infer" > .env
    echo "USE_MOCK=false" >> .env
    log "$ echo 'ASR_ENDPOINT=http://$ASR_IP:5000/v2/models/asr_am_ensemble/infer' > .env"
    log "$ echo 'USE_MOCK=false' >> .env"
    log " .env configured with ASR endpoint"

    # Step 8 — Run in REAL mode
    log ""
    log "Step 8: Run evaluation in REAL ASR mode"
    export $(cat .env | xargs)
    run "python3 asr_eval.py"
fi

# Step 9 — Check results
log ""
log "Step 9: Check output files"
run "ls -lh results/"
run "cat results/report.csv"

log ""
log " End-to-end test complete!"
log " Full log saved to: $LOG"