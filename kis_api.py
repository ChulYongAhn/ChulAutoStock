"""
한국투자증권 API 클라이언트
주가 조회, 계좌 조회 등 실제 API 호출 기능
"""

import json
import hashlib
import requests
from typing import Dict, Optional, Any
from kis_auth import KISAuth


class KISApi:
    """한국투자증권 API 클라이언트"""

    def __init__(self, auth: KISAuth):
        """
        초기화
        Args:
            auth: KISAuth 인스턴스
        """
        self.auth = auth
        self.base_url = auth.base_url
        self.account_no = auth.account_no

    def _make_request(self, method: str, path: str,
                     headers: Dict = None, params: Dict = None,
                     data: Dict = None) -> Optional[Dict]:
        """
        API 요청 공통 메서드
        """
        url = f"{self.base_url}{path}"

        # 기본 헤더 설정
        request_headers = self.auth.get_headers()
        if headers:
            request_headers.update(headers)

        try:
            if method == "GET":
                response = requests.get(url, headers=request_headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=request_headers, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 실패: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   응답: {e.response.text}")
            return None

    def get_current_price(self, stock_code: str) -> Optional[Dict]:
        """
        현재가 조회 (국내 주식)

        Args:
            stock_code: 종목 코드 (6자리)

        Returns:
            현재가 정보 딕셔너리
        """
        path = "/uapi/domestic-stock/v1/quotations/inquire-price"

        # 거래소 코드 (J: 주식)
        headers = {
            "tr_id": "FHKST01010100"  # 주식현재가 시세 조회
        }

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # 시장 분류 코드
            "FID_INPUT_ISCD": stock_code     # 종목 코드
        }

        result = self._make_request("GET", path, headers=headers, params=params)

        if result and result.get("rt_cd") == "0":
            output = result.get("output", {})
            return {
                "종목코드": stock_code,
                "현재가": int(output.get("stck_prpr", 0)),  # 주식 현재가
                "전일대비": int(output.get("prdy_vrss", 0)),  # 전일 대비
                "등락률": float(output.get("prdy_ctrt", 0)),  # 전일 대비율
                "시가": int(output.get("stck_oprc", 0)),  # 시가
                "고가": int(output.get("stck_hgpr", 0)),  # 고가
                "저가": int(output.get("stck_lwpr", 0)),  # 저가
                "거래량": int(output.get("acml_vol", 0)),  # 누적 거래량
                "거래대금": int(output.get("acml_tr_pbmn", 0)) * 1000000,  # 누적 거래대금 (백만원 단위)
            }

        return None

    def get_balance(self) -> Optional[Dict]:
        """
        계좌 잔고 조회

        Returns:
            잔고 정보 딕셔너리
        """
        path = "/uapi/domestic-stock/v1/trading/inquire-psbl-order"

        # 실전/모의 구분
        if self.auth.is_real:
            tr_id = "TTTC8908R"  # 실전투자
        else:
            tr_id = "VTTC8908R"  # 모의투자

        headers = {
            "tr_id": tr_id
        }

        # 계좌번호 처리 (10자리 또는 8자리-2자리 형식 지원)
        if "-" in self.account_no:
            account_parts = self.account_no.split("-")
        else:
            # 10자리 계좌번호의 경우 앞 8자리와 뒤 2자리로 분리
            if len(self.account_no) == 10:
                account_parts = [self.account_no[:8], self.account_no[8:]]
            else:
                print(f"❌ 잘못된 계좌번호 형식: {self.account_no}")
                return None

        params = {
            "CANO": account_parts[0],  # 계좌번호 앞 8자리
            "ACNT_PRDT_CD": account_parts[1],  # 계좌상품코드 뒤 2자리
            "PDNO": "",  # 종목번호 (전체 조회시 빈값)
            "ORD_UNPR": "",  # 주문단가
            "ORD_DVSN": "01",  # 주문구분 (01: 시장가)
            "CMA_EVLU_AMT_ICLD_YN": "N",  # CMA평가금액포함여부
            "OVRS_ICLD_YN": "N"  # 해외포함여부
        }

        result = self._make_request("GET", path, headers=headers, params=params)

        if result and result.get("rt_cd") == "0":
            output = result.get("output", {})
            return {
                "주문가능현금": int(output.get("ord_psbl_cash", 0)),  # 주문 가능 현금
                "예수금": int(output.get("dnca_tot_amt", 0)),  # 예수금 총액
                "총평가금액": int(output.get("tot_evlu_amt", 0)),  # 총 평가 금액
                "순자산금액": int(output.get("nass_amt", 0)),  # 순자산 금액
                "매입금액": int(output.get("pchs_amt", 0)),  # 매입 금액
                "평가손익": int(output.get("evlu_pfls_amt", 0)),  # 평가 손익 금액
                "수익률": float(output.get("evlu_pfls_rt", 0))  # 평가 손익율
            }

        return None

    def get_api_usage(self) -> Optional[Dict]:
        """
        API 사용량 조회

        Returns:
            API 사용량 정보
        """
        # 간단한 조회 API를 호출하여 응답 헤더에서 사용량 정보 추출
        path = "/uapi/domestic-stock/v1/quotations/inquire-price"

        headers = {
            "tr_id": "FHKST01010100"
        }

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": "005930"  # 삼성전자로 테스트
        }

        try:
            response = requests.get(
                f"{self.base_url}{path}",
                headers={**self.auth.get_headers(), **headers},
                params=params
            )

            # 응답 헤더에서 사용량 정보 추출
            if response.headers:
                usage_info = {
                    "일일_한도": response.headers.get("tr_cont_max", "N/A"),
                    "일일_사용": response.headers.get("tr_cont", "N/A"),
                    "일일_남은횟수": "N/A",
                    "연속_여부": response.headers.get("tr_cont_yn", "N")
                }

                # 남은 횟수 계산
                try:
                    if usage_info["일일_한도"] != "N/A" and usage_info["일일_사용"] != "N/A":
                        daily_remain = int(usage_info["일일_한도"]) - int(usage_info["일일_사용"])
                        usage_info["일일_남은횟수"] = str(daily_remain)

                        # 사용률 계산
                        usage_rate = (int(usage_info["일일_사용"]) / int(usage_info["일일_한도"])) * 100
                        usage_info["사용률"] = f"{usage_rate:.1f}%"
                except:
                    pass

                return usage_info

        except Exception as e:
            # 사용량 조회 실패는 무시
            pass

        return None

    def get_stock_balance(self) -> Optional[list]:
        """
        보유 주식 잔고 조회

        Returns:
            보유 주식 리스트
        """
        path = "/uapi/domestic-stock/v1/trading/inquire-balance"

        # 실전/모의 구분
        if self.auth.is_real:
            tr_id = "TTTC8434R"  # 실전투자
        else:
            tr_id = "VTTC8434R"  # 모의투자

        headers = {
            "tr_id": tr_id
        }

        # 계좌번호 처리 (10자리 또는 8자리-2자리 형식 지원)
        if "-" in self.account_no:
            account_parts = self.account_no.split("-")
        else:
            # 10자리 계좌번호의 경우 앞 8자리와 뒤 2자리로 분리
            if len(self.account_no) == 10:
                account_parts = [self.account_no[:8], self.account_no[8:]]
            else:
                return None

        params = {
            "CANO": account_parts[0],
            "ACNT_PRDT_CD": account_parts[1],
            "AFHR_FLPR_YN": "N",  # 시간외단일가여부
            "OFL_YN": "",  # 오프라인여부
            "INQR_DVSN": "02",  # 조회구분 (01: 대출일별, 02: 종목별)
            "UNPR_DVSN": "01",  # 단가구분
            "FUND_STTL_ICLD_YN": "N",  # 펀드결제분포함여부
            "FNCG_AMT_AUTO_RDPT_YN": "N",  # 융자금액자동상환여부
            "PRCS_DVSN": "01",  # 처리구분 (00: 전일매매포함, 01: 전일매매미포함)
            "CTX_AREA_FK100": "",  # 연속조회검색조건100
            "CTX_AREA_NK100": ""  # 연속조회키100
        }

        result = self._make_request("GET", path, headers=headers, params=params)

        if result and result.get("rt_cd") == "0":
            stocks = []
            for item in result.get("output1", []):
                if item.get("hldg_qty") and int(item.get("hldg_qty", 0)) > 0:
                    stocks.append({
                        "종목코드": item.get("pdno"),
                        "종목명": item.get("prdt_name"),
                        "보유수량": int(item.get("hldg_qty", 0)),
                        "매입단가": float(item.get("pchs_avg_pric", 0)),
                        "현재가": int(item.get("prpr", 0)),
                        "평가금액": int(item.get("evlu_amt", 0)),
                        "평가손익": int(item.get("evlu_pfls_amt", 0)),
                        "수익률": float(item.get("evlu_pfls_rt", 0))
                    })
            return stocks

        return None

    def buy_stock(self, stock_code: str, quantity: int, order_type: str = "01") -> Optional[Dict]:
        """
        주식 매수 주문

        Args:
            stock_code: 종목 코드
            quantity: 주문 수량
            order_type: 주문 구분 (01: 시장가, 00: 지정가)

        Returns:
            주문 결과
        """
        path = "/uapi/domestic-stock/v1/trading/order-cash"

        # 실전/모의 구분
        if self.auth.is_real:
            tr_id = "TTTC0802U"  # 실전 매수
        else:
            tr_id = "VTTC0802U"  # 모의 매수

        headers = {
            "tr_id": tr_id
        }

        # 계좌번호 처리
        if "-" in self.account_no:
            account_parts = self.account_no.split("-")
        else:
            if len(self.account_no) == 10:
                account_parts = [self.account_no[:8], self.account_no[8:]]
            else:
                return None

        data = {
            "CANO": account_parts[0],
            "ACNT_PRDT_CD": account_parts[1],
            "PDNO": stock_code,  # 종목코드
            "ORD_DVSN": order_type,  # 주문구분
            "ORD_QTY": str(quantity),  # 주문수량
            "ORD_UNPR": "0" if order_type == "01" else "",  # 주문단가 (시장가는 0)
        }

        result = self._make_request("POST", path, headers=headers, data=data)

        if result and result.get("rt_cd") == "0":
            output = result.get("output", {})
            return {
                "주문번호": output.get("ODNO"),
                "주문시간": output.get("ORD_TMD"),
                "종목코드": stock_code,
                "주문수량": quantity,
                "주문구분": "시장가" if order_type == "01" else "지정가",
                "메시지": result.get("msg1")
            }
        else:
            print(f"❌ 매수 주문 실패: {result.get('msg1') if result else '응답 없음'}")
            return None

    def sell_stock(self, stock_code: str, quantity: int, order_type: str = "01") -> Optional[Dict]:
        """
        주식 매도 주문

        Args:
            stock_code: 종목 코드
            quantity: 주문 수량
            order_type: 주문 구분 (01: 시장가, 00: 지정가)

        Returns:
            주문 결과
        """
        path = "/uapi/domestic-stock/v1/trading/order-cash"

        # 실전/모의 구분
        if self.auth.is_real:
            tr_id = "TTTC0801U"  # 실전 매도
        else:
            tr_id = "VTTC0801U"  # 모의 매도

        headers = {
            "tr_id": tr_id
        }

        # 계좌번호 처리
        if "-" in self.account_no:
            account_parts = self.account_no.split("-")
        else:
            if len(self.account_no) == 10:
                account_parts = [self.account_no[:8], self.account_no[8:]]
            else:
                return None

        data = {
            "CANO": account_parts[0],
            "ACNT_PRDT_CD": account_parts[1],
            "PDNO": stock_code,  # 종목코드
            "ORD_DVSN": order_type,  # 주문구분
            "ORD_QTY": str(quantity),  # 주문수량
            "ORD_UNPR": "0" if order_type == "01" else "",  # 주문단가 (시장가는 0)
        }

        result = self._make_request("POST", path, headers=headers, data=data)

        if result and result.get("rt_cd") == "0":
            output = result.get("output", {})
            return {
                "주문번호": output.get("ODNO"),
                "주문시간": output.get("ORD_TMD"),
                "종목코드": stock_code,
                "주문수량": quantity,
                "주문구분": "시장가" if order_type == "01" else "지정가",
                "메시지": result.get("msg1")
            }
        else:
            print(f"❌ 매도 주문 실패: {result.get('msg1') if result else '응답 없음'}")
            return None

    def get_orders(self) -> Optional[list]:
        """
        주문 내역 조회

        Returns:
            주문 리스트
        """
        path = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"

        # 실전/모의 구분
        if self.auth.is_real:
            tr_id = "TTTC8001R"  # 실전
        else:
            tr_id = "VTTC8001R"  # 모의

        headers = {
            "tr_id": tr_id
        }

        # 계좌번호 처리
        if "-" in self.account_no:
            account_parts = self.account_no.split("-")
        else:
            if len(self.account_no) == 10:
                account_parts = [self.account_no[:8], self.account_no[8:]]
            else:
                return None

        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")

        params = {
            "CANO": account_parts[0],
            "ACNT_PRDT_CD": account_parts[1],
            "INQR_STRT_DT": today,  # 조회시작일
            "INQR_END_DT": today,  # 조회종료일
            "SLL_BUY_DVSN_CD": "00",  # 매도매수구분 (00: 전체)
            "INQR_DVSN": "00",  # 조회구분
            "PDNO": "",  # 종목번호 (전체)
            "CCLD_DVSN": "00",  # 체결구분 (00: 전체)
            "ORD_GNO_BRNO": "",
            "ODNO": "",  # 주문번호
            "INQR_DVSN_3": "00",
            "INQR_DVSN_1": "",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }

        result = self._make_request("GET", path, headers=headers, params=params)

        if result and result.get("rt_cd") == "0":
            orders = []
            for item in result.get("output1", []):
                orders.append({
                    "주문번호": item.get("odno"),
                    "종목코드": item.get("pdno"),
                    "종목명": item.get("prdt_name"),
                    "매매구분": "매수" if item.get("sll_buy_dvsn_cd") == "02" else "매도",
                    "주문수량": int(item.get("ord_qty", 0)),
                    "체결수량": int(item.get("tot_ccld_qty", 0)),
                    "체결단가": float(item.get("avg_prvs", 0)),
                    "주문시간": item.get("ord_tmd"),
                    "체결시간": item.get("ccld_tmd"),
                    "주문상태": item.get("ord_gno_brno")
                })
            return orders

        return None


# 테스트 코드
if __name__ == "__main__":
    print("=" * 50)
    print("한국투자증권 API 테스트")
    print("=" * 50)

    # 인증
    auth = KISAuth(is_real=True)
    api = KISApi(auth)

    # 삼성전자 현재가 조회
    price_info = api.get_current_price("005930")
    if price_info:
        print("\n삼성전자 현재가:")
        for key, value in price_info.items():
            print(f"  {key}: {value:,}")

    # 계좌 잔고 조회
    balance = api.get_balance()
    if balance:
        print("\n계좌 잔고:")
        for key, value in balance.items():
            if isinstance(value, (int, float)):
                print(f"  {key}: {value:,}")
            else:
                print(f"  {key}: {value}")