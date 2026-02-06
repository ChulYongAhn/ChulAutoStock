"""
매수 테스트 스크립트
KT 1주 매수만 실행
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
    """매수 테스트 메인"""
    print("="*60)
    print("📈 매수 테스트 - KT 1주")
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
    slack_message(f"📈 매수 테스트 시작 - {mode_name}")

    # 1. 매수 전 잔액 조회
    print("\n💰 [매수 전 상태]")
    balance_before = api.get_balance()

    if not balance_before:
        print("❌ 잔고 조회 실패")
        return

    cash_before = balance_before.get('주문가능현금', 0)
    total_before = balance_before.get('총평가금액', 0)

    print(f"   주문가능현금: {cash_before:,}원")
    print(f"   총평가금액: {total_before:,}원")

    # 자금 체크
    if cash_before < 100000:
        print("\n⚠️ 주문 가능 현금이 10만원 미만입니다.")
        if is_real:
            return

    # 2. KT 현재가 조회
    print("\n📊 [종목 정보]")
    stock_code = "030200"
    stock_name = "KT"

    price_info = api.get_current_price(stock_code)
    if not price_info:
        print("❌ 현재가 조회 실패")
        return

    current_price = price_info.get("현재가", 0)
    change_rate = price_info.get("등락률", 0)
    volume = price_info.get("거래량", 0)

    print(f"   종목: {stock_name}({stock_code})")
    print(f"   현재가: {current_price:,}원")
    print(f"   등락률: {change_rate:+.2f}%")
    print(f"   거래량: {volume:,}주")

    if current_price <= 0:
        print("❌ 유효하지 않은 가격")
        return

    # 3. 매수 계산
    buy_quantity = 1
    buy_amount = current_price * buy_quantity
    expected_balance = cash_before - buy_amount

    print("\n🛒 [매수 주문 정보]")
    print(f"   매수 수량: {buy_quantity}주")
    print(f"   매수 가격: {current_price:,}원")
    print(f"   필요 금액: {buy_amount:,}원")
    print(f"   예상 잔액: {expected_balance:,}원")

    # 잔액 부족 체크
    if buy_amount > cash_before:
        print("\n❌ 잔액 부족으로 매수 불가")
        print(f"   부족 금액: {(buy_amount - cash_before):,}원")
        return

    # 실전 경고만 표시
    if is_real:
        print("\n⚠️ 실전투자 모드 - 실제 매수가 진행됩니다!")

    # 4. 매수 실행
    print("\n📤 [매수 주문 실행]")
    print(f"   시간: {datetime.now().strftime('%H:%M:%S')}")

    result = api.buy_stock(stock_code, buy_quantity, order_type="01")  # 시장가

    if not result:
        print("❌ 매수 주문 실패")
        return

    order_no = result.get('주문번호')
    print(f"   ✅ 주문 접수 완료")
    print(f"   주문번호: {order_no}")

    # Slack 거래 알림
    slack_trade(
        action="매수",
        stock_code=stock_code,
        stock_name=stock_name,
        quantity=buy_quantity,
        price=current_price,
        amount=buy_amount,
        is_real=is_real
    )

    # 5. 체결 확인 (간단히 대기)
    import time
    print("\n⏳ 체결 대기 중...")
    time.sleep(3)

    # 6. 매수 후 잔액 조회
    print("\n💰 [매수 후 상태]")
    balance_after = api.get_balance()

    if balance_after:
        cash_after = balance_after.get('주문가능현금', 0)
        total_after = balance_after.get('총평가금액', 0)

        print(f"   주문가능현금: {cash_after:,}원")
        print(f"   총평가금액: {total_after:,}원")
        print(f"   현금 변동: {(cash_after - cash_before):,}원")

    # 7. 보유 종목 확인
    print("\n📋 [보유 종목 확인]")
    stocks = api.get_stock_balance()

    if stocks:
        for stock in stocks:
            if stock.get("종목코드") == stock_code:
                print(f"   ✅ {stock.get('종목명')}: {stock.get('보유수량')}주")
                print(f"   매입단가: {stock.get('매입단가'):,.0f}원")
                print(f"   현재가치: {stock.get('평가금액'):,}원")
                break
        else:
            print("   ⏳ 아직 체결 처리 중...")
    else:
        print("   보유 종목 없음")

    # 8. 요약
    print("\n" + "="*60)
    print("📊 [매수 테스트 요약]")
    print("="*60)
    print(f"종목: {stock_name}")
    print(f"수량: {buy_quantity}주 × {current_price:,}원")
    print(f"투자금액: {buy_amount:,}원")
    print(f"남은현금: {cash_after:,}원" if balance_after else f"예상잔액: {expected_balance:,}원")
    print(f"상태: ✅ 매수 주문 완료")
    print("="*60)

    # 9. 전체 로그 Slack 전송
    log_data = {
        'stock_code': stock_code,
        'stock_name': stock_name,
        'cash_before': cash_before,
        'total_before': total_before,
        'current_price': current_price,
        'change_rate': change_rate,
        'volume': volume,
        'quantity': buy_quantity,
        'amount': buy_amount,
        'expected_balance': expected_balance,
        'order_no': order_no,
        'cash_after': cash_after if balance_after else 0,
        'cash_change': (cash_after - cash_before) if balance_after else 0
    }
    slack.send_buy_test_log(log_data, is_real)


if __name__ == "__main__":
    main()