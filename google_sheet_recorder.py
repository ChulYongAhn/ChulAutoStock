"""
구글 시트 거래 기록 모듈
실시간으로 매매 내역을 구글 시트에 기록하여 모바일에서 확인 가능
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class GoogleSheetRecorder:
    """구글 시트 거래 기록 클래스"""

    def __init__(self, credentials_file: str = None, sheet_id: str = None):
        """
        초기화

        Args:
            credentials_file: 서비스 계정 인증 JSON 파일 경로
            sheet_id: 구글 시트 ID
        """
        # 환경 변수에서 설정 로드
        self.credentials_file = credentials_file or os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        self.sheet_id = sheet_id or os.getenv('GOOGLE_SHEET_ID')

        if not self.sheet_id:
            raise ValueError("구글 시트 ID가 필요합니다. GOOGLE_SHEET_ID 환경변수를 설정하세요.")

        # 구글 시트 연결
        self.client = self._authenticate()
        self.spreadsheet = None
        self.trades_sheet = None

        # 시트 초기화
        self._initialize_sheets()

        # 거래 데이터 임시 저장 (매수-매도 매칭용)
        self.current_positions = {}  # 현재 보유 포지션

    def _authenticate(self):
        """구글 시트 API 인증"""
        try:
            # 인증 범위 설정
            scope = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            # 서비스 계정 인증
            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=scope
            )

            # gspread 클라이언트 생성
            return gspread.authorize(creds)

        except FileNotFoundError:
            print(f"❌ 인증 파일을 찾을 수 없습니다: {self.credentials_file}")
            print("   GOOGLE_SHEETS_SETUP.md 파일을 참고하여 설정하세요.")
            raise
        except Exception as e:
            print(f"❌ 인증 실패: {e}")
            raise

    def _initialize_sheets(self):
        """시트 초기화 및 헤더 설정"""
        try:
            # 스프레드시트 열기
            self.spreadsheet = self.client.open_by_key(self.sheet_id)

            # 거래내역 시트만 설정 (간소화)
            self._setup_trades_sheet()

            print("✅ 구글 시트 연결 성공")

        except Exception as e:
            print(f"❌ 시트 초기화 실패: {e}")
            raise

    def _setup_trades_sheet(self):
        """거래내역 시트 설정"""
        sheet_name = "거래내역"

        # 시트 생성 또는 가져오기
        try:
            self.trades_sheet = self.spreadsheet.worksheet(sheet_name)
        except:
            self.trades_sheet = self.spreadsheet.add_worksheet(
                title=sheet_name, rows=1000, cols=7
            )

        # 헤더가 없으면 추가
        if not self.trades_sheet.get_all_values():
            headers = [
                "기록타입", "날짜", "종목이름", "매수금액", "매도금액", "수익률", "수익금"
            ]
            self.trades_sheet.append_row(headers)

            # 헤더 스타일 설정 (굵게)
            self.trades_sheet.format('A1:G1', {'textFormat': {'bold': True}})

    def record_buy(self, code: str, name: str, price: int, quantity: int,
                   amount: int = None, memo: str = ""):
        """
        매수 기록 (포지션 정보만 저장, 시트에는 매도 시 기록)

        Args:
            code: 종목 코드
            name: 종목명
            price: 매수가
            quantity: 수량
            amount: 매수금액 (없으면 자동계산)
            memo: 메모
        """
        try:
            now = datetime.now()
            amount = amount or (price * quantity)

            # 포지션 정보 저장 (매도 시 한 번에 기록용)
            self.current_positions[code] = {
                "종목명": name,
                "매수가": price,
                "수량": quantity,
                "매수시간": now,
                "매수금액": amount
            }

            print(f"📝 포지션 저장: {name} 매수 ({quantity}주 × {price:,}원)")

        except Exception as e:
            print(f"❌ 매수 정보 저장 실패: {e}")

    def record_sell(self, code: str, name: str, price: int, quantity: int,
                   sell_type: str = "수동", memo: str = ""):
        """
        매도 기록 (매수-매도 정보를 한 행에 기록)

        Args:
            code: 종목 코드
            name: 종목명
            price: 매도가
            quantity: 수량
            sell_type: 매도유형 (익절/손절/청산)
            memo: 메모
        """
        try:
            now = datetime.now()
            sell_amount = price * quantity

            # 기록 타입 결정
            if sell_type == "익절" or sell_type == "손절":
                record_type = "모니터링매도"
            elif sell_type == "청산":
                record_type = "청산"
            else:
                record_type = "테스트"  # 기본값

            # 매수 정보 가져오기
            buy_amount = 0
            profit_rate = 0
            profit_amount = 0

            if code in self.current_positions:
                position = self.current_positions[code]
                buy_amount = position["매수금액"]

                # 수익률 및 수익금 계산
                if buy_amount > 0:
                    profit_rate = ((sell_amount - buy_amount) / buy_amount) * 100
                    profit_amount = sell_amount - buy_amount

            # 거래내역 시트에 기록 (한 행에 매수-매도 정보 모두 기록)
            row = [
                record_type,                   # 기록타입
                now.strftime("%Y-%m-%d"),     # 날짜
                name,                          # 종목이름
                buy_amount,                    # 매수금액
                sell_amount,                   # 매도금액
                f"{profit_rate:.2f}%",        # 수익률
                profit_amount                  # 수익금
            ]

            self.trades_sheet.append_row(row)

            # 수익률에 따른 색상 설정
            last_row = len(self.trades_sheet.get_all_values())

            # 기록타입별 색상
            if record_type == "모니터링매도":
                type_color = {'red': 0.0, 'green': 0.0, 'blue': 0.8}  # 파란색
            elif record_type == "청산":
                type_color = {'red': 1.0, 'green': 0.5, 'blue': 0.0}  # 주황색
            else:
                type_color = {'red': 0.5, 'green': 0.5, 'blue': 0.5}  # 회색

            self.trades_sheet.format(f'A{last_row}', {
                'textFormat': {'foregroundColor': type_color}
            })

            # 수익률 색상 (양수: 빨간색, 음수: 파란색)
            if profit_rate > 0:
                profit_color = {'red': 0.8, 'green': 0.0, 'blue': 0.0}  # 빨간색 (수익)
            else:
                profit_color = {'red': 0.0, 'green': 0.0, 'blue': 0.8}  # 파란색 (손실)

            self.trades_sheet.format(f'F{last_row}:G{last_row}', {
                'textFormat': {'foregroundColor': profit_color}
            })

            # 포지션 제거
            if code in self.current_positions:
                del self.current_positions[code]

            print(f"📝 구글시트 기록: {name} {record_type} (수익률: {profit_rate:+.2f}%)")

        except Exception as e:
            print(f"❌ 매도 기록 실패: {e}")

    def get_daily_summary(self) -> Dict:
        """일별 요약 정보 반환"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")

            # 오늘 거래 내역 가져오기
            all_trades = self.trades_sheet.get_all_values()[1:]  # 헤더 제외
            today_trades = [t for t in all_trades if t[1] == today]  # 날짜는 2번째 컬럼

            if not today_trades:
                return {
                    "날짜": today,
                    "거래건수": 0,
                    "총수익금": 0,
                    "평균수익률": 0
                }

            # 통계 계산
            total_profit = 0
            profit_rates = []

            for trade in today_trades:
                # 수익금 (7번째 컬럼)
                if trade[6]:
                    try:
                        total_profit += float(trade[6])
                    except:
                        pass

                # 수익률 (6번째 컬럼, % 제거)
                if trade[5]:
                    try:
                        rate = float(trade[5].replace('%', ''))
                        profit_rates.append(rate)
                    except:
                        pass

            avg_profit_rate = sum(profit_rates) / len(profit_rates) if profit_rates else 0

            return {
                "날짜": today,
                "거래건수": len(today_trades),
                "총수익금": total_profit,
                "평균수익률": avg_profit_rate,
                "시트URL": f"https://docs.google.com/spreadsheets/d/{self.sheet_id}"
            }

        except Exception as e:
            print(f"❌ 일별 요약 조회 실패: {e}")
            return {}

    def add_test_record(self, name: str, buy_amount: int, sell_amount: int):
        """테스트용 기록 추가 (매수/매도 한 번에)"""
        try:
            now = datetime.now()
            profit_rate = ((sell_amount - buy_amount) / buy_amount) * 100
            profit_amount = sell_amount - buy_amount

            row = [
                "테스트",                      # 기록타입
                now.strftime("%Y-%m-%d"),     # 날짜
                name,                          # 종목이름
                buy_amount,                    # 매수금액
                sell_amount,                   # 매도금액
                f"{profit_rate:.2f}%",        # 수익률
                profit_amount                  # 수익금
            ]

            self.trades_sheet.append_row(row)
            print(f"📝 테스트 기록 추가: {name} (수익률: {profit_rate:+.2f}%)")

        except Exception as e:
            print(f"❌ 테스트 기록 실패: {e}")


