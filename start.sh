#!/bin/bash

# ChulAutoStock 시작 스크립트
# cron에서 매일 08:25에 실행

# 프로젝트 경로
PROJECT_DIR="/Users/chulyong/Documents/RecentProjects/ChulAutoStock"
LOG_DIR="$PROJECT_DIR/logs"
PID_FILE="$PROJECT_DIR/chulstock.pid"

# 로그 디렉토리 생성
mkdir -p "$LOG_DIR"

# 이미 실행 중인지 확인
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Already running with PID $OLD_PID"
        exit 1
    fi
fi

# 프로젝트 디렉토리로 이동
cd "$PROJECT_DIR"

# Python 경로 (필요시 수정)
PYTHON="/usr/bin/python3"

# 오늘 날짜로 로그 파일 생성
LOG_FILE="$LOG_DIR/chulstock_$(date '+%Y%m%d').log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting ChulAutoStock..." >> "$LOG_FILE"

# 백그라운드로 실행
nohup $PYTHON scheduler.py >> "$LOG_FILE" 2>&1 &

# PID 저장
echo $! > "$PID_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Started with PID $(cat $PID_FILE)" >> "$LOG_FILE"