"""
Phase 5: 일일 청산 및 리포트 (09:59 ~ 10:00)
당일 거래 마감 및 다음 거래일 준비
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from kis_api import KISApi
from slack_service import slack_message, slack_daily_report


class Phase5Closing:
    """일일 마감 클래스"""

    def __init__(self, api: KISApi):
        """
        초기화

        Args:
            api: KIS API 클라이언트
        """
        self.api = api
        self.report_dir = "reports"
        self.log_dir = "logs"

        # 디렉토리 생성
        os.makedirs(self.report_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

    def cancel_pending_orders(self) -> int:
        """
        미체결 주문 취소

        Returns:
            취소한 주문 수
        """
        print("\n📋 미체결 주문 확인 중...")

        # 주문 내역 조회
        orders = self.api.get_orders()
        if not orders:
            print("   미체결 주문 없음")
            return 0

        cancel_count = 0
        for order in orders:
            # 미체결 주문 확인
            if order.get("체결수량", 0) < order.get("주문수량", 0):
                order_no = order.get("주문번호")
                stock_name = order.get("종목명")
                order_type = order.get("매매구분")

                print(f"   ❌ 미체결 취소: {stock_name} {order_type}")
                # TODO: 주문 취소 API 호출
                cancel_count += 1

        return cancel_count

    def liquidate_all_positions(self) -> Dict:
        """
        모든 보유 종목 청산

        Returns:
            청산 결과
        """
        print("\n🏁 보유 종목 전량 청산")
        print("-" * 60)

        # 보유 종목 조회
        stocks = self.api.get_stock_balance()
        if not stocks:
            print("   보유 종목 없음")
            slack_message("보유 종목 없음 - 청산 대상 없음")
            return {"청산_종목수": 0, "총_평가손익": 0}

        # Slack 알림: 청산 시작
        slack_message(f"💰 일일 청산 시작 - {len(stocks)}개 종목")

        total_profit = 0
        success_count = 0
        fail_count = 0
        liquidation_details = []

        for stock in stocks:
            code = stock.get("종목코드")
            name = stock.get("종목명")
            quantity = stock.get("보유수량", 0)
            profit = stock.get("평가손익", 0)
            profit_rate = stock.get("수익률", 0)

            if quantity <= 0:
                continue

            print(f"\n📤 {name}({code})")
            print(f"   수량: {quantity:,}주")
            print(f"   수익: {profit:+,}원 ({profit_rate:+.2f}%)")

            # 시장가 매도 주문
            result = self.api.sell_stock(code, quantity, order_type="01")

            if result:
                print(f"   ✅ 매도 주문 접수: {result.get('주문번호')}")
                success_count += 1
                total_profit += profit
                liquidation_details.append(f"✅ {name}: {profit_rate:+.2f}% ({profit:+,}원)")
            else:
                print(f"   ❌ 매도 주문 실패")
                fail_count += 1
                liquidation_details.append(f"❌ {name}: 매도 실패")

        print("\n" + "="*60)
        print(f"청산 완료: 성공 {success_count}건, 실패 {fail_count}건")
        print(f"총 평가손익: {total_profit:+,}원")
        print("="*60)

        # Slack 알림: 청산 결과
        result_msg = f"📊 **일일 청산 결과**\n"
        result_msg += f"• 성공: {success_count}건, 실패: {fail_count}건\n"
        result_msg += f"• 총 평가손익: {total_profit:+,}원\n\n"
        for detail in liquidation_details:
            result_msg += f"{detail}\n"
        slack_message(result_msg)

        return {
            "청산_종목수": success_count,
            "실패_건수": fail_count,
            "총_평가손익": total_profit
        }

    def generate_daily_report(self, phase4_report: Optional[Dict] = None) -> Dict:
        """
        일일 거래 리포트 생성

        Args:
            phase4_report: Phase 4 거래 리포트

        Returns:
            종합 리포트
        """
        print("\n📊 일일 거래 리포트 생성 중...")

        today = datetime.now().strftime("%Y-%m-%d")
        report = {
            "거래일": today,
            "시작시간": "08:29",
            "종료시간": "10:00",
            "계좌정보": {},
            "거래내역": {},
            "수익률": {},
            "API사용량": {}
        }

        # 1. 계좌 정보
        balance = self.api.get_balance()
        if balance:
            report["계좌정보"] = {
                "예수금": balance.get("예수금", 0),
                "총평가금액": balance.get("총평가금액", 0),
                "평가손익": balance.get("평가손익", 0),
                "수익률": balance.get("수익률", 0)
            }

        # 2. 거래 내역 (Phase 4 리포트 병합)
        if phase4_report:
            report["거래내역"] = {
                "매수_종목수": phase4_report.get("매수_종목수", 0),
                "익절_횟수": phase4_report.get("익절_횟수", 0),
                "손절_횟수": phase4_report.get("손절_횟수", 0),
                "총_거래횟수": phase4_report.get("총_거래횟수", 0)
            }

        # 3. 주문 내역
        orders = self.api.get_orders()
        if orders:
            buy_count = sum(1 for o in orders if o.get("매매구분") == "매수")
            sell_count = sum(1 for o in orders if o.get("매매구분") == "매도")
            report["거래내역"]["매수_주문"] = buy_count
            report["거래내역"]["매도_주문"] = sell_count

        # 4. API 사용량
        usage = self.api.get_api_usage()
        if usage:
            report["API사용량"] = {
                "일일_사용": usage.get("일일_사용", 0),
                "일일_한도": usage.get("일일_한도", 0),
                "사용률": usage.get("사용률", "0%")
            }

        # 5. 수익률 계산
        if balance:
            start_amount = balance.get("예수금", 0) + balance.get("매입금액", 0)
            end_amount = balance.get("총평가금액", 0)
            if start_amount > 0:
                daily_return = ((end_amount - start_amount) / start_amount) * 100
                report["수익률"]["일일_수익률"] = round(daily_return, 2)

        return report

    def save_report(self, report: Dict):
        """
        리포트 파일로 저장

        Args:
            report: 리포트 딕셔너리
        """
        # 파일명: reports/2024-01-15_report.json
        today = datetime.now().strftime("%Y%m%d")
        filename = os.path.join(self.report_dir, f"{today}_report.json")

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"📁 리포트 저장: {filename}")

    def print_summary(self, report: Dict):
        """
        리포트 요약 출력

        Args:
            report: 리포트 딕셔너리
        """
        print("\n" + "="*70)
        print(f"              📈 일일 거래 요약 - {report['거래일']}")
        print("="*70)

        # 계좌 정보
        account = report.get("계좌정보", {})
        print("\n💰 계좌 현황")
        print(f"   총 평가금액: {account.get('총평가금액', 0):,}원")
        print(f"   평가 손익: {account.get('평가손익', 0):+,}원")
        print(f"   수익률: {account.get('수익률', 0):+.2f}%")

        # 거래 내역
        trades = report.get("거래내역", {})
        print("\n📊 거래 내역")
        print(f"   매수 종목: {trades.get('매수_종목수', 0)}개")
        print(f"   익절: {trades.get('익절_횟수', 0)}회")
        print(f"   손절: {trades.get('손절_횟수', 0)}회")

        # API 사용량
        api_usage = report.get("API사용량", {})
        print("\n📡 API 사용량")
        print(f"   {api_usage.get('일일_사용', 0)}/{api_usage.get('일일_한도', 0)} ({api_usage.get('사용률', '0%')})")

        # 일일 수익률
        returns = report.get("수익률", {})
        daily_return = returns.get("일일_수익률", 0)
        if daily_return != 0:
            return_icon = "🟢" if daily_return > 0 else "🔴"
            print(f"\n{return_icon} 일일 수익률: {daily_return:+.2f}%")

        print("\n" + "="*70)

    def cleanup_logs(self):
        """
        로그 파일 정리 (30일 이상된 파일 삭제)
        """
        from datetime import timedelta

        print("\n🧹 로그 파일 정리 중...")

        cutoff_date = datetime.now() - timedelta(days=30)
        deleted_count = 0

        for filename in os.listdir(self.log_dir):
            filepath = os.path.join(self.log_dir, filename)
            if os.path.isfile(filepath):
                # 파일 수정 시간 확인
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if mtime < cutoff_date:
                    os.remove(filepath)
                    deleted_count += 1

        if deleted_count > 0:
            print(f"   {deleted_count}개 오래된 로그 파일 삭제")

    def run(self, phase4_report: Optional[Dict] = None) -> Dict:
        """
        Phase 5 실행

        Args:
            phase4_report: Phase 4 리포트

        Returns:
            최종 리포트
        """
        print("\n" + "="*70)
        print(f"🏁 Phase 5: 일일 마감 - {datetime.now().strftime('%H:%M:%S')}")
        print("="*70)

        # Slack 알림: Phase 5 시작
        slack_message("🏁 Phase 5 시작 - 일일 마감 및 리포트")

        # 1. 미체결 주문 취소
        cancel_count = self.cancel_pending_orders()
        if cancel_count > 0:
            slack_message(f"❌ 미체결 주문 {cancel_count}건 취소")

        # 2. 보유 종목 전량 청산
        liquidation_result = self.liquidate_all_positions()

        # 3. 일일 리포트 생성
        report = self.generate_daily_report(phase4_report)
        report["청산결과"] = liquidation_result

        # 4. 리포트 저장
        self.save_report(report)

        # 5. 요약 출력
        self.print_summary(report)

        # 6. Slack으로 일일 리포트 전송
        slack_daily_report(report)

        # 7. 로그 정리
        self.cleanup_logs()

        # Slack 알림: Phase 5 완료
        completion_msg = f"✅ **Phase 5 완료**\n"
        completion_msg += f"• 총 평가손익: {liquidation_result.get('총_평가손익', 0):+,}원\n"
        completion_msg += f"• 일일 수익률: {report.get('수익률', {}).get('일일_수익률', 0):+.2f}%"
        slack_message(completion_msg)

        print("\n✅ Phase 5 완료!")
        return report


# 테스트 코드
if __name__ == "__main__":
    from kis_auth import KISAuth
    from kis_api import KISApi

    print("="*60)
    print("Phase 5: 일일 마감 테스트")
    print("="*60)

    # API 초기화
    auth = KISAuth(is_real=True)
    api = KISApi(auth)

    # Phase 5 실행
    phase5 = Phase5Closing(api)

    # 테스트용 Phase 4 리포트
    test_phase4_report = {
        "매수_종목수": 3,
        "익절_횟수": 1,
        "손절_횟수": 0,
        "총_거래횟수": 4
    }

    # 실행
    final_report = phase5.run(test_phase4_report)