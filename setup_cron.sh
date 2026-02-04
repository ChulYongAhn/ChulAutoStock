#!/bin/bash

# Crontab 설정 도우미 스크립트

echo "================================"
echo "ChulAutoStock Crontab 설정"
echo "================================"

# 프로젝트 경로 확인
PROJECT_DIR=$(pwd)
echo "프로젝트 경로: $PROJECT_DIR"

# Python 경로 찾기
PYTHON_PATH=$(which python3)
echo "Python 경로: $PYTHON_PATH"

# 현재 crontab 백업
echo ""
echo "1. 현재 crontab 백업 중..."
crontab -l > crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || echo "기존 crontab 없음"

# crontab.txt 파일 수정
echo ""
echo "2. crontab.txt 파일 생성 중..."
cat > crontab_temp.txt << EOF
# ChulAutoStock 자동 거래 스케줄
# 생성일: $(date '+%Y-%m-%d %H:%M:%S')

# 환경 변수
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin

# 매일 08:25 시작 (월-금)
25 8 * * 1-5 $PROJECT_DIR/start.sh

# 매일 10:05 종료 (월-금)
5 10 * * 1-5 $PROJECT_DIR/stop.sh

# 매일 자정 로그 정리 (30일 이상)
0 0 * * * find $PROJECT_DIR/logs -name "*.log" -mtime +30 -delete
EOF

echo "생성된 crontab 내용:"
echo "-------------------"
cat crontab_temp.txt
echo "-------------------"

# 사용자 확인
echo ""
read -p "이 설정을 적용하시겠습니까? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 기존 crontab과 병합
    (crontab -l 2>/dev/null; echo ""; cat crontab_temp.txt) | crontab -
    echo "✅ Crontab 설정 완료!"
    echo ""
    echo "현재 crontab 목록:"
    crontab -l | grep ChulAutoStock -A 10
else
    echo "❌ 취소됨"
fi

# 임시 파일 삭제
rm -f crontab_temp.txt

echo ""
echo "================================"
echo "설정 완료!"
echo ""
echo "유용한 명령어:"
echo "  crontab -l     : 현재 설정 확인"
echo "  crontab -e     : 설정 편집"
echo "  crontab -r     : 모든 설정 삭제"
echo ""
echo "수동 실행:"
echo "  ./start.sh     : 수동 시작"
echo "  ./stop.sh      : 수동 종료"
echo "  tail -f logs/*.log : 로그 실시간 확인"
echo "================================"