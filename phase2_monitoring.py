"""
Phase 2: 프리장 종료 시점 모니터링
8시 51분에 코스피100 전 종목의 전일 대비 등락률을 계산하여 슬랙으로 전송
"""

from datetime import datetime
from typing import Dict, List, Optional
from kis_api import KISApi
from AutoStockSetting import KOSPI_100, get_stock_name
from slack_service import slack_message


class Phase2Monitoring:
    """Phase 2: 프리장 종료 시점 등락률 모니터링"""

    def __init__(self, api: KISApi, past_data: Dict):
        """
        초기화

        Args:
            api: KISApi 인스턴스
            past_data: Phase1에서 가져온 전일 데이터
        """
        self.api = api
        self.past_data = past_data
        self.market_data = []  # 전체 시장 데이터

    def run(self) -> List[Dict]:
        """
        Phase 2 실행 - 프리장 종료 시점(8:51)에 한 번만 실행

        Returns:
            전체 종목 데이터 리스트
        """
        current_time = datetime.now()

        print("\n" + "="*50)
        print("[ Phase 2: 프리장 종료 시점 모니터링 ]")
        print(f"실행 시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)

        # 전일 데이터 확인
        if not self.past_data:
            print("❌ 전일 데이터가 없습니다. Phase 1을 먼저 실행하세요.")
            slack_message("❌ Phase 2 실행 실패: 전일 데이터 없음")
            return []

        # 코스피100 전 종목 현재가 조회 및 등락률 계산
        self.market_data = []
        success_count = 0
        fail_count = 0

        print("\n코스피100 전 종목 현재가 조회 중...")
        for idx, (code, name) in enumerate(KOSPI_100.items(), 1):
            # 진행상황 표시
            if idx % 20 == 0 or idx == 1:
                print(f"  진행중... [{idx}/{len(KOSPI_100)}]")

            # 전일 데이터가 없으면 스킵
            if code not in self.past_data:
                fail_count += 1
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
            self.market_data.append({
                '종목코드': code,
                '종목명': name,
                '전일종가': past_close,
                '현재가': current_price,
                '등락률': round(change_rate, 2),
                '거래량': current_data['거래량'],
                '거래대금': current_data['거래대금']
            })

            success_count += 1

        print(f"\n✅ 조회 성공: {success_count}개")
        print(f"❌ 조회 실패: {fail_count}개")

        # 등락률 기준 정렬 (상승 → 하락 순)
        self.market_data.sort(key=lambda x: x['등락률'], reverse=True)

        # 결과 출력 및 슬랙 전송
        self._send_market_summary()

        return self.market_data

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

    def _send_market_summary(self):
        """전체 시장 요약 정보를 슬랙으로 전송"""
        if not self.market_data:
            print("⚠️ 조회된 데이터가 없습니다.")
            return

        # 통계 계산
        up_stocks = [s for s in self.market_data if s['등락률'] > 0]
        down_stocks = [s for s in self.market_data if s['등락률'] < 0]
        flat_stocks = [s for s in self.market_data if s['등락률'] == 0]

        avg_change = sum(s['등락률'] for s in self.market_data) / len(self.market_data)

        # 어제/오늘 날짜
        today = datetime.now()
        yesterday = self.past_data.get('date', '전일')  # past_data에 날짜가 있다면 사용

        # 슬랙 메시지 구성
        slack_msg = f"""📊 **코스피100 프리장 등락률 현황**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
어제: {yesterday}
오늘: {today.strftime('%m월 %d일 %H:%M')} 기준

"""

        # 상승 종목 (상위 20개)
        if up_stocks:
            slack_msg += f"🔴 **상승 종목 ({len(up_stocks)}개)**\n"
            for stock in up_stocks[:20]:  # 상위 20개만
                slack_msg += f"[{stock['종목명']}] {stock['전일종가']:,}원 → {stock['현재가']:,}원 (+{stock['등락률']:.2f}%)\n"
            if len(up_stocks) > 20:
                slack_msg += f"... 외 {len(up_stocks) - 20}개\n"
            slack_msg += "\n"

        # 하락 종목 (하위 20개)
        if down_stocks:
            slack_msg += f"🔵 **하락 종목 ({len(down_stocks)}개)**\n"
            for stock in down_stocks[:20]:  # 상위 20개만
                slack_msg += f"[{stock['종목명']}] {stock['전일종가']:,}원 → {stock['현재가']:,}원 ({stock['등락률']:.2f}%)\n"
            if len(down_stocks) > 20:
                slack_msg += f"... 외 {len(down_stocks) - 20}개\n"
            slack_msg += "\n"

        # 보합 종목
        if flat_stocks:
            slack_msg += f"⚪ **보합 종목 ({len(flat_stocks)}개)**\n"
            for stock in flat_stocks[:5]:  # 최대 5개만
                slack_msg += f"[{stock['종목명']}] {stock['현재가']:,}원 (0.00%)\n"
            if len(flat_stocks) > 5:
                slack_msg += f"... 외 {len(flat_stocks) - 5}개\n"
            slack_msg += "\n"

        # 요약 통계
        slack_msg += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 상승: {len(up_stocks)}개 | 📉 하락: {len(down_stocks)}개 | ➖ 보합: {len(flat_stocks)}개
전체 평균 등락률: {avg_change:+.2f}%

🎯 상승률 TOP 5:
"""
        # 상승률 TOP 5
        for i, stock in enumerate(up_stocks[:5], 1):
            slack_msg += f"{i}. {stock['종목명']}: +{stock['등락률']:.2f}%\n"

        slack_msg += "\n💥 하락률 TOP 5:\n"
        # 하락률 TOP 5
        for i, stock in enumerate(down_stocks[:5], 1):
            slack_msg += f"{i}. {stock['종목명']}: {stock['등락률']:.2f}%\n"

        # 슬랙 전송
        slack_message(slack_msg)

        # 터미널 출력
        print("\n" + "="*50)
        print("[ 프리장 종료 시점 시장 현황 ]")
        print("="*50)
        print(f"상승: {len(up_stocks)}개 | 하락: {len(down_stocks)}개 | 보합: {len(flat_stocks)}개")
        print(f"전체 평균 등락률: {avg_change:+.2f}%")
        print("\n상승률 TOP 10:")
        for i, stock in enumerate(up_stocks[:10], 1):
            print(f"  {i:2d}. {stock['종목명']:12s}: {stock['전일종가']:8,}원 → {stock['현재가']:8,}원 (+{stock['등락률']:.2f}%)")
        print("\n하락률 TOP 10:")
        for i, stock in enumerate(down_stocks[:10], 1):
            print(f"  {i:2d}. {stock['종목명']:12s}: {stock['전일종가']:8,}원 → {stock['현재가']:8,}원 ({stock['등락률']:.2f}%)")

    def get_market_data(self) -> List[Dict]:
        """
        전체 시장 데이터 반환

        Returns:
            전체 종목 데이터 리스트
        """
        return self.market_data

    def get_filtered_stocks(self, min_rate: float = 2.0, max_rate: float = 4.0) -> List[Dict]:
        """
        특정 등락률 범위의 종목만 필터링

        Args:
            min_rate: 최소 등락률
            max_rate: 최대 등락률

        Returns:
            필터링된 종목 리스트
        """
        return [
            stock for stock in self.market_data
            if min_rate <= stock['등락률'] <= max_rate
        ]


# 테스트 코드
if __name__ == "__main__":
    from kis_auth import KISAuth
    from phase1_past_data import Phase1PastData

    print("Phase 2 테스트 - 프리장 종료 시점 모니터링")

    # 인증
    auth = KISAuth(is_real=True)
    api = KISApi(auth)

    # Phase 1 실행하여 전일 데이터 가져오기
    phase1 = Phase1PastData()
    past_data = phase1.run()

    if past_data:
        # Phase 2 실행
        phase2 = Phase2Monitoring(api, past_data)
        market_data = phase2.run()

        print(f"\n전체 조회 결과: {len(market_data)}개 종목")

        # 2~4% 범위 종목만 필터링 (Phase 3에서 활용 가능)
        filtered = phase2.get_filtered_stocks(min_rate=2.0, max_rate=4.0)
        print(f"2~4% 범위 종목: {len(filtered)}개")
    else:
        print("전일 데이터 조회 실패")