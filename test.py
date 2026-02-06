"""
ChulAutoStock 테스트 스크립트
모의투자/실전투자 테스트용
삼성전자 1주 매수 → 매도 테스트
"""

import time
import os
from datetime import datetime
from dotenv import load_dotenv

# 모듈 임포트
from kis_auth import KISAuth
from kis_api import KISApi

# .env 로드
load_dotenv()


def main():
    """테스트 메인 함수"""
    print("="*60)
    print("ChulAutoStock 매매 테스트")
    print("="*60)

    # 1. 모드 확인 및 API 초기화
    env_mode = os.getenv("IS_REAL_TRADING", "false").lower()
    is_real = env_mode == "true"

    mode_name = "🔴 실전투자" if is_real else "🟢 모의투자"
    print(f"\n{mode_name} 모드로 테스트합니다.")

    # API 인증
    print("\n📡 API 연결 중...")
    auth = KISAuth(is_real=is_real)
    api = KISApi(auth)

    if not auth.access_token:
        print("❌ API 인증 실패!")
        return

    print(f"✅ API 연결 성공")
    print(f"   서버: {auth.base_url}")
    print(f"   계좌: {auth.account_no}")

    # 2. 잔액 조회
    print("\n💰 계좌 잔액 조회...")
    balance = api.get_balance()

    if balance:
        print(f"   주문가능현금: {balance.get('주문가능현금', 0):,}원")
        print(f"   총평가금액: {balance.get('총평가금액', 0):,}원")

        available_cash = balance.get('주문가능현금', 0)
        if available_cash < 100000:
            print("⚠️ 주문 가능 현금이 10만원 미만입니다.")
            if is_real:
                print("실전투자 모드에서는 충분한 자금이 필요합니다.")
                return
    else:
        print("❌ 잔고 조회 실패")
        return

    print("\n⏳ 1초 대기...")
    time.sleep(1)

    # 3. 삼성전자 현재가 조회
    stock_code = "005930"  # 삼성전자
    print(f"\n📊 삼성전자({stock_code}) 현재가 조회...")

    price_info = api.get_current_price(stock_code)
    if not price_info:
        print("❌ 현재가 조회 실패")
        return

    current_price = price_info.get("현재가", 0)
    print(f"   현재가: {current_price:,}원")
    print(f"   등락률: {price_info.get('등락률', 0):+.2f}%")

    if current_price <= 0:
        print("❌ 유효하지 않은 가격")
        return

    # 4. 매수 주문 (1주)
    buy_quantity = 1
    print(f"\n🛒 매수 주문 실행")
    print(f"   종목: 삼성전자")
    print(f"   수량: {buy_quantity}주")
    print(f"   예상금액: {current_price * buy_quantity:,}원")

    # 실전투자일 경우 최종 확인
    if is_real:
        print("\n⚠️ 실전투자 모드입니다! 실제 매수가 진행됩니다.")
        confirm = input("계속하시겠습니까? (yes/no): ")
        if confirm.lower() != "yes":
            print("테스트 중단")
            return

    # 매수 실행
    buy_result = api.buy_stock(stock_code, buy_quantity, order_type="01")  # 시장가

    if not buy_result:
        print("❌ 매수 주문 실패")
        return

    print(f"✅ 매수 주문 접수: {buy_result.get('주문번호')}")
    buy_time = datetime.now()

    # 5. 체결 대기 (최대 30초)
    print("\n⏳ 매수 체결 대기 중...")

    for i in range(30):
        time.sleep(1)

        # 보유 종목 확인
        stocks = api.get_stock_balance()
        if stocks:
            for stock in stocks:
                if stock.get("종목코드") == stock_code and stock.get("보유수량", 0) > 0:
                    print(f"✅ 매수 체결 완료!")
                    print(f"   보유수량: {stock.get('보유수량')}주")
                    print(f"   매입단가: {stock.get('매입단가'):,.0f}원")
                    buy_price = stock.get('매입단가', current_price)
                    break
            else:
                if i % 5 == 0:
                    print(f"   {i}초 대기 중...")
                continue
            break
    else:
        print("⚠️ 30초 내 체결되지 않았습니다.")
        buy_price = current_price

    # 6. 5초 대기
    print("\n⏳ 5초 후 매도 예정...")
    for i in range(5, 0, -1):
        print(f"   {i}초...")
        time.sleep(1)

    # 7. 매도 주문
    print(f"\n📤 매도 주문 실행")
    print(f"   종목: 삼성전자")
    print(f"   수량: {buy_quantity}주")

    # 현재가 다시 조회
    price_info = api.get_current_price(stock_code)
    if price_info:
        sell_price = price_info.get("현재가", 0)
        print(f"   현재가: {sell_price:,}원")
    else:
        sell_price = current_price

    # 매도 실행
    sell_result = api.sell_stock(stock_code, buy_quantity, order_type="01")  # 시장가

    if not sell_result:
        print("❌ 매도 주문 실패")
        return

    print(f"✅ 매도 주문 접수: {sell_result.get('주문번호')}")
    sell_time = datetime.now()

    # 8. 매도 체결 대기
    print("\n⏳ 매도 체결 대기 중...")

    for i in range(30):
        time.sleep(1)

        # 보유 종목 확인
        stocks = api.get_stock_balance()
        is_sold = True

        if stocks:
            for stock in stocks:
                if stock.get("종목코드") == stock_code and stock.get("보유수량", 0) > 0:
                    is_sold = False
                    break

        if is_sold:
            print(f"✅ 매도 체결 완료!")
            break

        if i % 5 == 0:
            print(f"   {i}초 대기 중...")
    else:
        print("⚠️ 30초 내 체결되지 않았습니다.")

    # 9. 수익률 계산 및 출력
    print("\n" + "="*60)
    print("📊 거래 결과")
    print("="*60)

    # 실제 체결 내역 조회
    orders = api.get_orders()
    if orders:
        for order in orders:
            if order.get("종목코드") == stock_code:
                print(f"   {order.get('매매구분')}: {order.get('체결수량')}주 @ {order.get('체결단가'):,.0f}원")

    # 예상 수익률 계산
    profit = (sell_price - buy_price) * buy_quantity
    profit_rate = ((sell_price - buy_price) / buy_price) * 100 if buy_price > 0 else 0

    print(f"\n💰 수익 분석")
    print(f"   매수가: {buy_price:,.0f}원")
    print(f"   매도가: {sell_price:,.0f}원")
    print(f"   손익: {profit:+,.0f}원")
    print(f"   수익률: {profit_rate:+.2f}%")

    # 소요 시간
    total_time = (sell_time - buy_time).seconds
    print(f"   소요시간: {total_time}초")

    # 최종 잔고
    print(f"\n💼 최종 잔고")
    balance = api.get_balance()
    if balance:
        print(f"   주문가능현금: {balance.get('주문가능현금', 0):,}원")
        print(f"   총평가금액: {balance.get('총평가금액', 0):,}원")

    print("\n" + "="*60)
    print("✅ 테스트 완료!")
    print("="*60)


if __name__ == "__main__":
    # 장 운영 시간 체크 (옵션)
    now = datetime.now()
    hour = now.hour
    weekday = now.weekday()

    # 주말 체크
    if weekday >= 5:  # 토요일(5), 일요일(6)
        print("⚠️ 주말에는 거래가 불가능합니다.")
        print("모의투자는 가능하지만 체결되지 않을 수 있습니다.")
        confirm = input("계속하시겠습니까? (yes/no): ")
        if confirm.lower() != "yes":
            exit()

    # 장시간 체크 (09:00 ~ 15:30)
    if not (9 <= hour < 16):
        print("⚠️ 정규 장시간(09:00~15:30)이 아닙니다.")
        print("시장가 주문이 체결되지 않을 수 있습니다.")
        confirm = input("계속하시겠습니까? (yes/no): ")
        if confirm.lower() != "yes":
            exit()

    # 메인 실행
    main()