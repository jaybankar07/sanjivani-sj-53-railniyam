#!/bin/sh
# 1. Start FastAPI backend in background on port 8000
uvicorn app.main:app --host 127.0.0.1 --port 8000 &

# 2. Start Streamlit UI on $PORT (Render sets $PORT=10000)
exec streamlit run ui/app.py \
    --server.port "${PORT:-8501}" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false

