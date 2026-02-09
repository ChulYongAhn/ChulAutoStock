"""
Phase 4: 포지션 관리 (09:00 ~ 09:59)
보유 종목 실시간 모니터링 및 자동 매매
"""

import time
from datetime import datetime
from typing import Dict, List, Optional
from kis_api import KISApi
from slack_service import slack_message, slack_trade
from AutoStockSetting import (
    PROFIT_TARGET, STOP_LOSS,
    FUND_ALLOCATION_MODE, MONITORING_INTERVAL
)
from google_sheet_recorder import GoogleSheetRecorder


class Phase4Position:
    """포지션 관리 클래스"""

    def __init__(self, api: KISApi, use_google_sheets: bool = True):
        """
        초기화

        Args:
            api: KIS API 클라이언트
            use_google_sheets: 구글 시트 기록 사용 여부
        """
        self.api = api
        self.positions = {}  # 보유 종목 정보
        self.target_stocks = []  # Phase 3에서 선정된 종목

        # 익절/손절 기준 (AutoStockSetting에서 가져옴)
        self.PROFIT_TARGET = PROFIT_TARGET  # 익절 목표
        self.STOP_LOSS = STOP_LOSS  # 손절

        # 매매 기록
        self.trade_history = []

        # 구글 시트 레코더 초기화
        self.sheet_recorder = None
        if use_google_sheets:
            try:
                self.sheet_recorder = GoogleSheetRecorder()
                print("✅ 구글 시트 연동 활성화")
            except Exception as e:
                print(f"⚠️ 구글 시트 연동 실패: {e}")
                print("   로컬 기록만 진행합니다.")

    def set_target_stocks(self, stocks: List[Dict]):
        """
        Phase 3에서 선정된 매수 대상 종목 설정

        Args:
            stocks: 매수 대상 종목 리스트
        """
        self.target_stocks = stocks
        print(f"\n📌 매수 대상 종목 {len(stocks)}개 설정 완료")

    def execute_buy_orders(self) -> bool:
        """
        08:59에 매수 주문 실행

        Returns:
            성공 여부
        """
        if not self.target_stocks:
            print("⚠️ 매수 대상 종목이 없습니다")
            slack_message("⚠️ Phase 4: 매수 대상 종목 없음")
            return False

        # 계좌 잔고 확인
        balance = self.api.get_balance()
        if not balance:
            print("❌ 계좌 조회 실패")
            return False

        available_cash = balance.get("주문가능현금", 0)
        print(f"\n💰 주문 가능 현금: {available_cash:,}원")

        if available_cash <= 0:
            print("⚠️ 주문 가능 현금이 없습니다")
            slack_message(f"⚠️ Phase 4: 주문 가능 현금 없음")
            return False

        # 종목당 투자 금액 계산 (균등 분할)
        per_stock_amount = available_cash // len(self.target_stocks)
        print(f"   종목당 투자금: {per_stock_amount:,}원")

        # Slack 알림: 매수 시작
        slack_msg = f"💰 **Phase 4 매수 시작**\n"
        slack_msg += f"• 가용 현금: {available_cash:,}원\n"
        slack_msg += f"• 종목당 투자금: {per_stock_amount:,}원\n"
        slack_msg += f"• 대상 종목: {len(self.target_stocks)}개"
        slack_message(slack_msg)

        success_count = 0
        buy_details = []

        for stock in self.target_stocks:
            code = stock.get("종목코드")
            name = stock.get("종목명")
            current_price = stock.get("현재가", 0)

            if current_price <= 0:
                # 현재가 재조회
                price_info = self.api.get_current_price(code)
                if price_info:
                    current_price = price_info.get("현재가", 0)

            if current_price > 0:
                # 매수 수량 계산
                quantity = per_stock_amount // current_price

                if quantity > 0:
                    print(f"\n🛒 매수 주문: {name}({code})")
                    print(f"   수량: {quantity}주 × {current_price:,}원")

                    # 시장가 매수 주문
                    result = self.api.buy_stock(code, quantity, order_type="01")

                    if result:
                        print(f"   ✅ 주문 성공: {result.get('주문번호')}")
                        success_count += 1

                        # 포지션 정보 저장
                        self.positions[code] = {
                            "종목명": name,
                            "매수수량": quantity,
                            "매수가": current_price,
                            "현재가": current_price,
                            "수익률": 0.0,
                            "상태": "보유",
                            "경고": False
                        }

                        # Slack용 매수 정보 저장
                        buy_details.append(f"✅ {name}: {quantity}주 × {current_price:,}원")

                        # 개별 매수 알림
                        slack_trade(
                            action="매수",
                            stock_code=code,
                            stock_name=name,
                            quantity=quantity,
                            price=current_price,
                            amount=quantity * current_price
                        )

                        # 구글 시트 기록
                        if self.sheet_recorder:
                            self.sheet_recorder.record_buy(
                                code=code,
                                name=name,
                                price=current_price,
                                quantity=quantity,
                                amount=quantity * current_price,
                                memo=f"Phase3 선정 종목"
                            )
                    else:
                        print(f"   ❌ 주문 실패")
                        buy_details.append(f"❌ {name}: 주문 실패")

        # Slack 알림: 매수 결과
        result_msg = f"📊 **Phase 4 매수 완료**\n"
        result_msg += f"• 성공: {success_count}/{len(self.target_stocks)}개\n\n"
        for detail in buy_details:
            result_msg += f"{detail}\n"
        slack_message(result_msg)

        print(f"\n📊 매수 결과: {success_count}/{len(self.target_stocks)} 종목 주문 성공")
        return success_count > 0

    def monitor_positions(self):
        """
        보유 종목 실시간 모니터링 (5초 간격)
        """
        if not self.positions:
            # 보유 종목 조회
            stocks = self.api.get_stock_balance()
            if stocks:
                for stock in stocks:
                    code = stock.get("종목코드")
                    self.positions[code] = {
                        "종목명": stock.get("종목명"),
                        "매수수량": stock.get("보유수량"),
                        "매수가": stock.get("매입단가"),
                        "현재가": stock.get("현재가"),
                        "수익률": stock.get("수익률"),
                        "상태": "보유",
                        "경고": False
                    }

        if not self.positions:
            return

        print(f"\n📊 포지션 모니터링 - {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 60)

        for code, position in self.positions.items():
            if position.get("상태") != "보유":
                continue

            # 현재가 조회
            price_info = self.api.get_current_price(code)
            if not price_info:
                continue

            current_price = price_info.get("현재가", 0)
            if current_price <= 0:
                continue

            # 수익률 계산
            buy_price = position.get("매수가", 0)
            if buy_price > 0:
                profit_rate = ((current_price - buy_price) / buy_price) * 100
            else:
                profit_rate = 0

            position["현재가"] = current_price
            position["수익률"] = profit_rate

            # 상태 표시
            status_icon = "🟢" if profit_rate > 0 else "🔴" if profit_rate < 0 else "⚪"
            print(f"{status_icon} {position['종목명']}: {profit_rate:+.2f}% ({current_price:,}원)")

            # 매도 조건 체크
            self._check_sell_conditions(code, position, profit_rate)

    def _check_sell_conditions(self, code: str, position: Dict, profit_rate: float):
        """
        매도 조건 체크 및 실행

        Args:
            code: 종목 코드
            position: 포지션 정보
            profit_rate: 수익률
        """
        quantity = position.get("매수수량", 0)
        stock_name = position.get("종목명", "")

        # 1. +4% 이상: 전량 매도
        if profit_rate >= self.PROFIT_TARGET:
            print(f"   🎯 익절 목표 달성! +{profit_rate:.2f}% → 전량 매도")
            slack_message(f"🎯 익절 목표 달성! {stock_name} +{profit_rate:.2f}% → 전량 매도")
            self._execute_sell(code, quantity, f"익절(+{self.PROFIT_TARGET}%)")
            position["상태"] = "매도완료"

        # 2. -2% 이하: 전량 손절
        elif profit_rate <= self.STOP_LOSS:
            print(f"   ⛔ 손절선 도달! {profit_rate:.2f}% → 전량 매도")
            slack_message(f"⛔ 손절! {stock_name} {profit_rate:.2f}% → 전량 매도")
            self._execute_sell(code, quantity, "손절(-2%)")
            position["상태"] = "손절완료"

    def _execute_sell(self, code: str, quantity: int, reason: str):
        """
        매도 주문 실행

        Args:
            code: 종목 코드
            quantity: 매도 수량
            reason: 매도 사유
        """
        result = self.api.sell_stock(code, quantity, order_type="01")  # 시장가 매도
        stock_name = self.positions[code].get("종목명")
        current_price = self.positions[code].get("현재가", 0)

        if result:
            print(f"      ✅ 매도 주문 성공: {result.get('주문번호')}")

            # 거래 기록
            self.trade_history.append({
                "시간": datetime.now().strftime("%H:%M:%S"),
                "종목코드": code,
                "종목명": stock_name,
                "구분": "매도",
                "수량": quantity,
                "사유": reason
            })

            # Slack 매도 알림
            profit = None
            if "익절" in reason:
                buy_price = self.positions[code].get("매수가", 0)
                if buy_price > 0:
                    profit = ((current_price - buy_price) / buy_price) * 100

            slack_trade(
                action="매도",
                stock_code=code,
                stock_name=stock_name,
                quantity=quantity,
                price=current_price,
                amount=quantity * current_price,
                profit=profit
            )

            # 구글 시트 기록
            if self.sheet_recorder:
                # 매도 유형 결정
                if "익절" in reason:
                    sell_type = "익절"
                elif "손절" in reason:
                    sell_type = "손절"
                else:
                    sell_type = "기타"

                self.sheet_recorder.record_sell(
                    code=code,
                    name=stock_name,
                    price=current_price,
                    quantity=quantity,
                    sell_type=sell_type,
                    memo=reason
                )
        else:
            print(f"      ❌ 매도 주문 실패")

    def close_all_positions(self):
        """
        09:59 - 모든 포지션 청산
        """
        print("\n" + "="*60)
        print("🏁 일일 청산 시작")
        print("="*60)

        # Slack 알림: 청산 시작
        slack_message("🏁 Phase 4: 일일 청산 시작 (09:59)")

        # 보유 종목 조회
        stocks = self.api.get_stock_balance()
        if not stocks:
            print("보유 종목 없음")
            slack_message("보유 종목 없음 - 청산 대상 없음")
            return

        sell_results = []

        for stock in stocks:
            code = stock.get("종목코드")
            name = stock.get("종목명")
            quantity = stock.get("보유수량")
            profit_rate = stock.get("수익률", 0)
            current_price = stock.get("현재가", 0)

            if quantity > 0:
                print(f"\n📤 {name}({code}) 전량 매도")
                print(f"   수량: {quantity}주, 수익률: {profit_rate:+.2f}%")

                # 시장가 매도
                result = self.api.sell_stock(code, quantity, order_type="01")

                if result:
                    print(f"   ✅ 매도 주문 성공")
                    sell_results.append(f"✅ {name}: {profit_rate:+.2f}%")

                    # 개별 매도 알림
                    slack_trade(
                        action="청산매도",
                        stock_code=code,
                        stock_name=name,
                        quantity=quantity,
                        price=current_price,
                        amount=quantity * current_price,
                        profit=profit_rate
                    )

                    # 구글 시트 기록
                    if self.sheet_recorder:
                        self.sheet_recorder.record_sell(
                            code=code,
                            name=name,
                            price=current_price,
                            quantity=quantity,
                            sell_type="청산",
                            memo=f"09:59 일일청산 (수익률: {profit_rate:+.2f}%)"
                        )
                else:
                    print(f"   ❌ 매도 주문 실패")
                    sell_results.append(f"❌ {name}: 매도 실패")

        # Slack 알림: 청산 결과
        result_msg = "📊 **일일 청산 완료**\n\n"
        for result in sell_results:
            result_msg += f"{result}\n"
        slack_message(result_msg)

        print("\n청산 완료!")

    def get_daily_report(self) -> Dict:
        """
        일일 거래 리포트 생성

        Returns:
            리포트 딕셔너리
        """
        report = {
            "거래일": datetime.now().strftime("%Y-%m-%d"),
            "총_거래횟수": len(self.trade_history),
            "매수_종목수": len(self.target_stocks),
            "익절_횟수": 0,
            "손절_횟수": 0,
            "거래_내역": self.trade_history
        }

        # 익절/손절 카운트
        for trade in self.trade_history:
            if "익절" in trade.get("사유", ""):
                report["익절_횟수"] += 1
            elif "손절" in trade.get("사유", ""):
                report["손절_횟수"] += 1

        return report

    def run(self):
        """
        Phase 4 실행 (09:00 ~ 09:59)
        """
        current_time = datetime.now()

        # 09:00 ~ 09:59 동안 모니터링 (AutoStockSetting.MONITORING_INTERVAL 사용)
        while current_time.hour == 9 and current_time.minute < 59:
            self.monitor_positions()
            time.sleep(MONITORING_INTERVAL)  # 설정된 간격으로 대기
            current_time = datetime.now()

        # 09:59 - 전량 청산
        if current_time.hour == 9 and current_time.minute == 59:
            self.close_all_positions()

            # 구글 시트 일별 통계 업데이트
            if self.sheet_recorder:
                self.sheet_recorder.update_daily_stats()

        return self.get_daily_report()


# 테스트 코드
if __name__ == "__main__":
    from kis_auth import KISAuth
    from kis_api import KISApi

    print("="*60)
    print("Phase 4: 포지션 관리 테스트")
    print("="*60)

    # API 초기화
    auth = KISAuth(is_real=True)
    api = KISApi(auth)

    # Phase 4 실행
    phase4 = Phase4Position(api)

    # 테스트용 타겟 종목 설정
    test_stocks = [
        {"종목코드": "005930", "종목명": "삼성전자", "현재가": 70000}
    ]
    phase4.set_target_stocks(test_stocks)

    # 모니터링 테스트 (1회만)
    phase4.monitor_positions()