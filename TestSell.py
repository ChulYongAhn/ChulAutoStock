"""
매도 테스트 스크립트
KT 1주 매도만 실행
"""

import os
from datetime import datetime
from dotenv import load_dotenv

# 모듈 임포트
from kis_auth import KISAuth
from kis_api import KISApi
from slack_service import get_slack, slack_message, slack_trade

# .env 로드
load_dotenv()


def main():
    """매도 테스트 메인"""
    print("="*60)
    print("📉 매도 테스트 - KT 1주")
    print("="*60)

    # 모드 확인
    env_mode = os.getenv("IS_REAL_TRADING", "false").lower()
    is_real = env_mode == "true"
    mode_name = "🔴 실전투자" if is_real else "🟢 모의투자"

    print(f"\n모드: {mode_name}")
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # API 초기화
    auth = KISAuth(is_real=is_real)
    api = KISApi(auth)

    # 토큰 획득 시도
    token = auth.get_token()
    if not token:
        print("❌ API 인증 실패!")
        return

    print(f"계좌: {auth.account_no}")
    print("-"*60)

    # Slack 알림 초기화
    slack = get_slack()
    slack_message(f"📉 매도 테스트 시작 - {mode_name}")

    # 1. 보유 종목 확인
    print("\n📋 [보유 종목 확인]")
    stocks = api.get_stock_balance()

    stock_code = "030200"
    stock_name = "KT"
    holding_quantity = 0
    avg_price = 0

    if stocks:
        for stock in stocks:
            if stock.get("종목코드") == stock_code:
                holding_quantity = stock.get("보유수량", 0)
                avg_price = stock.get("매입단가", 0)
                print(f"   종목: {stock.get('종목명')}({stock_code})")
                print(f"   보유수량: {holding_quantity}주")
                print(f"   매입단가: {avg_price:,.0f}원")
                print(f"   평가금액: {stock.get('평가금액'):,}원")
                print(f"   평가손익: {stock.get('평가손익'):+,}원")
                print(f"   수익률: {stock.get('수익률'):+.2f}%")
                break
        else:
            print(f"   ⚠️ {stock_name} 보유하지 않음")
            print("\n매도할 주식이 없습니다.")
            print("먼저 BuyTest.py를 실행하여 주식을 매수하세요.")
            return
    else:
        print("   보유 종목 없음")
        return

    if holding_quantity <= 0:
        print("\n⚠️ 매도 가능한 수량이 없습니다.")
        return

    # 2. 매도 전 잔액 조회
    print("\n💰 [매도 전 상태]")
    balance_before = api.get_balance()

    if not balance_before:
        print("❌ 잔고 조회 실패")
        return

    cash_before = balance_before.get('주문가능현금', 0)
    total_before = balance_before.get('총평가금액', 0)
    profit_before = balance_before.get('평가손익', 0)

    print(f"   주문가능현금: {cash_before:,}원")
    print(f"   총평가금액: {total_before:,}원")
    print(f"   평가손익: {profit_before:+,}원")

    # 3. 현재가 조회
    print("\n📊 [현재 시세]")
    price_info = api.get_current_price(stock_code)

    if not price_info:
        print("❌ 현재가 조회 실패")
        return

    current_price = price_info.get("현재가", 0)
    change_rate = price_info.get("등락률", 0)
    volume = price_info.get("거래량", 0)

    print(f"   현재가: {current_price:,}원")
    print(f"   등락률: {change_rate:+.2f}%")
    print(f"   거래량: {volume:,}주")

    # 4. 매도 계산
    sell_quantity = min(1, holding_quantity)  # 1주 또는 보유 수량 중 작은 값
    sell_amount = current_price * sell_quantity
    expected_cash = cash_before + sell_amount
    profit = (current_price - avg_price) * sell_quantity
    profit_rate = ((current_price - avg_price) / avg_price * 100) if avg_price > 0 else 0

    print("\n📤 [매도 주문 정보]")
    print(f"   매도 수량: {sell_quantity}주 (보유: {holding_quantity}주)")
    print(f"   매도 가격: {current_price:,}원")
    print(f"   예상 수익: {profit:+,}원 ({profit_rate:+.2f}%)")
    print(f"   예상 입금: {sell_amount:,}원")
    print(f"   예상 현금: {expected_cash:,}원")

    # 실전 경고만 표시
    if is_real:
        print("\n⚠️ 실전투자 모드 - 실제 매도가 진행됩니다!")

    # 5. 매도 실행
    print("\n📉 [매도 주문 실행]")
    print(f"   시간: {datetime.now().strftime('%H:%M:%S')}")

    result = api.sell_stock(stock_code, sell_quantity, order_type="01")  # 시장가

    if not result:
        print("❌ 매도 주문 실패")
        return

    order_no = result.get('주문번호')
    print(f"   ✅ 주문 접수 완료")
    print(f"   주문번호: {order_no}")

    # Slack 거래 알림 (수익률 포함)
    slack_trade(
        action="매도",
        stock_code=stock_code,
        stock_name=stock_name,
        quantity=sell_quantity,
        price=current_price,
        amount=sell_amount,
        profit=profit_rate,
        is_real=is_real
    )

    # 6. 체결 확인 (간단히 대기)
    import time
    print("\n⏳ 체결 대기 중...")
    time.sleep(3)

    # 7. 매도 후 잔액 조회
    print("\n💰 [매도 후 상태]")
    balance_after = api.get_balance()

    if balance_after:
        cash_after = balance_after.get('주문가능현금', 0)
        total_after = balance_after.get('총평가금액', 0)
        profit_after = balance_after.get('평가손익', 0)

        print(f"   주문가능현금: {cash_after:,}원")
        print(f"   총평가금액: {total_after:,}원")
        print(f"   현금 증가: +{(cash_after - cash_before):,}원")

    # 8. 남은 보유 종목 확인
    print("\n📋 [남은 보유 종목]")
    stocks_after = api.get_stock_balance()

    remaining = 0
    if stocks_after:
        for stock in stocks_after:
            if stock.get("종목코드") == stock_code:
                remaining = stock.get("보유수량", 0)
                if remaining > 0:
                    print(f"   {stock.get('종목명')}: {remaining}주 남음")
                break
        else:
            print(f"   ✅ {stock_name} 전량 매도 완료")
    else:
        print("   보유 종목 없음")

    # 9. 실현 손익 계산
    print("\n💵 [실현 손익]")
    print(f"   매입단가: {avg_price:,.0f}원")
    print(f"   매도단가: {current_price:,}원")
    print(f"   손익단가: {(current_price - avg_price):+,}원")
    print(f"   실현손익: {profit:+,}원")
    print(f"   수익률: {profit_rate:+.2f}%")

    # 10. 요약
    print("\n" + "="*60)
    print("📊 [매도 테스트 요약]")
    print("="*60)
    print(f"종목: {stock_name}")
    print(f"매도: {sell_quantity}주 × {current_price:,}원 = {sell_amount:,}원")
    print(f"손익: {profit:+,}원 ({profit_rate:+.2f}%)")
    print(f"남은주식: {remaining}주")
    print(f"현금잔액: {cash_after:,}원" if balance_after else f"예상현금: {expected_cash:,}원")
    print(f"상태: ✅ 매도 주문 완료")
    print("="*60)

    # 11. 전체 로그 Slack 전송
    log_data = {
        'stock_code': stock_code,
        'stock_name': stock_name,
        'holding_quantity': holding_quantity,
        'avg_price': avg_price,
        'holding_profit': profit_before if balance_before else 0,
        'cash_before': cash_before,
        'total_before': total_before,
        'current_price': current_price,
        'quantity': sell_quantity,
        'profit': profit,
        'profit_rate': profit_rate,
        'order_no': order_no,
        'cash_after': cash_after if balance_after else 0,
        'cash_increase': (cash_after - cash_before) if balance_after else sell_amount,
        'remaining': remaining
    }
    slack.send_sell_test_log(log_data, is_real)


if __name__ == "__main__":
    main()