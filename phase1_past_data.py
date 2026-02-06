"""
Phase 1: 과거 탐색 모드
08:30 ~ 08:50 실행
코스피 100개 종목의 전일 데이터를 조회하여 캐싱
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
from pykrx import stock
from stock_list import KOSPI_100, get_stock_name
from slack_service import slack_message


class Phase1PastData:
    """Phase 1: 전일 데이터 조회 및 캐싱"""

    def __init__(self):
        self.cache_file = "past_data_cache.json"
        self.cached_data = {}

    def run(self) -> Dict:
        """
        Phase 1 실행
        Returns:
            처리 결과 딕셔너리
        """
        print("\n" + "="*50)
        print("[ Phase 1: 과거 데이터 탐색 시작 ]")
        print(f"시작 시간: {datetime.now().strftime('%H:%M:%S')}")
        print(f"대상 종목: {len(KOSPI_100)}개")
        print("="*50)

        # Slack 알림: Phase 1 시작
        slack_message(f"📊 Phase 1 시작 - KOSPI 100 종목 전일 데이터 수집")

        # 캐시 확인
        if self._load_cache():
            print("✅ 오늘 캐시된 데이터 사용")
            slack_message(f"✅ Phase 1: 캐시 사용 ({len(self.cached_data)}개 종목)")
            return self.cached_data

        # 전일 날짜 계산 (주말 고려)
        yesterday = self._get_last_trading_day()
        print(f"📅 조회 기준일: {yesterday.strftime('%Y-%m-%d')}")

        # 데이터 수집
        success_count = 0
        fail_count = 0
        total_count = len(KOSPI_100)

        for idx, (code, name) in enumerate(KOSPI_100.items(), 1):
            try:
                # 진행상황 표시
                if idx % 10 == 0 or idx == 1:
                    print(f"\n진행중... [{idx}/{total_count}]")

                # pykrx로 전일 데이터 조회
                data = self._get_stock_data(code, yesterday)

                if data:
                    self.cached_data[code] = data
                    success_count += 1

                    # 샘플 출력 (처음 3개, 마지막 1개만)
                    if idx <= 3 or idx == total_count:
                        print(f"  {name}({code}): 종가 {data['종가']:,}원, "
                              f"거래량 {data['거래량']:,}주")
                else:
                    fail_count += 1

                # 대기 없이 바로 다음 종목 조회
                # API가 알아서 처리하고 응답 속도에 맞춰 진행됨

            except Exception as e:
                print(f"  ❌ {name}({code}) 조회 실패: {e}")
                fail_count += 1

        # 결과 요약
        print("\n" + "="*50)
        print("[ Phase 1 완료 ]")
        print(f"✅ 성공: {success_count}개")
        print(f"❌ 실패: {fail_count}개")
        print(f"완료 시간: {datetime.now().strftime('%H:%M:%S')}")
        print("="*50)

        # Slack 알림: Phase 1 완료
        slack_msg = f"✅ Phase 1 완료\n"
        slack_msg += f"• 성공: {success_count}개\n"
        slack_msg += f"• 실패: {fail_count}개\n"
        slack_msg += f"• 시간: {datetime.now().strftime('%H:%M:%S')}"
        slack_message(slack_msg)

        # 캐시 저장
        if success_count > 0:
            self._save_cache()

        return self.cached_data

    def _get_stock_data(self, code: str, date: datetime) -> Optional[Dict]:
        """
        특정 종목의 전일 데이터 조회

        Args:
            code: 종목 코드
            date: 조회 날짜

        Returns:
            종목 데이터 딕셔너리
        """
        try:
            # pykrx는 날짜를 문자열로 받음
            date_str = date.strftime("%Y%m%d")

            # OHLCV 데이터 조회
            df = stock.get_market_ohlcv(date_str, date_str, code)

            if df.empty:
                return None

            # 데이터 추출 (Series를 dict로 변환)
            row = df.iloc[0]

            return {
                "종목명": get_stock_name(code),
                "날짜": date.strftime("%Y-%m-%d"),
                "시가": int(row['시가']),
                "고가": int(row['고가']),
                "저가": int(row['저가']),
                "종가": int(row['종가']),
                "거래량": int(row['거래량']),
                "거래대금": int(row['거래대금']) if '거래대금' in row else 0,
                "등락률": float(row['등락률']) if '등락률' in row else 0.0,
                "조회시간": datetime.now().isoformat()
            }

        except Exception as e:
            return None

    def _get_last_trading_day(self) -> datetime:
        """
        마지막 거래일 계산 (주말, 공휴일 고려)

        Returns:
            마지막 거래일 datetime
        """
        today = datetime.now()

        # 오늘이 월요일이면 지난 금요일
        if today.weekday() == 0:  # Monday
            return today - timedelta(days=3)
        # 오늘이 일요일이면 지난 금요일
        elif today.weekday() == 6:  # Sunday
            return today - timedelta(days=2)
        # 오늘이 토요일이면 어제(금요일)
        elif today.weekday() == 5:  # Saturday
            return today - timedelta(days=1)
        # 평일이면 어제
        else:
            return today - timedelta(days=1)

    def _load_cache(self) -> bool:
        """
        캐시 파일 로드

        Returns:
            캐시 사용 가능 여부
        """
        if not os.path.exists(self.cache_file):
            return False

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)

            # 캐시 날짜 확인 (오늘 캐시인지)
            cache_date = cache.get('cache_date', '')
            today = datetime.now().strftime("%Y-%m-%d")

            if cache_date == today:
                self.cached_data = cache.get('data', {})
                print(f"📂 캐시 로드 성공 (생성: {cache.get('cache_time', '')})")
                return True

        except Exception as e:
            print(f"⚠️  캐시 로드 실패: {e}")

        return False

    def _save_cache(self):
        """캐시 파일 저장"""
        try:
            cache = {
                'cache_date': datetime.now().strftime("%Y-%m-%d"),
                'cache_time': datetime.now().strftime("%H:%M:%S"),
                'data': self.cached_data
            }

            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)

            print(f"💾 캐시 저장 완료: {self.cache_file}")

        except Exception as e:
            print(f"❌ 캐시 저장 실패: {e}")

    def get_cached_data(self) -> Dict:
        """
        캐시된 데이터 반환

        Returns:
            종목별 전일 데이터 딕셔너리
        """
        return self.cached_data


# 테스트 코드
if __name__ == "__main__":
    phase1 = Phase1PastData()

    # 테스트용: 일부 종목만 조회
    print("Phase 1 테스트 (상위 5개 종목만)")

    # 임시로 종목 수 제한
    original_stocks = dict(list(KOSPI_100.items())[:5])
    KOSPI_100.clear()
    KOSPI_100.update(original_stocks)

    result = phase1.run()

    print(f"\n총 {len(result)}개 종목 데이터 수집 완료")