"""
한국투자증권 API 인증 모듈
토큰 발급 및 관리
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class KISAuth:
    """한국투자증권 API 인증 클래스"""

    def __init__(self, is_real: bool = True):
        """
        초기화
        Args:
            is_real: True=실전, False=모의투자
        """
        self.is_real = is_real
        self.app_key = os.getenv("KIS_APP_KEY")
        self.app_secret = os.getenv("KIS_APP_SECRET")
        self.account_no = os.getenv("KIS_ACCOUNT_NO")

        # API URL 설정
        if is_real:
            self.base_url = "https://openapi.koreainvestment.com:9443"
        else:
            self.base_url = "https://openapivts.koreainvestment.com:29443"

        # 토큰 정보
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.token_type: str = "Bearer"

        # 토큰 파일 경로 (캐싱용)
        self.token_file = "kis_token.json"

    def validate_config(self) -> bool:
        """설정값 검증"""
        missing = []

        if not self.app_key or self.app_key == "DEFAULT_NOT_SET":
            missing.append("KIS_APP_KEY")
        if not self.app_secret or self.app_secret == "DEFAULT_NOT_SET":
            missing.append("KIS_APP_SECRET")
        if not self.account_no or self.account_no == "00000000-00":
            missing.append("KIS_ACCOUNT_NO")

        if missing:
            print(f"❌ 오류: .env 파일에서 다음 값을 설정하세요: {', '.join(missing)}")
            print("  한국투자증권 오픈API에서 발급받은 값을 입력해주세요.")
            print("  https://apiportal.koreainvestment.com")
            return False

        return True

    def get_token(self) -> Optional[str]:
        """
        액세스 토큰 반환 (필요시 자동 발급/갱신)
        """
        # 설정 검증
        if not self.validate_config():
            return None

        # 기존 토큰 확인
        if self._is_token_valid():
            return self.access_token

        # 캐시된 토큰 로드 시도
        if self._load_cached_token():
            if self._is_token_valid():
                print("✅ 캐시된 토큰 사용")
                return self.access_token

        # 새 토큰 발급
        print("🔄 새 액세스 토큰 발급 중...")
        if self._issue_token():
            print("✅ 토큰 발급 성공!")
            self._save_cached_token()
            return self.access_token

        return None

    def _issue_token(self) -> bool:
        """API로 토큰 발급"""
        url = f"{self.base_url}/oauth2/tokenP"

        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()

            # 토큰 정보 저장
            self.access_token = result.get("access_token")
            self.token_type = result.get("token_type", "Bearer")

            # 만료 시간 계산 (24시간에서 1시간 여유)
            expires_in = result.get("expires_in", 86400)  # 기본 24시간
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 3600)

            return True

        except requests.exceptions.RequestException as e:
            print(f"❌ 토큰 발급 실패: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   응답 내용: {e.response.text}")
            return False

    def _is_token_valid(self) -> bool:
        """토큰 유효성 확인"""
        if not self.access_token or not self.token_expires_at:
            return False

        # 만료 10분 전에 갱신
        buffer_time = timedelta(minutes=10)
        return datetime.now() < (self.token_expires_at - buffer_time)

    def _save_cached_token(self):
        """토큰 정보를 파일에 저장 (캐싱)"""
        if not self.access_token:
            return

        token_data = {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "token_expires_at": self.token_expires_at.isoformat() if self.token_expires_at else None,
            "is_real": self.is_real,
            "saved_at": datetime.now().isoformat()
        }

        try:
            with open(self.token_file, 'w', encoding='utf-8') as f:
                json.dump(token_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  토큰 캐시 저장 실패: {e}")

    def _load_cached_token(self) -> bool:
        """캐시된 토큰 로드"""
        if not os.path.exists(self.token_file):
            return False

        try:
            with open(self.token_file, 'r', encoding='utf-8') as f:
                token_data = json.load(f)

            # 실전/모의 모드 확인
            if token_data.get("is_real") != self.is_real:
                return False

            self.access_token = token_data.get("access_token")
            self.token_type = token_data.get("token_type", "Bearer")

            if token_data.get("token_expires_at"):
                self.token_expires_at = datetime.fromisoformat(token_data["token_expires_at"])

            return True

        except Exception as e:
            print(f"⚠️  토큰 캐시 로드 실패: {e}")
            return False

    def get_headers(self) -> Dict[str, str]:
        """API 요청용 헤더 반환"""
        token = self.get_token()
        if not token:
            return {}

        return {
            "authorization": f"{self.token_type} {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "content-type": "application/json"
        }


# 테스트 코드
if __name__ == "__main__":
    print("=" * 50)
    print("한국투자증권 API 인증 테스트")
    print("=" * 50)

    # 실전 모드로 인증
    auth = KISAuth(is_real=True)

    # 토큰 발급
    token = auth.get_token()

    if token:
        print(f"\n✅ 토큰 발급 성공!")
        print(f"   토큰: {token[:20]}...")
        print(f"   만료: {auth.token_expires_at}")
    else:
        print("\n❌ 토큰 발급 실패")
        print("   .env 파일의 API 키를 확인해주세요")