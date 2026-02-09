#!/bin/bash

echo "🗓️ ChulAutoStock Cron 스케줄러 설정"

# 현재 디렉토리 경로
CURRENT_DIR=$(pwd)

# Python 경로 확인
PYTHON_PATH=$(which python3)

# cron 작업 내용
CRON_JOB="28 8 * * 1-5 cd $CURRENT_DIR && $PYTHON_PATH main.py >> $CURRENT_DIR/trading.log 2>&1"

# 기존 cron 백업
echo "1. 기존 cron 백업 중..."
crontab -l > cron_backup.txt 2>/dev/null

# ChulAutoStock 관련 기존 항목 제거
echo "2. 기존 ChulAutoStock 스케줄 제거..."
crontab -l 2>/dev/null | grep -v "ChulAutoStock\|main.py" | crontab -

# 새 스케줄 추가
echo "3. 새 스케줄 추가..."
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo ""
echo "✅ 스케줄러 설정 완료!"
echo "📋 등록된 스케줄:"
echo "   $CRON_JOB"
echo ""
echo "🔍 확인 명령어: crontab -l"
echo "📝 수동 편집: crontab -e"
