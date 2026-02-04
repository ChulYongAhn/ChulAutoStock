"""
Phase 3: 스코어링 & 순위화
Phase 2에서 필터링된 10개 종목 중 상위 3개 선별
08:59:00 ~ 08:59:50 실행
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class Phase3Scoring:
    """Phase 3: 스코어링 및 최종 선별"""

    def __init__(self, filtered_stocks: List[Dict]):
        """
        초기화

        Args:
            filtered_stocks: Phase2에서 필터링된 종목 리스트
        """
        self.filtered_stocks = filtered_stocks
        self.scored_stocks = []
        self.top_stocks = []
        self.result_file = f"scoring_result_{datetime.now().strftime('%Y%m%d')}.json"

        # 스코어링 가중치
        self.weights = {
            '등락률': 0.35,      # 35% - 상승률
            '거래량증가율': 0.25,  # 25% - 거래량 증가
            '거래대금': 0.20,    # 20% - 거래 활발도
            '안정성': 0.20       # 20% - 가격 안정성
        }

    def run(self) -> List[Dict]:
        """
        Phase 3 실행

        Returns:
            상위 3개 종목 리스트
        """
        print("\n" + "="*50)
        print("[ Phase 3: 스코어링 & 순위화 ]")
        print(f"시작 시간: {datetime.now().strftime('%H:%M:%S')}")
        print(f"평가 대상: {len(self.filtered_stocks)}개 종목")
        print("="*50)

        if not self.filtered_stocks:
            print("❌ 평가할 종목이 없습니다.")
            return []

        # 스코어링 수행
        self._calculate_scores()

        # 상위 3개 선정
        self._select_top_stocks()

        # 결과 출력
        self._print_results()

        # 결과 저장
        self._save_results()

        return self.top_stocks

    def _calculate_scores(self):
        """각 종목별 점수 계산"""
        print("\n📊 스코어링 진행 중...")

        # 정규화를 위한 최대/최소값 찾기
        max_values = self._get_max_values()
        min_values = self._get_min_values()

        for stock in self.filtered_stocks:
            scores = {}

            # 1. 등락률 점수 (2% = 0점, 4% = 100점)
            change_rate = stock['등락률']
            scores['등락률'] = self._normalize(change_rate, 2.0, 4.0) * 100

            # 2. 거래량 증가율 점수 (전일 대비)
            # 실제로는 전일 거래량과 비교해야 하지만, 현재는 절대 거래량으로 대체
            volume = stock['거래량']
            scores['거래량증가율'] = self._normalize_log(
                volume,
                min_values['거래량'],
                max_values['거래량']
            ) * 100

            # 3. 거래대금 점수 (거래 활발도)
            trading_value = stock['거래대금']
            scores['거래대금'] = self._normalize_log(
                trading_value,
                min_values['거래대금'],
                max_values['거래대금']
            ) * 100

            # 4. 안정성 점수 (등락률이 3%에 가까울수록 높음)
            # 2%나 4%보다 3%가 더 안정적이라고 가정
            stability = 100 - abs(change_rate - 3.0) * 50
            scores['안정성'] = max(0, min(100, stability))

            # 총점 계산 (가중 평균)
            total_score = sum(
                scores[key] * self.weights[key]
                for key in self.weights
            )

            # 결과 저장
            scored_stock = stock.copy()
            scored_stock['점수상세'] = scores
            scored_stock['총점'] = round(total_score, 2)
            self.scored_stocks.append(scored_stock)

        # 총점 기준으로 정렬
        self.scored_stocks.sort(key=lambda x: x['총점'], reverse=True)

    def _get_max_values(self) -> Dict:
        """최대값 계산"""
        if not self.filtered_stocks:
            return {}

        return {
            '거래량': max(s['거래량'] for s in self.filtered_stocks),
            '거래대금': max(s['거래대금'] for s in self.filtered_stocks)
        }

    def _get_min_values(self) -> Dict:
        """최소값 계산"""
        if not self.filtered_stocks:
            return {}

        return {
            '거래량': min(s['거래량'] for s in self.filtered_stocks),
            '거래대금': min(s['거래대금'] for s in self.filtered_stocks)
        }

    def _normalize(self, value: float, min_val: float, max_val: float) -> float:
        """
        값을 0~1 범위로 정규화

        Args:
            value: 정규화할 값
            min_val: 최소값
            max_val: 최대값

        Returns:
            정규화된 값 (0~1)
        """
        if max_val == min_val:
            return 0.5

        normalized = (value - min_val) / (max_val - min_val)
        return max(0, min(1, normalized))

    def _normalize_log(self, value: float, min_val: float, max_val: float) -> float:
        """
        로그 스케일로 정규화 (큰 수치용)

        Args:
            value: 정규화할 값
            min_val: 최소값
            max_val: 최대값

        Returns:
            정규화된 값 (0~1)
        """
        import math

        if max_val <= min_val or value <= 0:
            return 0

        # 로그 변환 후 정규화
        log_value = math.log10(value + 1)
        log_min = math.log10(min_val + 1)
        log_max = math.log10(max_val + 1)

        return self._normalize(log_value, log_min, log_max)

    def _select_top_stocks(self):
        """상위 3개 종목 선정"""
        self.top_stocks = self.scored_stocks[:3]

    def _print_results(self):
        """결과 출력"""
        print("\n" + "="*50)
        print("[ 🏆 최종 선정 종목 TOP 3 ]")
        print("="*50)

        for rank, stock in enumerate(self.top_stocks, 1):
            print(f"\n{rank}위: {stock['종목명']} ({stock['종목코드']})")
            print(f"  총점: {stock['총점']:.2f}점")
            print(f"  현재가: {stock['현재가']:,}원")
            print(f"  등락률: +{stock['등락률']:.2f}%")
            print(f"  거래량: {stock['거래량']:,}주")
            print(f"  거래대금: {stock['거래대금']:,}원")

            # 점수 상세
            print("  [점수 상세]")
            for key, score in stock['점수상세'].items():
                weight = self.weights[key]
                print(f"    {key}: {score:.1f}점 (가중치 {weight*100:.0f}%)")

        print("\n" + "="*50)
        print(f"스코어링 완료: {datetime.now().strftime('%H:%M:%S')}")
        print("="*50)

    def _save_results(self):
        """결과를 파일로 저장"""
        try:
            result = {
                'execution_time': datetime.now().isoformat(),
                'total_evaluated': len(self.filtered_stocks),
                'top_3': self.top_stocks,
                'all_scores': self.scored_stocks
            }

            with open(self.result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"\n💾 결과 저장: {self.result_file}")

        except Exception as e:
            print(f"❌ 결과 저장 실패: {e}")

    def get_top_stocks(self) -> List[Dict]:
        """
        상위 종목 반환

        Returns:
            상위 3개 종목 리스트
        """
        return self.top_stocks


# 테스트 코드
if __name__ == "__main__":
    print("Phase 3 테스트")

    # 테스트용 필터링된 종목 데이터
    test_stocks = [
        {
            '종목코드': '005930',
            '종목명': '삼성전자',
            '전일종가': 50000,
            '현재가': 51500,
            '등락률': 3.0,
            '거래량': 10000000,
            '거래대금': 515000000000
        },
        {
            '종목코드': '000660',
            '종목명': 'SK하이닉스',
            '전일종가': 100000,
            '현재가': 102500,
            '등락률': 2.5,
            '거래량': 5000000,
            '거래대금': 512500000000
        },
        {
            '종목코드': '035720',
            '종목명': '카카오',
            '전일종가': 45000,
            '현재가': 46800,
            '등락률': 4.0,
            '거래량': 3000000,
            '거래대금': 140400000000
        },
        {
            '종목코드': '051910',
            '종목명': 'LG화학',
            '전일종가': 300000,
            '현재가': 307500,
            '등락률': 2.5,
            '거래량': 1000000,
            '거래대금': 307500000000
        },
        {
            '종목코드': '066570',
            '종목명': 'LG전자',
            '전일종가': 80000,
            '현재가': 82800,
            '등락률': 3.5,
            '거래량': 2000000,
            '거래대금': 165600000000
        }
    ]

    # Phase 3 실행
    phase3 = Phase3Scoring(test_stocks)
    top_stocks = phase3.run()

    print(f"\n최종 선정: {len(top_stocks)}개 종목")