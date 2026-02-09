"""
ChulAutoStock - 24시간 자동 주식 트레이딩 시스템
매일 08:29 ~ 10:00 자동 실행
"""

import time
from datetime import datetime, timedelta
from typing import Dict
from dotenv import load_dotenv

# Phase 모듈 임포트
from phase0_auth import Phase0Auth
from phase1_past_data import Phase1PastData
from phase2_monitoring import Phase2Monitoring
from phase3_scoring import Phase3Scoring
from phase4_position import Phase4Position
from phase5_closing import Phase5Closing

# .env 파일 로드
load_dotenv()


class ChulAutoStock:
    """24시간 자동 트레이딩 시스템"""

    def __init__(self, is_real: bool = None):
        """
        초기화

        Args:
            is_real: True=실전, False=모의투자, None=.env에서 읽기
        """
        # .env에서 모드 설정 읽기
        if is_real is None:
            import os
            env_mode = os.getenv("IS_REAL_TRADING", "false").lower()
            self.is_real = env_mode == "true"
        else:
            self.is_real = is_real
        self.auth = None
        self.api = None
        self.past_data = {}
        self.selected_stocks = []  # Phase 3에서 선정된 종목
        self.phase4_report = {}  # Phase 4 거래 리포트
        self.phase4_instance = None  # Phase 4 인스턴스

        # 거래 시간 설정
        self.RESET_TIME = (8, 28)     # 08:28 초기화
        self.WAKE_TIME = (8, 29)      # 08:29 시작
        self.PHASE1_TIME = (8, 30)    # 08:30 Phase 1
        self.PHASE2_TIME = (8, 35)    # 08:35 Phase 2 시작
        self.PHASE3_TIME = (8, 58)    # 08:58 Phase 3
        self.MARKET_OPEN = (9, 0)     # 09:00 장 시작
        self.PHASE5_TIME = (9, 59)    # 09:59 Phase 5
        self.SLEEP_TIME = (10, 0)     # 10:00 종료

        self.TRADING_DAYS = [0, 1, 2, 3, 4]  # 월~금

        # Phase 완료 상태 추적
        self.phase_completed = {
            'phase0': False,
            'phase1': False,
            'phase2_started': False,
            'phase3': False,
            'phase4': False,
            'phase5': False
        }

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

                # 늦은 시작 체크 - Phase 0가 완료되지 않았는데 08:30이 넘었다면 종료
                if current_time > self.WAKE_TIME and not self.phase_completed['phase0']:
                    print("\n⚠️  경고: 프로그램이 너무 늦게 시작되었습니다!")
                    print(f"   현재 시간: {now.strftime('%H:%M')}")
                    print("   08:29 이전에 프로그램을 실행해야 합니다.")
                    print("   프로그램을 종료합니다.")
                    break

                # 08:28 - 일일 초기화
                if current_time == self.RESET_TIME:
                    self.daily_reset()

                # 08:29 - 깨어나기
                elif current_time == self.WAKE_TIME:
                    self.wake_up()

                # 08:30 - Phase 1 (Phase 0 완료 필수)
                elif current_time == self.PHASE1_TIME:
                    if not self.phase_completed['phase0']:
                        print("⚠️ Phase 0가 완료되지 않아 Phase 1 건너뜀")
                    elif self.auth and self.api:
                        self.phase1_past_data()

                # 08:35 ~ 08:57 - Phase 2 반복 (Phase 1 완료 필수)
                elif self.PHASE2_TIME <= current_time < self.PHASE3_TIME:
                    if not self.phase_completed['phase1']:
                        if not self.phase_completed.get('phase2_warning'):
                            print("⚠️ Phase 1이 완료되지 않아 Phase 2 실행 불가")
                            self.phase_completed['phase2_warning'] = True
                    elif self.auth and self.api and self.past_data:
                        self.phase2_monitoring()
                        self.phase_completed['phase2_started'] = True

                # 08:58 - Phase 3 (Phase 2 시작 필수)
                elif current_time == self.PHASE3_TIME:
                    if not self.phase_completed['phase2_started']:
                        print("⚠️ Phase 2가 실행되지 않아 Phase 3 건너뜀")
                    elif self.auth and self.api:
                        self.phase3_final_selection()

                # 08:59 ~ 09:58 - Phase 4 (Phase 3 완료 필수)
                elif (current_time[0] == 8 and current_time[1] == 59) or \
                     (self.MARKET_OPEN <= current_time < self.PHASE5_TIME):
                    if not self.phase_completed['phase3']:
                        if not self.phase_completed.get('phase4_warning'):
                            print("⚠️ Phase 3가 완료되지 않아 Phase 4 실행 불가")
                            self.phase_completed['phase4_warning'] = True
                    elif self.auth and self.api:
                        self.phase4_position_management()

                # 09:59 - Phase 5
                elif current_time == self.PHASE5_TIME:
                    if self.auth and self.api:
                        self.phase5_daily_closing()

                # 10:00 이후 - 대기 모드
                elif current_time >= self.SLEEP_TIME:
                    self.enter_sleep_mode()

                # 08:28 이전 - 대기 모드
                elif current_time < self.RESET_TIME:
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

        # Phase 0 완료 표시
        self.phase_completed['phase0'] = True

        # API 사용량 체크
        self._check_api_usage("Wake Up")

        print("✅ 거래 준비 완료! Phase 1 대기 중...")

    def phase1_past_data(self):
        """Phase 1: 과거 데이터 수집"""
        phase1 = Phase1PastData()
        self.past_data = phase1.run()

        if self.past_data:
            print(f"✅ Phase 1 완료: {len(self.past_data)}개 종목 데이터 수집")
            self.phase_completed['phase1'] = True
        else:
            print("❌ Phase 1 실패: 데이터 수집 실패")

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
            # Phase 2 최종 결과를 Slack으로 전송
            self.phase2_instance.send_final_result()

            filtered = self.phase2_instance.get_filtered_stocks()

            if filtered:
                phase3 = Phase3Scoring(filtered)
                top_stocks = phase3.run()

                if top_stocks:
                    print("\n🎯 Phase 3 최종 선정 완료!")
                    print(f"   매수 예정: {len(top_stocks)}개 종목")
                    self.phase_completed['phase3'] = True
                    self.selected_stocks = top_stocks  # 선정 종목 저장

                    for stock in top_stocks:
                        print(f"   - {stock['종목명']} ({stock['종목코드']})")

                    # Phase 4 인스턴스 생성 및 종목 설정
                    if self.api:
                        self.phase4_instance = Phase4Position(self.api)
                        self.phase4_instance.set_target_stocks(top_stocks)

                        # 08:59에 매수 주문 실행 예약
                        print("\n⏰ 08:59에 매수 주문 예정")
                else:
                    print("⚠️ Phase 3: 선정된 종목 없음")
            else:
                print("⚠️ Phase 3: 필터링된 종목 없음")

        self._check_api_usage("Phase 3")

    def phase4_position_management(self):
        """Phase 4: 포지션 관리"""
        current_time = datetime.now()

        # 08:59 - 매수 주문 실행
        if current_time.hour == 8 and current_time.minute == 59:
            if self.phase4_instance and not self.phase_completed.get('phase4_buy'):
                print("\n🛒 Phase 4: 매수 주문 실행")
                success = self.phase4_instance.execute_buy_orders()
                if success:
                    self.phase_completed['phase4_buy'] = True
                    self.phase_completed['phase4'] = True

        # 09:00 ~ 09:58 - 포지션 모니터링
        elif current_time.hour == 9 and current_time.minute < 59:
            if self.phase4_instance:
                # 5초마다 모니터링 (30초 주기 대신)
                if not hasattr(self, 'last_monitor_time'):
                    self.last_monitor_time = datetime.now()

                time_diff = (datetime.now() - self.last_monitor_time).seconds
                if time_diff >= 5:  # 5초마다 모니터링
                    self.phase4_instance.monitor_positions()
                    self.last_monitor_time = datetime.now()

    def phase5_daily_closing(self):
        """Phase 5: 일일 마감"""
        print("\n" + "="*70)
        print(f"🏁 일일 마감 - {datetime.now().strftime('%H:%M:%S')}")
        print("="*70)

        # Phase 4 리포트 가져오기
        if self.phase4_instance:
            self.phase4_report = self.phase4_instance.get_daily_report()

        # Phase 5 실행
        if self.api:
            phase5 = Phase5Closing(self.api)
            final_report = phase5.run(self.phase4_report)

            # 리포트 저장
            self._save_final_report(final_report)

        # API 사용량 최종 체크
        self._check_api_usage("Daily Closing")

        print("\n😴 대기 모드 전환 준비...")
        self.phase_completed['phase5'] = True

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
            self.selected_stocks = []
            self.phase4_report = {}
            if hasattr(self, 'phase2_instance'):
                del self.phase2_instance
            if hasattr(self, 'phase4_instance'):
                del self.phase4_instance

            # Phase 완료 상태 초기화
            self.phase_completed = {
                'phase0': False,
                'phase1': False,
                'phase2_started': False,
                'phase3': False,
                'phase4': False,
                'phase5': False
            }

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

    def daily_reset(self):
        """08:28 - 일일 초기화"""
        print("\n" + "="*70)
        print(f"🔄 DAILY RESET - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("새로운 거래일 준비 중...")
        print("="*70)

        # 모든 상태 초기화
        self.auth = None
        self.api = None
        self.past_data = {}
        self.selected_stocks = []
        self.phase4_report = {}
        if hasattr(self, 'phase2_instance'):
            del self.phase2_instance
        if hasattr(self, 'phase4_instance'):
            del self.phase4_instance

        # Phase 완료 상태 초기화
        self.phase_completed = {
            'phase0': False,
            'phase1': False,
            'phase2_started': False,
            'phase3': False,
            'phase4': False,
            'phase5': False
        }

        # 경고 플래그 초기화
        for key in list(self.phase_completed.keys()):
            if 'warning' in key:
                del self.phase_completed[key]

        print("✅ 초기화 완료! 08:29 거래 시작 대기 중...")

    def _save_final_report(self, report: Dict):
        """최종 리포트 저장"""
        import json
        import os

        # reports 디렉토리 생성
        os.makedirs("reports", exist_ok=True)

        # 파일명: reports/20240115_final.json
        today = datetime.now().strftime("%Y%m%d")
        filename = f"reports/{today}_final.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"📁 최종 리포트 저장: {filename}")
        except Exception as e:
            print(f"❌ 리포트 저장 실패: {e}")


def main():
    """메인 함수"""
    # 24시간 모드 (.env 설정 따름)
    app = ChulAutoStock()  # is_real 파라미터 제거 → .env에서 읽음

    # 모드 확인 메시지
    mode_name = "🔴 실전투자" if app.is_real else "🟢 모의투자"
    print(f"\n{mode_name} 모드로 실행합니다.")

    app.run_forever()


if __name__ == "__main__":
    main()