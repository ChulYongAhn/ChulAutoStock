"""
Phase 0: API 인증
프로그램 시작 시 한 번만 실행
토큰 발급 및 API 클라이언트 초기화
"""

from datetime import datetime
from typing import Optional, Tuple
from kis_auth import KISAuth
from kis_api import KISApi
from slack_service import slack_message, slack_error


class Phase0Auth:
    """Phase 0: API 인증 및 초기화"""

    def __init__(self, is_real: bool = True):
        """
        초기화

        Args:
            is_real: True=실전, False=모의투자
        """
        self.is_real = is_real
        self.auth = None
        self.api = None

    def run(self) -> Tuple[Optional[KISAuth], Optional[KISApi]]:
        """
        Phase 0 실행

        Returns:
            (KISAuth 인스턴스, KISApi 인스턴스) 튜플
            실패 시 (None, None) 반환
        """
        print("\n" + "="*50)
        print("[ Phase 0: API 인증 ]")
        print("="*50)

        # Slack 알림: Phase 0 시작
        mode_text = "🔴 실전" if self.is_real else "🟢 모의"
        slack_message(f"🔐 Phase 0 시작 - API 인증 ({mode_text})")

        # KISAuth 인스턴스 생성
        self.auth = KISAuth(is_real=self.is_real)

        # 토큰 발급
        token = self.auth.get_token()

        if not token:
            error_msg = "API 인증 실패! .env 설정 확인 필요"
            print(f"❌ {error_msg}")
            print("   .env 파일의 설정을 확인해주세요:")
            print("   - KIS_APP_KEY: 한국투자증권에서 발급받은 APP KEY")
            print("   - KIS_APP_SECRET: 한국투자증권에서 발급받은 APP SECRET")
            print("   - KIS_ACCOUNT_NO: 계좌번호 (10자리 또는 8자리-2자리)")
            print("\n   한국투자증권 오픈API:")
            print("   https://apiportal.koreainvestment.com")

            # Slack 에러 알림
            slack_error("Phase 0 실패", error_msg)
            return None, None

        print("✅ API 인증 성공!")
        print(f"   모드: {'실전' if self.is_real else '모의투자'}")
        print(f"   계좌: {self.auth.account_no}")
        print(f"   토큰 만료: {self.auth.token_expires_at}")

        # API 클라이언트 생성
        self.api = KISApi(self.auth)

        # 계좌 확인 (선택적)
        balance_info = self._verify_account()

        # Slack 알림: Phase 0 완료
        success_msg = f"✅ Phase 0 완료\n"
        success_msg += f"• 계좌: {self.auth.account_no}\n"
        if balance_info:
            success_msg += f"• 잔액: {balance_info:,}원"
        else:
            success_msg += f"• API 연결 성공"
        slack_message(success_msg)

        return self.auth, self.api

    def _verify_account(self):
        """계좌 연결 확인 (선택적)"""
        try:
            balance = self.api.get_balance()
            if balance:
                available_cash = balance.get('주문가능현금', 0)
                print(f"   계좌 연결: ✅ (잔액: {available_cash:,}원)")
                return available_cash
            else:
                print("   계좌 연결: ⚠️  (잔고 조회 실패, API는 정상)")
                return None
        except:
            # 계좌 확인 실패는 무시 (API 인증은 성공)
            return None

    def get_auth(self) -> Optional[KISAuth]:
        """
        인증 객체 반환

        Returns:
            KISAuth 인스턴스
        """
        return self.auth

    def get_api(self) -> Optional[KISApi]:
        """
        API 클라이언트 반환

        Returns:
            KISApi 인스턴스
        """
        return self.api


# 테스트 코드
if __name__ == "__main__":
    print("Phase 0 테스트")
    print("="*50)

    # Phase 0 실행
    phase0 = Phase0Auth(is_real=True)
    auth, api = phase0.run()

    if auth and api:
        print("\n✅ Phase 0 성공!")

        # API 사용량 확인
        usage = api.get_api_usage()
        if usage:
            print(f"\n📊 API 사용량:")
            print(f"   일일: {usage.get('일일_사용', 'N/A')}/{usage.get('일일_한도', 'N/A')}")
            print(f"   사용률: {usage.get('사용률', 'N/A')}")
    else:
        print("\n❌ Phase 0 실패!")