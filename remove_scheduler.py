#!/usr/bin/env python3
"""
스케줄러(cron) 삭제 스크립트
VSCode에서 F5 또는 Run Python File로 실행
"""

import subprocess
import os
import sys
from datetime import datetime

def remove_scheduler():
    """cron 스케줄러 삭제"""

    print("="*50)
    print("🗑️  ChulAutoStock 스케줄러 삭제")
    print("="*50)

    try:
        # 1. 현재 cron 확인
        print("\n1. 현재 등록된 스케줄 확인 중...")
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_cron = result.stdout if result.returncode == 0 else ""

        if not current_cron:
            print("   ⚠️  등록된 스케줄이 없습니다.")
            return True

        # 2. ChulAutoStock 관련 항목 찾기
        print("\n2. ChulAutoStock 관련 스케줄 검색 중...")
        lines_to_remove = []
        lines_to_keep = []

        for line in current_cron.split('\n'):
            if line and ('main.py' in line or 'ChulAutoStock' in line):
                lines_to_remove.append(line)
                print(f"   🔍 발견: {line}")
            elif line:  # 빈 줄이 아닌 다른 스케줄
                lines_to_keep.append(line)

        if not lines_to_remove:
            print("   ⚠️  ChulAutoStock 관련 스케줄이 없습니다.")
            return True

        # 3. 백업
        print("\n3. 백업 중...")
        backup_file = f"cron_backup_before_remove_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(backup_file, 'w') as f:
            f.write(current_cron)
        print(f"   ✅ 백업 완료: {backup_file}")

        # 4. 삭제 확인
        print("\n" + "="*50)
        print("⚠️  다음 스케줄을 삭제합니다:")
        print("="*50)
        for line in lines_to_remove:
            print(f"   - {line}")

        print("\n정말 삭제하시겠습니까? (y/n): ", end='')
        confirm = input().lower().strip()

        if confirm != 'y':
            print("\n❌ 삭제 취소")
            return False

        # 5. 삭제 실행
        print("\n4. 스케줄 삭제 중...")
        new_cron = '\n'.join(lines_to_keep) + '\n' if lines_to_keep else ''

        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_cron)

        print(f"   ✅ 삭제 완료! ({len(lines_to_remove)}개 항목)")

        # 6. 결과 확인
        print("\n" + "="*50)
        print("📋 남은 스케줄:")
        print("="*50)

        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        else:
            print("   (없음 - 모든 스케줄이 삭제됨)")

        # 7. 실행 중인 프로세스 확인
        print("\n" + "="*50)
        print("🔍 실행 중인 프로세스 확인:")
        print("="*50)

        result = subprocess.run(['pgrep', '-f', 'main.py'], capture_output=True, text=True)
        if result.stdout:
            pids = result.stdout.strip().split('\n')
            print(f"   ⚠️  main.py가 실행 중입니다. (PID: {', '.join(pids)})")
            print("   종료하려면: pkill -f main.py")
        else:
            print("   ✅ 실행 중인 프로세스 없음")

        print("\n✅ 스케줄러 삭제 완료!")
        print("📌 ChulAutoStock이 더 이상 자동으로 실행되지 않습니다.")

        return True

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("\n수동으로 삭제하려면:")
        print("1. 터미널에서: crontab -e")
        print("2. main.py가 포함된 줄을 찾아서 dd로 삭제")
        print("3. :wq로 저장")
        return False

if __name__ == "__main__":
    success = remove_scheduler()

    if not success:
        sys.exit(1)

    print("\n" + "="*50)
    print("💡 다시 등록하려면:")
    print("   reset_scheduler.py 실행")
    print("="*50)