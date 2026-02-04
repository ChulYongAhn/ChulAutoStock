"""
ChulAutoStock - 자동 주식 트레이딩 프로젝트
한국투자증권 API 사용
"""

import os
from dotenv import load_dotenv
from pykrx import stock

# .env 파일 로드
load_dotenv()


class KISConfig:
    """한국투자증권 API 설정"""

    APP_KEY = os.getenv("KIS_APP_KEY")
    APP_SECRET = os.getenv("KIS_APP_SECRET")
    ACCOUNT_NO = os.getenv("KIS_ACCOUNT_NO")

    # API URL (실전/모의)
    BASE_URL = "https://openapi.koreainvestment.com:9443"  # 실전
    # BASE_URL = "https://openapivts.koreainvestment.com:29443"  # 모의투자

    @classmethod
    def validate(cls):
        """설정값 검증"""
        missing = []
        # 주의: 여기 값을 직접 수정하지 마세요! .env 파일에 입력하세요!
        if not cls.APP_KEY or cls.APP_KEY == "DEFAULT_NOT_SET":
            missing.append("KIS_APP_KEY")
        if not cls.APP_SECRET or cls.APP_SECRET == "DEFAULT_NOT_SET":
            missing.append("KIS_APP_SECRET")
        if not cls.ACCOUNT_NO or cls.ACCOUNT_NO == "00000000-00":
            missing.append("KIS_ACCOUNT_NO")

        if missing:
            print(f"[경고] .env 파일에서 다음 값을 설정하세요: {', '.join(missing)}")
            return False
        return True


def get_stock_price(ticker, start_date, end_date):
    """주식 가격 데이터 가져오기"""
    df = stock.get_market_ohlcv(start_date, end_date, ticker)
    return df


def main():
    """메인 함수"""
    print("=" * 50)
    print("ChulAutoStock 시작")
    print("=" * 50)

    # 한투 API 설정 확인
    if KISConfig.validate():
        print("[OK] 한국투자증권 API 설정 완료")
    print()

    # 예시: 삼성전자(005930) 최근 주가 조회
    ticker = "005930"  # 삼성전자
    df = get_stock_price(ticker, "20250101", "20250131")

    print(f"삼성전자 주가 데이터:")
    print(df)


if __name__ == "__main__":
    main()
