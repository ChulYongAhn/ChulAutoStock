"""
Slack 알림 서비스 모듈
거래 로그 및 중요 이벤트를 Slack으로 전송
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Optional, List
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class SlackService:
    """Slack 알림 서비스"""

    def __init__(self):
        """초기화"""
        self.webhook_url = os.getenv("SLACK_WEBHOOK")
        self.enabled = bool(self.webhook_url)

        if not self.enabled:
            print("⚠️ Slack 웹훅이 설정되지 않음 (.env 파일 확인)")

    def send_message(self, text: str, blocks: List[Dict] = None) -> bool:
        """
        Slack 메시지 전송

        Args:
            text: 메시지 텍스트
            blocks: Slack Block Kit 형식 (선택)

        Returns:
            전송 성공 여부
        """
        if not self.enabled:
            return False

        try:
            payload = {"text": text}
            if blocks:
                payload["blocks"] = blocks

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            return response.status_code == 200

        except Exception as e:
            print(f"❌ Slack 전송 실패: {e}")
            return False

    def send_simple(self, message: str, emoji: str = "📢") -> bool:
        """
        간단한 메시지 전송

        Args:
            message: 메시지 내용
            emoji: 이모지 (기본: 📢)
        """
        text = f"{emoji} {message}"
        return self.send_message(text)

    def send_error(self, error_msg: str, details: str = None) -> bool:
        """
        에러 메시지 전송

        Args:
            error_msg: 에러 메시지
            details: 상세 내용
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 에러 발생",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*메시지:* {error_msg}"
                }
            }
        ]

        if details:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{details}```"
                }
            })

        blocks.append({
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }]
        })

        return self.send_message("에러 발생", blocks)

    def send_trading_alert(self, action: str, stock_code: str, stock_name: str,
                          quantity: int, price: int, amount: int,
                          profit: float = None, is_real: bool = True) -> bool:
        """
        거래 알림 전송

        Args:
            action: 매수/매도
            stock_code: 종목코드
            stock_name: 종목명
            quantity: 수량
            price: 가격
            amount: 금액
            profit: 수익률 (매도시)
            is_real: 실전/모의
        """
        mode = "실전" if is_real else "모의"
        emoji = "💰" if is_real else "🧪"
        color = "#FF0000" if is_real else "#00FF00"

        if action == "매수":
            icon = "🛒"
            title = f"{icon} 매수 주문"
        elif action == "매도":
            icon = "📤"
            title = f"{icon} 매도 주문"
        else:
            icon = "📊"
            title = f"{icon} 거래 알림"

        # 메시지 구성
        fields = [
            {"title": "종목", "value": f"{stock_name}({stock_code})", "short": True},
            {"title": "수량", "value": f"{quantity:,}주", "short": True},
            {"title": "가격", "value": f"{price:,}원", "short": True},
            {"title": "금액", "value": f"{amount:,}원", "short": True},
        ]

        if profit is not None and action == "매도":
            profit_emoji = "🔴" if profit < 0 else "🟢"
            fields.append({
                "title": "수익률",
                "value": f"{profit_emoji} {profit:+.2f}%",
                "short": True
            })

        # Slack 메시지 (attachments 형식)
        message = {
            "text": f"{emoji} [{mode}] {title}",
            "attachments": [{
                "color": color,
                "fields": fields,
                "footer": "ChulAutoStock",
                "footer_icon": "https://cdn-icons-png.flaticon.com/512/2936/2936712.png",
                "ts": int(datetime.now().timestamp())
            }]
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={"Content-Type": "application/json"}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Slack 거래 알림 실패: {e}")
            return False

    def send_daily_report(self, report: Dict, is_real: bool = True) -> bool:
        """
        일일 리포트 전송

        Args:
            report: 일일 리포트 딕셔너리
            is_real: 실전/모의
        """
        mode = "실전" if is_real else "모의"
        emoji = "💰" if is_real else "🧪"

        # 수익률에 따른 이모지
        daily_return = report.get("수익률", {}).get("일일_수익률", 0)
        if daily_return > 0:
            result_emoji = "🎉"
            color = "good"
        elif daily_return < 0:
            result_emoji = "😢"
            color = "danger"
        else:
            result_emoji = "😐"
            color = "warning"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{result_emoji} 일일 거래 리포트",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*모드:* {emoji} {mode}"},
                    {"type": "mrkdwn", "text": f"*날짜:* {report.get('거래일', 'N/A')}"}
                ]
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*💰 계좌 현황*"
                },
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*총평가:* {report.get('계좌정보', {}).get('총평가금액', 0):,}원"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*일일손익:* {report.get('계좌정보', {}).get('평가손익', 0):+,}원"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📊 거래 내역*"
                },
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*매수:* {report.get('거래내역', {}).get('매수_종목수', 0)}종목"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*익절:* {report.get('거래내역', {}).get('익절_횟수', 0)}회"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*손절:* {report.get('거래내역', {}).get('손절_횟수', 0)}회"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*수익률:* {daily_return:+.2f}%"
                    }
                ]
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"API 사용: {report.get('API사용량', {}).get('사용률', 'N/A')} | ChulAutoStock"
                    }
                ]
            }
        ]

        return self.send_message(f"{result_emoji} [{mode}] 일일 리포트", blocks)

    def send_phase_alert(self, phase: str, status: str, details: str = None) -> bool:
        """
        Phase 진행 상황 알림

        Args:
            phase: Phase 이름 (0~5)
            status: 상태 (시작/완료/실패)
            details: 상세 내용
        """
        emoji_map = {
            "Phase 0": "🔐",
            "Phase 1": "📊",
            "Phase 2": "👀",
            "Phase 3": "🎯",
            "Phase 4": "💹",
            "Phase 5": "🏁",
        }

        emoji = emoji_map.get(phase, "📍")

        if status == "시작":
            color = "#36a64f"
            text = f"{emoji} {phase} 시작"
        elif status == "완료":
            color = "#2eb886"
            text = f"{emoji} {phase} 완료"
        elif status == "실패":
            color = "#ff0000"
            text = f"❌ {phase} 실패"
        else:
            color = "#808080"
            text = f"{emoji} {phase} {status}"

        message = {
            "attachments": [{
                "color": color,
                "text": text,
                "footer": datetime.now().strftime("%H:%M:%S")
            }]
        }

        if details:
            message["attachments"][0]["fields"] = [{
                "value": details,
                "short": False
            }]

        try:
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={"Content-Type": "application/json"}
            )
            return response.status_code == 200
        except:
            return False

    def send_buy_test_log(self, log_data: Dict, is_real: bool = True) -> bool:
        """
        매수 테스트 전체 로그 전송

        Args:
            log_data: 로그 데이터
            is_real: 실전/모의
        """
        mode = "실전" if is_real else "모의"
        emoji = "💰" if is_real else "🧪"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📈 매수 테스트 로그 - {mode}",
                    "emoji": True
                }
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*💰 매수 전 상태*"
                },
                "fields": [
                    {"type": "mrkdwn", "text": f"*주문가능:* {log_data.get('cash_before', 0):,}원"},
                    {"type": "mrkdwn", "text": f"*총평가:* {log_data.get('total_before', 0):,}원"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📊 종목 정보*"
                },
                "fields": [
                    {"type": "mrkdwn", "text": f"*종목:* {log_data.get('stock_name')}({log_data.get('stock_code')})"},
                    {"type": "mrkdwn", "text": f"*현재가:* {log_data.get('current_price', 0):,}원"},
                    {"type": "mrkdwn", "text": f"*등락률:* {log_data.get('change_rate', 0):+.2f}%"},
                    {"type": "mrkdwn", "text": f"*거래량:* {log_data.get('volume', 0):,}주"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🛒 매수 정보*"
                },
                "fields": [
                    {"type": "mrkdwn", "text": f"*수량:* {log_data.get('quantity', 0)}주"},
                    {"type": "mrkdwn", "text": f"*필요금액:* {log_data.get('amount', 0):,}원"},
                    {"type": "mrkdwn", "text": f"*예상잔액:* {log_data.get('expected_balance', 0):,}원"},
                    {"type": "mrkdwn", "text": f"*주문번호:* {log_data.get('order_no', 'N/A')}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*💰 매수 후 상태*"
                },
                "fields": [
                    {"type": "mrkdwn", "text": f"*주문가능:* {log_data.get('cash_after', 0):,}원"},
                    {"type": "mrkdwn", "text": f"*현금변동:* {log_data.get('cash_change', 0):,}원"}
                ]
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }]
            }
        ]

        return self.send_message(f"{emoji} 매수 테스트 완료", blocks)

    def send_sell_test_log(self, log_data: Dict, is_real: bool = True) -> bool:
        """
        매도 테스트 전체 로그 전송

        Args:
            log_data: 로그 데이터
            is_real: 실전/모의
        """
        mode = "실전" if is_real else "모의"
        emoji = "💰" if is_real else "🧪"

        # 수익률에 따른 색상
        profit_rate = log_data.get('profit_rate', 0)
        profit_emoji = "🔴" if profit_rate < 0 else "🟢"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📉 매도 테스트 로그 - {mode}",
                    "emoji": True
                }
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📋 보유 종목*"
                },
                "fields": [
                    {"type": "mrkdwn", "text": f"*종목:* {log_data.get('stock_name')}({log_data.get('stock_code')})"},
                    {"type": "mrkdwn", "text": f"*보유수량:* {log_data.get('holding_quantity', 0)}주"},
                    {"type": "mrkdwn", "text": f"*매입단가:* {log_data.get('avg_price', 0):,.0f}원"},
                    {"type": "mrkdwn", "text": f"*평가손익:* {log_data.get('holding_profit', 0):+,}원"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📤 매도 정보*"
                },
                "fields": [
                    {"type": "mrkdwn", "text": f"*매도수량:* {log_data.get('quantity', 0)}주"},
                    {"type": "mrkdwn", "text": f"*매도가격:* {log_data.get('current_price', 0):,}원"},
                    {"type": "mrkdwn", "text": f"*예상수익:* {log_data.get('profit', 0):+,}원"},
                    {"type": "mrkdwn", "text": f"*수익률:* {profit_emoji} {profit_rate:+.2f}%"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*💰 매도 후 상태*"
                },
                "fields": [
                    {"type": "mrkdwn", "text": f"*주문가능:* {log_data.get('cash_after', 0):,}원"},
                    {"type": "mrkdwn", "text": f"*현금증가:* +{log_data.get('cash_increase', 0):,}원"},
                    {"type": "mrkdwn", "text": f"*남은주식:* {log_data.get('remaining', 0)}주"},
                    {"type": "mrkdwn", "text": f"*주문번호:* {log_data.get('order_no', 'N/A')}"}
                ]
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }]
            }
        ]

        return self.send_message(f"{emoji} 매도 테스트 완료", blocks)

    def send_balance_update(self, balance: Dict, is_real: bool = True) -> bool:
        """
        잔액 변동 알림

        Args:
            balance: 잔액 정보
            is_real: 실전/모의
        """
        mode = "실전" if is_real else "모의"
        emoji = "💰" if is_real else "🧪"

        text = f"{emoji} [{mode}] 잔액 업데이트\n"
        text += f"• 주문가능: {balance.get('주문가능현금', 0):,}원\n"
        text += f"• 총평가: {balance.get('총평가금액', 0):,}원\n"
        text += f"• 손익: {balance.get('평가손익', 0):+,}원"

        return self.send_simple(text, "")


# 싱글톤 인스턴스
_slack_instance = None


def get_slack() -> SlackService:
    """Slack 서비스 싱글톤 인스턴스 반환"""
    global _slack_instance
    if _slack_instance is None:
        _slack_instance = SlackService()
    return _slack_instance


# 간편 함수들
def slack_message(message: str) -> bool:
    """간단한 메시지 전송"""
    return get_slack().send_simple(message)


def slack_error(error_msg: str, details: str = None) -> bool:
    """에러 알림 전송"""
    return get_slack().send_error(error_msg, details)


def slack_trade(action: str, stock_code: str, stock_name: str,
               quantity: int, price: int, amount: int,
               profit: float = None, is_real: bool = True) -> bool:
    """거래 알림 전송"""
    return get_slack().send_trading_alert(
        action, stock_code, stock_name,
        quantity, price, amount, profit, is_real
    )


def slack_daily_report(report: Dict, is_real: bool = True) -> bool:
    """일일 리포트 전송"""
    return get_slack().send_daily_report(report, is_real)


# 테스트 코드
if __name__ == "__main__":
    print("Slack 서비스 테스트")
    print("="*50)

    slack = SlackService()

    if slack.enabled:
        print("✅ Slack 웹훅 설정됨")

        # 테스트 메시지
        if slack.send_simple("🎉 ChulAutoStock Slack 연동 테스트 성공!"):
            print("✅ 테스트 메시지 전송 성공")

        # 거래 알림 테스트
        slack.send_trading_alert(
            action="매수",
            stock_code="005930",
            stock_name="삼성전자",
            quantity=10,
            price=70000,
            amount=700000,
            is_real=False
        )
        print("✅ 거래 알림 테스트 완료")

    else:
        print("❌ Slack 웹훅이 설정되지 않음")
        print("   .env 파일에 SLACK_WEBHOOK을 추가하세요")