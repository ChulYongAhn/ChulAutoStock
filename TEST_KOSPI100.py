"""
KOSPI 100 전체 종목 등락률 분석
"""

from datetime import datetime, timedelta
from kis_auth import KISAuth
from kis_api import KISApi
from pykrx import stock
from AutoStockSetting import KOSPI_100

def check_kospi100_prices():
    """KOSPI 100 종목 가격 조회 및 등락률 계산"""

    # API 인증
    print("API 인증 중...")
    auth = KISAuth(is_real=True)  # 실전 모드
    api = KISApi(auth)

    # 어제 날짜 계산 (주말 고려)
    yesterday = datetime.now() - timedelta(days=1)
    while yesterday.weekday() >= 5:  # 5=토요일, 6=일요일
        yesterday -= timedelta(days=1)

    today = datetime.now()
    yesterday_str = yesterday.strftime("%Y%m%d")

    print("\n" + "="*100)
    print(f"KOSPI 100 종목 등락률 분석 | {yesterday.strftime('%m월%d일')} → {today.strftime('%m월%d일 %H:%M')}")
    print("="*100)
    print()

    # 결과 저장 리스트
    results = []
    success_count = 0
    fail_count = 0

    for idx, (code, name) in enumerate(KOSPI_100.items(), 1):
        try:
            # 1. 어제 종가 조회 (pykrx)
            df = stock.get_market_ohlcv(yesterday_str, yesterday_str, code)

            if df.empty:
                fail_count += 1
                continue

            yesterday_close = int(df.iloc[0]['종가'])

            # 2. 현재가 조회 (KIS API)
            current_data = api.get_current_price(code)

            if not current_data:
                fail_count += 1
                continue

            current_price = current_data['현재가']

            # 3. 등락률 계산
            change_rate = ((current_price - yesterday_close) / yesterday_close) * 100

            # 결과 저장
            results.append({
                'name': name,
                'code': code,
                'yesterday_close': yesterday_close,
                'current_price': current_price,
                'change_rate': change_rate
            })

            success_count += 1

            # 한 줄로 출력
            sign = "+" if change_rate >= 0 else ""
            print(f"[{name:10s}] 어제 | {yesterday.strftime('%m월%d일')} | {yesterday_close:>7,}원 → "
                  f"오늘 | {today.strftime('%m월%d일 %H:%M')} | {current_price:>7,}원 → "
                  f"등락 {sign}{change_rate:.1f}%")

        except Exception as e:
            fail_count += 1
            print(f"[{name:10s}] 조회 실패: {str(e)[:30]}")
            continue

    # 통계 출력
    print("\n" + "="*100)
    print(f"조회 완료: 성공 {success_count}개 / 실패 {fail_count}개")
    print("="*100)

    # Phase 2 조건(+2% ~ +4%) 충족 종목 필터링
    filtered = [r for r in results if 2.0 <= r['change_rate'] <= 4.0]

    print(f"\n📊 Phase 2 조건(+2% ~ +4%) 충족 종목: {len(filtered)}개")
    if filtered:
        for r in filtered:
            print(f"   • {r['name']}: +{r['change_rate']:.2f}%")
    else:
        print("   ⚠️ 조건을 만족하는 종목이 없습니다")

    # 상위 상승률 TOP 10
    results.sort(key=lambda x: x['change_rate'], reverse=True)
    print(f"\n📈 상승률 TOP 10:")
    for i, r in enumerate(results[:10], 1):
        sign = "+" if r['change_rate'] >= 0 else ""
        print(f"   {i:2d}. {r['name']:10s}: {sign}{r['change_rate']:.2f}%")

    # 하위 하락률 TOP 10
    print(f"\n📉 하락률 TOP 10:")
    for i, r in enumerate(results[-10:], 1):
        sign = "+" if r['change_rate'] >= 0 else ""
        print(f"   {i:2d}. {r['name']:10s}: {sign}{r['change_rate']:.2f}%")

    return results


if __name__ == "__main__":
    check_kospi100_prices()