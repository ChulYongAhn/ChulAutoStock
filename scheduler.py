"""
ChulAutoStock 일일 스케줄러
08:29 ~ 10:00까지만 실행되는 단일 세션용
cron으로 08:25에 시작, 10:05에 종료
"""

import time
import sys
import signal
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Phase 모듈 임포트
from phase0_auth import Phase0Auth
from phase1_past_data import Phase1PastData
from phase2_monitoring import Phase2Monitoring
from phase3_scoring import Phase3Scoring

# .env 파일 로드
load_dotenv()


class DailyScheduler:
    """일일 거래 스케줄러 (08:29 ~ 10:00)"""

    def __init__(self, is_real: bool = True):
        self.is_real = is_real
        self.auth = None
        self.api = None
        self.past_data = {}
        self.is_running = True

        # 시그널 핸들러 등록 (graceful shutdown)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        """종료 시그널 처리"""
        print(f"\n📌 종료 시그널 받음 ({signum})")
        self.is_running = False
        self.cleanup()
        sys.exit(0)

    def run(self):
        """일일 거래 실행 (08:29 ~ 10:00)"""
        print("="*70)
        print(f" ChulAutoStock 일일 거래 시작")
        print(f" 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)

        # 08:29까지 대기
        self.wait_until(8, 29)

        # Phase 0: API 인증 (08:29)
        if not self.phase0_auth():
            print("❌ API 인증 실패. 프로그램 종료")
            return

        # 08:30까지 대기
        self.wait_until(8, 30)

        # Phase 1: 데이터 수집 (08:30)
        self.phase1_past_data()

        # 08:35까지 대기
        self.wait_until(8, 35)

        # Phase 2: 동시호가 모니터링 (08:35 ~ 08:57)
        phase2 = Phase2Monitoring(self.api, self.past_data)
        end_time = datetime.now().replace(hour=8, minute=58, second=0)

        while datetime.now() < end_time and self.is_running:
            filtered = phase2.run()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {len(filtered)}개 종목 필터링")

            # 10초 대기
            time.sleep(10)

        # Phase 3: 최종 선정 (08:58)
        if self.is_running:
            self.wait_until(8, 58)
            top_stocks = self.phase3_final_selection(phase2.get_filtered_stocks())

            # TODO: 매수 주문 실행

        # Phase 4: 포지션 관리 (09:00 ~ 09:59)
        self.wait_until(9, 0)
        print("\n🔔 장 시작! 포지션 관리 시작")

        end_time = datetime.now().replace(hour=9, minute=59, second=0)
        while datetime.now() < end_time and self.is_running:
            self.phase4_position_management()
            time.sleep(5)  # 5초마다 체크

        # Phase 5: 일일 마감 (09:59 ~ 10:00)
        if self.is_running:
            self.wait_until(9, 59)
            self.phase5_daily_closing()

        print("\n✅ 일일 거래 완료")
        print(f"종료 시간: {datetime.now().strftime('%H:%M:%S')}")

    def wait_until(self, hour: int, minute: int):
        """특정 시간까지 대기"""
        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0)

        # 이미 지난 시간이면 스킵
        if now >= target:
            return

        wait_seconds = (target - now).total_seconds()
        print(f"⏰ {hour:02d}:{minute:02d}까지 대기 ({int(wait_seconds)}초)")

        # 대기 중에도 종료 시그널 체크
        while datetime.now() < target and self.is_running:
            time.sleep(1)

    def phase0_auth(self) -> bool:
        """Phase 0: API 인증"""
        print("\n[Phase 0] API 인증")
        phase0 = Phase0Auth(is_real=self.is_real)
        self.auth, self.api = phase0.run()
        return self.auth is not None and self.api is not None

    def phase1_past_data(self):
        """Phase 1: 데이터 수집"""
        print("\n[Phase 1] 데이터 수집")
        phase1 = Phase1PastData()
        self.past_data = phase1.run()
        print(f"✅ {len(self.past_data)}개 종목 데이터 수집 완료")

    def phase3_final_selection(self, filtered_stocks):
        """Phase 3: 최종 선정"""
        print("\n[Phase 3] 최종 종목 선정")
        if filtered_stocks:
            phase3 = Phase3Scoring(filtered_stocks)
            top_stocks = phase3.run()
            return top_stocks
        return []

    def phase4_position_management(self):
        """Phase 4: 포지션 관리"""
        # TODO: 실시간 모니터링 및 매매
        pass

    def phase5_daily_closing(self):
        """Phase 5: 일일 마감"""
        print("\n[Phase 5] 일일 마감")
        # TODO: 보유 종목 청산
        self.generate_report()

    def generate_report(self):
        """일일 리포트 생성"""
        print("\n📋 일일 거래 리포트")
        print(f"날짜: {datetime.now().strftime('%Y-%m-%d')}")
        print("거래 시간: 08:29 ~ 10:00")
        # TODO: 실제 거래 통계

    def cleanup(self):
        """종료 시 정리"""
        print("\n🧹 정리 작업 중...")
        # API 연결 종료, 캐시 저장 등


def main():
    """메인 함수"""
    scheduler = DailyScheduler(is_real=True)
    scheduler.run()


if __name__ == "__main__":
    main()