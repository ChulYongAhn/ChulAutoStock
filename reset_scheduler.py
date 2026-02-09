#!/usr/bin/env python3
"""
스케줄러(cron) 재등록 스크립트
VSCode에서 F5 또는 Run Python File로 실행
"""

import subprocess
import os
import sys
from datetime import datetime

def reset_scheduler():
    """cron 스케줄러 재등록"""

    print("="*50)
    print("🗓️  ChulAutoStock 스케줄러 재등록")
    print("="*50)

    # 현재 디렉토리
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Python 경로
    python_path = sys.executable

    # cron 작업 내용
    cron_job = f"28 8 * * 1-5 cd {current_dir} && {python_path} main.py >> {current_dir}/trading.log 2>&1"

    try:
        # 1. 기존 cron 백업
        print("\n1. 기존 스케줄 백업 중...")
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_cron = result.stdout if result.returncode == 0 else ""

        # 백업 파일 저장
        backup_file = f"cron_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(backup_file, 'w') as f:
            f.write(current_cron)
        print(f"   ✅ 백업 완료: {backup_file}")

        # 2. ChulAutoStock 관련 기존 항목 제거
        print("\n2. 기존 ChulAutoStock 스케줄 제거 중...")
        new_cron_lines = []
        removed_count = 0

        for line in current_cron.split('\n'):
            if line and 'main.py' not in line and 'ChulAutoStock' not in line:
                new_cron_lines.append(line)
            elif line and ('main.py' in line or 'ChulAutoStock' in line):
                print(f"   삭제: {line}")
                removed_count += 1

        if removed_count == 0:
            print("   기존 스케줄 없음")

        # 3. 새 스케줄 추가
        print("\n3. 새 스케줄 추가 중...")
        new_cron_lines.append(cron_job)
        new_cron = '\n'.join(new_cron_lines) + '\n'

        # 4. cron 업데이트
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_cron)

        print(f"   ✅ 추가 완료!")

        # 5. 확인
        print("\n" + "="*50)
        print("📋 등록된 스케줄:")
        print("="*50)
        print(f"시간: 매일 08:28 (월-금)")
        print(f"경로: {current_dir}")
        print(f"명령: python main.py")
        print("\n전체 명령어:")
        print(cron_job)

        # 6. 현재 등록된 모든 cron 작업 표시
        print("\n" + "="*50)
        print("🔍 현재 등록된 모든 스케줄:")
        print("="*50)
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        else:
            print("등록된 스케줄 없음")

        print("\n✅ 스케줄러 재등록 완료!")
        print("📌 다음 실행 시간: 내일 08:28 (평일)")

        return True

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("\n수동으로 설정하려면:")
        print("1. 터미널에서: crontab -e")
        print("2. 다음 줄 추가:")
        print(f"   {cron_job}")
        return False

if __name__ == "__main__":
    success = reset_scheduler()

    if not success:
        sys.exit(1)

    print("\n" + "="*50)
    print("💡 확인 명령어:")
    print("   crontab -l  (모든 스케줄 확인)")
    print("   ps aux | grep main.py  (실행 중인 프로세스 확인)")
    print("="*50)