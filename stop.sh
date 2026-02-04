#!/bin/bash

# ChulAutoStock 종료 스크립트
# cron에서 매일 10:05에 실행

# 프로젝트 경로
PROJECT_DIR="/Users/chulyong/Documents/RecentProjects/ChulAutoStock"
LOG_DIR="$PROJECT_DIR/logs"
PID_FILE="$PROJECT_DIR/chulstock.pid"

# 로그 파일
LOG_FILE="$LOG_DIR/chulstock_$(date '+%Y%m%d').log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stopping ChulAutoStock..." >> "$LOG_FILE"

# PID 파일 확인
if [ ! -f "$PID_FILE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] PID file not found" >> "$LOG_FILE"
    exit 1
fi

PID=$(cat "$PID_FILE")

# 프로세스 확인
if ! ps -p "$PID" > /dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Process $PID not running" >> "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 0
fi

# SIGTERM 시그널 전송 (graceful shutdown)
kill -TERM "$PID"

# 최대 10초 대기
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Process stopped gracefully" >> "$LOG_FILE"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# 강제 종료
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Force killing process..." >> "$LOG_FILE"
kill -9 "$PID"
rm -f "$PID_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Process force killed" >> "$LOG_FILE"