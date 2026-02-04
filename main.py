"""
ChulAutoStock - 자동 주식 트레이딩 프로젝트
한국투자증권 API 사용
"""

from datetime import datetime
from dotenv import load_dotenv

# 모듈 임포트
from phase0_auth import Phase0Auth
from phase1_past_data import Phase1PastData
from phase2_monitoring import Phase2Monitoring
from phase3_scoring import Phase3Scoring

# .env 파일 로드
load_dotenv()


class ChulAutoStock:
    """메인 프로그램 클래스"""

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

    def phase0_auth(self) -> bool:
        """
        Phase 0: API 인증

        Returns:
            성공 여부
        """
        phase0 = Phase0Auth(is_real=self.is_real)
        self.auth, self.api = phase0.run()

        if not self.auth or not self.api:
            return False

        # API 사용량 체크
        self._check_api_usage("Phase 0")
        return True

    def phase1_past_data(self) -> bool:
        """
        Phase 1: 과거 데이터 조회

        Returns:
            성공 여부
        """
        phase1 = Phase1PastData()
        self.past_data = phase1.run()

        if not self.past_data:
            print("❌ Phase 1 실패: 전일 데이터를 가져오지 못했습니다.")
            return False

        # API 사용량 체크 (Phase 1은 pykrx 사용이므로 한투 API 사용량과 무관하지만 참고용)
        self._check_api_usage("Phase 1")

        return True

    def phase2_monitoring(self) -> list:
        """
        Phase 2: 실시간 모니터링

        Returns:
            필터링된 종목 리스트
        """
        phase2 = Phase2Monitoring(self.api, self.past_data)
        filtered_stocks = phase2.run()

        # API 사용량 체크
        self._check_api_usage("Phase 2")

        return filtered_stocks

    def phase3_scoring(self, filtered_stocks: list) -> list:
        """
        Phase 3: 스코어링 및 순위화

        Args:
            filtered_stocks: Phase 2에서 필터링된 종목

        Returns:
            상위 3개 종목
        """
        if not filtered_stocks:
            print("\n⚠️  Phase 3 스킵: 필터링된 종목이 없습니다.")
            return []

        phase3 = Phase3Scoring(filtered_stocks)
        top_stocks = phase3.run()

        # API 사용량 체크
        self._check_api_usage("Phase 3")

        return top_stocks

    def _check_api_usage(self, phase_name: str):
        """
        API 사용량 체크 및 출력

        Args:
            phase_name: Phase 이름
        """
        if not self.api:
            return

        usage = self.api.get_api_usage()
        if usage:
            print(f"\n📊 [{phase_name} 완료] API 사용량:")
            print(f"   일일: {usage.get('일일_사용', 'N/A')}/{usage.get('일일_한도', 'N/A')} " +
                  f"(남은횟수: {usage.get('일일_남은횟수', 'N/A')}, 사용률: {usage.get('사용률', 'N/A')})")
        else:
            print(f"\n📊 [{phase_name} 완료] API 사용량 조회 실패")

    def run_once(self):
        """단일 실행 모드"""
        print("\n" + "🚀 ChulAutoStock 단일 실행 모드")

        # Phase 0: 인증
        if not self.phase0_auth():
            return

        # Phase 1: 전일 데이터
        if not self.phase1_past_data():
            return

        # Phase 2: 모니터링
        filtered_stocks = self.phase2_monitoring()

        # Phase 3: 스코어링
        top_stocks = self.phase3_scoring(filtered_stocks)

        print("\n" + "="*50)
        print("✅ 모든 Phase 완료!")
        print(f"   최종 선정: {len(top_stocks)}개 종목")
        print("="*50)

    def run_continuous(self):
        """
        연속 실행 모드
        """
        print("\n" + "="*70)
        print("🔄 ChulAutoStock 연속 실행 모드")
        print("   완료 즉시 다시 실행")
        print("   중단하려면 Ctrl+C를 누르세요")
        print("="*70)

        # Phase 0: 인증
        if not self.phase0_auth():
            return

        # Phase 1: 전일 데이터 (한 번만 실행)
        if not self.phase1_past_data():
            return

        iteration = 0
        try:
            while True:
                iteration += 1
                current_time = datetime.now().strftime("%H:%M:%S")

                print(f"\n\n{'='*20} 반복 #{iteration} - {current_time} {'='*20}")

                # Phase 2: 모니터링
                filtered_stocks = self.phase2_monitoring()

                # Phase 3: 스코어링 (08:59:00 ~ 08:59:50 사이에만)
                now = datetime.now()
                if now.hour == 8 and 59 <= now.minute <= 59:
                    top_stocks = self.phase3_scoring(filtered_stocks)
                    if top_stocks:
                        print("\n🎯 장 시작 직전 최종 선정 완료!")

                # 바로 다음 반복 시작 (대기 없음)
                print("\n➡️  즉시 다시 실행...")

        except KeyboardInterrupt:
            print("\n\n⚠️  사용자에 의해 중단되었습니다.")
            print(f"총 {iteration}회 실행")

    def test_account(self):
        """계좌 정보 테스트"""
        print("\n" + "="*50)
        print("[ 계좌 정보 테스트 ]")
        print("="*50)

        # Phase 0: 인증
        if not self.phase0_auth():
            return

        # 계좌 잔고 조회
        balance = self.api.get_balance()
        if balance:
            print("\n📊 계좌 정보:")
            print(f"   주문가능현금: {balance['주문가능현금']:,}원")
            print(f"   총평가금액: {balance['총평가금액']:,}원")
            print(f"   평가손익: {balance['평가손익']:+,}원 ({balance['수익률']:+.2f}%)")

        # 보유 주식 조회
        stocks = self.api.get_stock_balance()
        if stocks:
            print(f"\n📈 보유 종목: {len(stocks)}개")
            for stock in stocks:
                print(f"   {stock['종목명']}: {stock['보유수량']:,}주")
        else:
            print("\n📈 보유 종목: 없음")


def main():
    """메인 함수"""
    print("="*70)
    print(" ChulAutoStock - 한국투자증권 API 자동 트레이딩")
    print(f" 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    print("\n📌 연속 실행 모드로 시작합니다")
    print("   완료 즉시 다시 실행")
    print("   종료하려면 Ctrl+C를 누르세요")

    # 바로 연속 실행 모드 시작 (대기 없음)
    app = ChulAutoStock(is_real=True)  # 실전 모드
    app.run_continuous()


if __name__ == "__main__":
    main()