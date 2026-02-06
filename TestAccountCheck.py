"""
계좌 정보 조회 테스트
잔액, 보유종목, 수익률 등 확인
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from kis_auth import KISAuth
from kis_api import KISApi

# .env 로드
load_dotenv()


def main():
    """계좌 정보 조회"""
    print("="*60)
    print("💰 계좌 정보 조회")
    print("="*60)

    # 모드 확인
    is_real = os.getenv("IS_REAL_TRADING", "false").lower() == "true"
    mode_name = "🔴 실전투자" if is_real else "🟢 모의투자"

    print(f"\n모드: {mode_name}")
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*60)

    # API 초기화
    auth = KISAuth(is_real=is_real)
    api = KISApi(auth)

    # 토큰 획득
    token = auth.get_token()
    if not token:
        print("❌ API 인증 실패!")
        return

    print(f"✅ API 연결 성공")
    print(f"계좌번호: {auth.account_no}")
    print("-"*60)

    # 1. 계좌 잔액 조회
    print("\n📊 [계좌 잔액]")
    balance = api.get_balance()

    if balance:
        cash = balance.get('주문가능현금', 0)
        total_eval = balance.get('총평가금액', 0)
        total_buy = balance.get('총매입금액', 0)
        total_profit = balance.get('평가손익', 0)

        print(f"   주문가능현금: {cash:,}원")
        print(f"   총평가금액: {total_eval:,}원")
        print(f"   총매입금액: {total_buy:,}원")
        print(f"   평가손익: {total_profit:+,}원")

        if total_buy > 0:
            profit_rate = (total_profit / total_buy) * 100
            print(f"   수익률: {profit_rate:+.2f}%")
    else:
        print("   ❌ 잔액 조회 실패")

    print("-"*60)

    # 2. 보유 종목 조회
    print("\n📈 [보유 종목]")
    stocks = api.get_stock_balance()

    if stocks and len(stocks) > 0:
        total_stock_value = 0
        total_stock_profit = 0

        for i, stock in enumerate(stocks, 1):
            code = stock.get("종목코드")
            name = stock.get("종목명")
            quantity = stock.get("보유수량", 0)
            avg_price = stock.get("매입단가", 0)
            current_price = stock.get("현재가", 0)
            eval_amount = stock.get("평가금액", 0)
            profit = stock.get("평가손익", 0)
            profit_rate = stock.get("수익률", 0)

            if quantity > 0:  # 실제 보유 종목만 표시
                print(f"\n   [{i}] {name}({code})")
                print(f"       보유수량: {quantity:,}주")
                print(f"       매입단가: {avg_price:,}원")
                print(f"       현재가: {current_price:,}원")
                print(f"       평가금액: {eval_amount:,}원")
                print(f"       평가손익: {profit:+,}원 ({profit_rate:+.2f}%)")

                total_stock_value += eval_amount
                total_stock_profit += profit

        if total_stock_value > 0:
            print("\n   " + "="*50)
            print(f"   종목 합계: {total_stock_value:,}원")
            print(f"   총 손익: {total_stock_profit:+,}원")
    else:
        print("   보유 종목 없음")

    print("-"*60)

    # 3. 주문 내역 조회 (당일)
    print("\n📝 [당일 주문 내역]")
    orders = api.get_orders()

    if orders and len(orders) > 0:
        buy_count = 0
        sell_count = 0

        for order in orders:
            order_type = order.get("매매구분")
            stock_name = order.get("종목명")
            quantity = order.get("주문수량", 0)
            price = order.get("주문단가", 0)
            status = order.get("주문상태")

            if order_type == "매수":
                buy_count += 1
            else:
                sell_count += 1

            print(f"   • {order_type} {stock_name}: {quantity}주 @ {price:,}원 ({status})")

        print(f"\n   총 매수: {buy_count}건, 매도: {sell_count}건")
    else:
        print("   당일 주문 내역 없음")

    print("\n" + "="*60)

    # 4. 계좌 요약
    if balance:
        print("\n💼 [계좌 요약]")
        total = cash + total_stock_value if 'total_stock_value' in locals() else cash

        print(f"   💵 현금: {cash:,}원")
        if 'total_stock_value' in locals() and total_stock_value > 0:
            print(f"   📊 주식: {total_stock_value:,}원")
        print(f"   💰 총액: {total:,}원")

        # 투자 비율
        if total > 0:
            cash_ratio = (cash / total) * 100
            stock_ratio = 100 - cash_ratio
            print(f"\n   현금 비율: {cash_ratio:.1f}%")
            print(f"   주식 비율: {stock_ratio:.1f}%")

    print("\n" + "="*60)
    print("✅ 계좌 조회 완료!")
    print("="*60)


if __name__ == "__main__":
    main()