# 테스트 코드
if __name__ == "__main__":
    print("구글 시트 연동 테스트")
    print("-" * 40)

    # 레코더 생성
    recorder = GoogleSheetRecorder()

    # 테스트 1: 일반 매매 시뮬레이션
    print("\n[테스트 1: 일반 매매]")
    recorder.record_buy(
        code="005930",
        name="삼성전자",
        price=70000,
        quantity=10
    )

    # 매도 (익절)
    recorder.record_sell(
        code="005930",
        name="삼성전자",
        price=73000,
        quantity=10,
        sell_type="익절"
    )

    # 테스트 2: 손절 시뮬레이션
    print("\n[테스트 2: 손절 매매]")
    recorder.record_buy(
        code="000660",
        name="SK하이닉스",
        price=130000,
        quantity=5
    )

    recorder.record_sell(
        code="000660",
        name="SK하이닉스",
        price=127000,
        quantity=5,
        sell_type="손절"
    )

    # 테스트 3: 청산 시뮬레이션
    print("\n[테스트 3: 일일 청산]")
    recorder.record_buy(
        code="035420",
        name="NAVER",
        price=200000,
        quantity=3
    )

    recorder.record_sell(
        code="035420",
        name="NAVER",
        price=201000,
        quantity=3,
        sell_type="청산"
    )

    # 테스트 4: 테스트 기록
    print("\n[테스트 4: 간단 테스트 기록]")
    recorder.add_test_record(
        name="카카오",
        buy_amount=500000,
        sell_amount=520000
    )

    # 일별 요약 확인
    summary = recorder.get_daily_summary()
    print("\n📱 오늘의 거래 요약:")
    print(f"   거래 건수: {summary.get('거래건수', 0)}건")
    print(f"   총 수익금: {summary.get('총수익금', 0):,.0f}원")
    print(f"   평균 수익률: {summary.get('평균수익률', 0):.2f}%")
    print(f"   시트 URL: {summary.get('시트URL', '')}")

    print("\n✅ 구글 시트에서 확인하세요!")