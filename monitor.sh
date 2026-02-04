#!/bin/bash

# 실행 상태 모니터링 스크립트

PROJECT_DIR="/Users/chulyong/Documents/RecentProjects/ChulAutoStock"
PID_FILE="$PROJECT_DIR/chulstock.pid"
LOG_DIR="$PROJECT_DIR/logs"

echo "================================"
echo "ChulAutoStock 모니터링"
echo "================================"

# 실행 상태 확인
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null; then
        echo "✅ 실행 중 (PID: $PID)"
        echo ""
        echo "프로세스 정보:"
        ps -p "$PID" -o pid,vsz,rss,pcpu,comm
    else
        echo "❌ 실행 중이 아님 (PID 파일은 있으나 프로세스 없음)"
    fi
else
    echo "❌ 실행 중이 아님 (PID 파일 없음)"
fi

echo ""
echo "--------------------------------"
echo "오늘의 로그:"
echo "--------------------------------"

# 오늘 날짜 로그 파일
TODAY_LOG="$LOG_DIR/chulstock_$(date '+%Y%m%d').log"

if [ -f "$TODAY_LOG" ]; then
    echo "로그 파일: $TODAY_LOG"
    echo "마지막 20줄:"
    echo ""
    tail -20 "$TODAY_LOG"
else
    echo "오늘 로그 파일 없음"
fi

echo ""
echo "--------------------------------"
echo "다음 실행 예정:"
echo "--------------------------------"

# crontab 확인
crontab -l 2>/dev/null | grep ChulAutoStock -A 5 || echo "Cron 설정 없음"

echo ""
echo "================================"
echo "명령어:"
echo "  tail -f $TODAY_LOG  # 실시간 로그"
echo "  ./stop.sh                    # 중지"
echo "  ./start.sh                   # 시작"
echo "================================"