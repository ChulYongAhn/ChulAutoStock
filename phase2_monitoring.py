"""
Phase 2: 실시간 모니터링
100개 종목의 현재가를 조회하고 +2% ~ +4% 범위 종목 필터링
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from kis_api import KISApi
from stock_list import KOSPI_100, get_stock_name
from slack_service import slack_message


class Phase2Monitoring:
    """Phase 2: 실시간 모니터링 및 필터링"""

    def __init__(self, api: KISApi, past_data: Dict):
        """
        초기화

        Args:
            api: KISApi 인스턴스
            past_data: Phase1에서 가져온 전일 데이터
        """
        self.api = api
        self.past_data = past_data
        self.filtered_stocks = []

        # 필터링 조건
        self.min_change_rate = 2.0  # 최소 상승률 2%
        self.max_change_rate = 4.0  # 최대 상승률 4%
        self.max_filtered_stocks = 10  # 최대 필터링 종목 수

    def run(self) -> List[Dict]:
        """
        Phase 2 실행

        Returns:
            필터링된 종목 리스트 (최대 10개)
        """
        print("\n" + "="*50)
        print("[ Phase 2: 실시간 모니터링 시작 ]")
        print(f"시작 시간: {datetime.now().strftime('%H:%M:%S')}")
        print(f"필터링 조건: +{self.min_change_rate}% ~ +{self.max_change_rate}%")
        print("="*50)

        # Slack 알림: Phase 2 시작
        slack_message(f"👀 Phase 2 시작 - 실시간 모니터링 (+{self.min_change_rate}%~+{self.max_change_rate}%)")

        # 전일 데이터 확인
        if not self.past_data:
            print("❌ 전일 데이터가 없습니다. Phase 1을 먼저 실행하세요.")
            return []

        # 종목별 현재가 조회 및 등락률 계산
        monitoring_results = []
        success_count = 0
        fail_count = 0

        print("\n현재가 조회 중...")
        for idx, (code, name) in enumerate(KOSPI_100.items(), 1):
            # 진행상황 표시
            if idx % 20 == 0 or idx == 1:
                print(f"  진행중... [{idx}/{len(KOSPI_100)}]")

            # 전일 데이터가 없으면 스킵
            if code not in self.past_data:
                continue

            # 현재가 조회
            current_data = self._get_current_price(code)
            if not current_data:
                fail_count += 1
                continue

            # 등락률 계산
            past_close = self.past_data[code]['종가']
            current_price = current_data['현재가']
            change_rate = ((current_price - past_close) / past_close) * 100

            # 결과 저장
            monitoring_results.append({
                '종목코드': code,
                '종목명': name,
                '전일종가': past_close,
                '현재가': current_price,
                '등락률': round(change_rate, 2),
                '거래량': current_data['거래량'],
                '거래대금': current_data['거래대금']
            })

            success_count += 1

            # 대기 없이 바로 다음 종목 조회
            # API 응답 속도에 자연스럽게 맞춰짐

        print(f"\n✅ 조회 성공: {success_count}개")
        print(f"❌ 조회 실패: {fail_count}개")

        # 필터링: +2% ~ +4% 범위
        self.filtered_stocks = self._filter_stocks(monitoring_results)

        # 결과 출력
        self._print_results()

        return self.filtered_stocks

    def _get_current_price(self, code: str) -> Optional[Dict]:
        """
        현재가 조회

        Args:
            code: 종목 코드

        Returns:
            현재가 정보
        """
        try:
            return self.api.get_current_price(code)
        except Exception as e:
            return None

    def _filter_stocks(self, stocks: List[Dict]) -> List[Dict]:
        """
        조건에 맞는 종목 필터링

        Args:
            stocks: 전체 모니터링 결과

        Returns:
            필터링된 종목 리스트
        """
        # 조건: +2% ~ +4% 범위
        filtered = [
            stock for stock in stocks
            if self.min_change_rate <= stock['등락률'] <= self.max_change_rate
        ]

        # 등락률 기준 내림차순 정렬
        filtered.sort(key=lambda x: x['등락률'], reverse=True)

        # 상위 10개만 선택
        return filtered[:self.max_filtered_stocks]

    def _print_results(self):
        """결과 출력"""
        print("\n" + "="*50)
        print("[ Phase 2 필터링 결과 ]")
        print("="*50)

        if not self.filtered_stocks:
            print("⚠️  조건에 맞는 종목이 없습니다.")
            slack_message("⚠️ Phase 2: 조건 만족 종목 없음")
            return

        print(f"\n📊 필터링된 종목: {len(self.filtered_stocks)}개\n")

        # Slack 알림: Phase 2 결과
        slack_msg = f"📊 Phase 2 결과 - {len(self.filtered_stocks)}개 종목\n"

        for idx, stock in enumerate(self.filtered_stocks[:3], 1):  # 상위 3개만 Slack 전송
            print(f"{idx:2d}. {stock['종목명']} ({stock['종목코드']})")
            print(f"    현재가: {stock['현재가']:,}원 (전일: {stock['전일종가']:,}원)")
            print(f"    등락률: +{stock['등락률']:.2f}%")
            print(f"    거래량: {stock['거래량']:,}주")
            print(f"    거래대금: {stock['거래대금']:,}원")
            print()

            # Slack 메시지 구성
            slack_msg += f"{idx}. {stock['종목명']}: +{stock['등락률']:.2f}%\n"

        # 나머지 종목도 터미널에는 출력
        for idx, stock in enumerate(self.filtered_stocks[3:], 4):
            print(f"{idx:2d}. {stock['종목명']} ({stock['종목코드']})")
            print(f"    현재가: {stock['현재가']:,}원 (전일: {stock['전일종가']:,}원)")
            print(f"    등락률: +{stock['등락률']:.2f}%")
            print(f"    거래량: {stock['거래량']:,}주")
            print(f"    거래대금: {stock['거래대금']:,}원")
            print()

        slack_message(slack_msg)

    def get_filtered_stocks(self) -> List[Dict]:
        """
        필터링된 종목 반환

        Returns:
            필터링된 종목 리스트
        """
        return self.filtered_stocks

    def run_continuous(self, max_iterations: int = None):
        """
        연속 실행 모드 (대기 없이)

        Args:
            max_iterations: 최대 반복 횟수 (None이면 무한)
        """
        iteration = 0
        print(f"\n🔄 연속 모니터링 모드 시작 (대기 없음)")

        try:
            while max_iterations is None or iteration < max_iterations:
                iteration += 1
                print(f"\n\n{'='*20} 반복 #{iteration} {'='*20}")

                # Phase 2 실행
                self.run()

                # 대기 없이 바로 다음 실행

        except KeyboardInterrupt:
            print("\n\n⚠️  사용자에 의해 중단되었습니다.")

        print(f"\n총 {iteration}회 실행 완료")


# 테스트 코드
if __name__ == "__main__":
    from kis_auth import KISAuth

    print("Phase 2 테스트")

    # 인증
    auth = KISAuth(is_real=True)
    api = KISApi(auth)

    # 가짜 전일 데이터 (테스트용)
    fake_past_data = {}
    for code in list(KOSPI_100.keys())[:10]:  # 10개만 테스트
        fake_past_data[code] = {
            '종가': 50000,  # 임시 값
            '거래량': 1000000
        }

    # Phase 2 실행
    phase2 = Phase2Monitoring(api, fake_past_data)
    results = phase2.run()

    print(f"\n필터링 결과: {len(results)}개 종목")