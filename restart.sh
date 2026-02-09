#!/bin/bash

echo "🔄 ChulAutoStock 재시작 중..."

# 기존 프로세스 종료
echo "1. 기존 프로세스 종료..."
pkill -f main.py
sleep 1

# git pull (선택사항)
echo "2. 최신 코드 가져오기..."
git pull

# 새로 시작
echo "3. 프로그램 시작..."
nohup python main.py > trading.log 2>&1 &

# PID 확인
sleep 2
NEW_PID=$(pgrep -f main.py)

if [ ! -z "$NEW_PID" ]; then
    echo "✅ 재시작 완료! (PID: $NEW_PID)"
    echo "📝 로그 확인: tail -f trading.log"
else
    echo "❌ 시작 실패. 수동으로 확인하세요."
fi