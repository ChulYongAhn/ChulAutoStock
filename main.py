"""
ChulAutoStock - 24시간 자동 주식 트레이딩 시스템
매일 08:29 ~ 10:00 자동 실행
"""

import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Phase 모듈 임포트
from phase0_auth import Phase0Auth
from phase1_past_data import Phase1PastData
from phase2_monitoring import Phase2Monitoring
from phase3_scoring import Phase3Scoring

# .env 파일 로드
load_dotenv()


class ChulAutoStock:
    """24시간 자동 트레이딩 시스템"""

    def __init__(self, is_real: bool = True):
        """
        초기화

        Args:
            is_real: True=실전, False=모의투자
        """
        self.is_real = is_real
        self.auth = None
        self.api = None
        self.past_data = {}

        # 거래 시간 설정
        self.WAKE_TIME = (8, 29)      # 08:29 시작
        self.PHASE1_TIME = (8, 30)    # 08:30 Phase 1
        self.PHASE2_TIME = (8, 35)    # 08:35 Phase 2 시작
        self.PHASE3_TIME = (8, 58)    # 08:58 Phase 3
        self.MARKET_OPEN = (9, 0)     # 09:00 장 시작
        self.PHASE5_TIME = (9, 59)    # 09:59 Phase 5
        self.SLEEP_TIME = (10, 0)     # 10:00 종료

        self.TRADING_DAYS = [0, 1, 2, 3, 4]  # 월~금

    def run_forever(self):
        """24시간 무한 실행"""
        print("="*70)
        print(" ChulAutoStock - 24시간 자동 트레이딩 시스템")
        print(" 프로그램이 24시간 구동됩니다.")
        print(" 매일 08:29 ~ 10:00 자동 거래")
        print(" 종료: Ctrl+C")
        print("="*70)

        while True:
            try:
                now = datetime.now()

                # 거래일 체크
                if not self.is_trading_day(now):
                    self.wait_mode(f"주말/공휴일 - 다음 거래일 대기")
                    continue

                # 시간별 동작
                current_time = (now.hour, now.minute)

                # 08:29 - 깨어나기
                if current_time == self.WAKE_TIME:
                    self.wake_up()

                # 08:30 - Phase 1
                elif current_time == self.PHASE1_TIME:
                    if self.auth and self.api:
                        self.phase1_past_data()

                # 08:35 ~ 08:57 - Phase 2 반복
                elif self.PHASE2_TIME <= current_time < self.PHASE3_TIME:
                    if self.auth and self.api and self.past_data:
                        self.phase2_monitoring()

                # 08:58 - Phase 3
                elif current_time == self.PHASE3_TIME:
                    if self.auth and self.api:
                        self.phase3_final_selection()

                # 09:00 ~ 09:58 - Phase 4
                elif self.MARKET_OPEN <= current_time < self.PHASE5_TIME:
                    if self.auth and self.api:
                        self.phase4_position_management()

                # 09:59 - Phase 5
                elif current_time == self.PHASE5_TIME:
                    if self.auth and self.api:
                        self.phase5_daily_closing()

                # 10:00 이후 - 대기 모드
                elif current_time >= self.SLEEP_TIME:
                    self.enter_sleep_mode()

                # 08:29 이전 - 대기 모드
                elif current_time < self.WAKE_TIME:
                    minutes_until = self.minutes_until_wake()
                    self.wait_mode(f"거래 시작까지 {minutes_until}분 남음")

                # 짧은 대기 (CPU 사용량 최소화)
                time.sleep(30)  # 30초마다 체크

            except KeyboardInterrupt:
                print("\n\n프로그램을 종료합니다.")
                break
            except Exception as e:
                print(f"\n❌ 오류 발생: {e}")
                print("1분 후 재시작...")
                time.sleep(60)

    def wake_up(self):
        """08:29 - 거래 준비 시작"""
        print("\n" + "="*70)
        print(f"🔔 WAKE UP! - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)

        # Phase 0: API 인증
        phase0 = Phase0Auth(is_real=self.is_real)
        self.auth, self.api = phase0.run()

        if not self.auth or not self.api:
            print("❌ API 인증 실패! 대기 모드 유지...")
            return

        # API 사용량 체크
        self._check_api_usage("Wake Up")

        print("✅ 거래 준비 완료! Phase 1 대기 중...")

    def phase1_past_data(self):
        """Phase 1: 과거 데이터 수집"""
        phase1 = Phase1PastData()
        self.past_data = phase1.run()

        if self.past_data:
            print(f"✅ Phase 1 완료: {len(self.past_data)}개 종목 데이터 수집")

        self._check_api_usage("Phase 1")

    def phase2_monitoring(self):
        """Phase 2: 실시간 모니터링"""
        if not hasattr(self, 'phase2_instance'):
            self.phase2_instance = Phase2Monitoring(self.api, self.past_data)

        filtered = self.phase2_instance.run()
        print(f"📊 Phase 2: {len(filtered)}개 종목 필터링")

        # 08:57 이후에만 API 사용량 체크 (과도한 체크 방지)
        if datetime.now().minute >= 57:
            self._check_api_usage("Phase 2")

    def phase3_final_selection(self):
        """Phase 3: 최종 종목 선정"""
        if hasattr(self, 'phase2_instance'):
            filtered = self.phase2_instance.get_filtered_stocks()

            if filtered:
                phase3 = Phase3Scoring(filtered)
                top_stocks = phase3.run()

                if top_stocks:
                    print("\n🎯 Phase 3 최종 선정 완료!")
                    print(f"   매수 예정: {len(top_stocks)}개 종목")

                    # TODO: 실제 매수 주문 구현
                    for stock in top_stocks:
                        print(f"   - {stock['종목명']} ({stock['종목코드']})")

        self._check_api_usage("Phase 3")

    def phase4_position_management(self):
        """Phase 4: 포지션 관리 (구현 예정)"""
        # 실시간 현재가 모니터링
        # 익절/손절 체크
        # 자동 매도 실행
        pass

    def phase5_daily_closing(self):
        """Phase 5: 일일 마감"""
        print("\n" + "="*70)
        print(f"🏁 일일 마감 - {datetime.now().strftime('%H:%M:%S')}")
        print("="*70)

        # TODO: 보유 종목 전량 매도

        # 일일 리포트
        self._generate_daily_report()

        # API 사용량 최종 체크
        self._check_api_usage("Daily Closing")

        print("\n😴 대기 모드 전환 준비...")

    def enter_sleep_mode(self):
        """대기 모드 진입"""
        # 10:00가 되면 한 번만 실행
        now = datetime.now()
        if now.hour == 10 and now.minute == 0:
            if hasattr(self, 'sleep_announced'):
                return

            print("\n" + "="*70)
            print(f"😴 SLEEP MODE - {datetime.now().strftime('%H:%M:%S')}")
            print("다음 거래일 08:29까지 대기")
            print("="*70)

            # 초기화
            self.auth = None
            self.api = None
            self.past_data = {}
            if hasattr(self, 'phase2_instance'):
                del self.phase2_instance

            self.sleep_announced = True

        # 10:01 이후에는 플래그 리셋
        elif now.hour == 10 and now.minute == 1:
            if hasattr(self, 'sleep_announced'):
                del self.sleep_announced

    def wait_mode(self, message: str):
        """대기 모드 표시"""
        now = datetime.now()

        # 1분마다 한 번만 출력
        if now.second < 30:
            print(f"\r⏰ [{now.strftime('%H:%M')}] {message}", end="", flush=True)

        time.sleep(30)

    def is_trading_day(self, date: datetime) -> bool:
        """거래일 여부 확인"""
        # 주말 체크
        if date.weekday() not in self.TRADING_DAYS:
            return False

        # TODO: 공휴일 체크 추가

        return True

    def minutes_until_wake(self) -> int:
        """거래 시작까지 남은 시간 (분)"""
        now = datetime.now()
        wake_time = now.replace(hour=8, minute=29, second=0)

        # 오늘 08:29가 이미 지났으면 내일
        if now >= wake_time:
            wake_time += timedelta(days=1)

            # 주말 스킵
            while wake_time.weekday() not in self.TRADING_DAYS:
                wake_time += timedelta(days=1)

        diff = wake_time - now
        return int(diff.total_seconds() / 60)

    def _check_api_usage(self, phase_name: str):
        """API 사용량 체크"""
        if not self.api:
            return

        usage = self.api.get_api_usage()
        if usage:
            print(f"📊 [{phase_name}] API: {usage.get('일일_사용', '?')}/{usage.get('일일_한도', '?')} ({usage.get('사용률', '?')})")

    def _generate_daily_report(self):
        """일일 거래 리포트 생성"""
        print("\n📋 일일 거래 리포트")
        print(f"   날짜: {datetime.now().strftime('%Y-%m-%d')}")
        print(f"   실행 시간: 08:29 ~ 10:00")
        # TODO: 실제 거래 통계 추가
        print("   [거래 내역은 Phase 4, 5 구현 후 추가]")


def test_mode():
    """테스트 모드 - 즉시 실행"""
    print("🧪 테스트 모드 실행")
    print("=" * 70)

    app = ChulAutoStock(is_real=True)

    # 바로 실행
    print("Phase 0: API 인증")
    app.wake_up()

    if app.auth and app.api:
        print("\nPhase 1: 데이터 수집")
        app.phase1_past_data()

        if app.past_data:
            print("\nPhase 2: 모니터링")
            app.phase2_monitoring()

            print("\nPhase 3: 최종 선정")
            app.phase3_final_selection()

            print("\nPhase 5: 마감")
            app.phase5_daily_closing()

    print("\n✅ 테스트 완료")


def main():
    """메인 함수"""
    import sys

    # 테스트 모드 체크
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_mode()
    else:
        # 24시간 모드
        app = ChulAutoStock(is_real=True)
        app.run_forever()


if __name__ == "__main__":
    main()