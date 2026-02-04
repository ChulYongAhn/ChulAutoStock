# AI Guide - 프로젝트 컨텍스트

## 사용자 프로필
- **경험**: Unity 개발 경험 많음
- **Python 수준**: 초보 (거의 모름)
- **특이사항**:
  - Python 기본 개념 설명 필요
  - 용어/개념을 쉽게 풀어서 설명
  - 단계별 상세한 가이드 제공

## 프로젝트 정보
- **이름**: ChulAutoStock
- **목적**: 한국투자증권 API를 이용한 자동 주식 트레이딩
- **주요 기술**: Python, pykrx, 한국투자증권 API

## 환경 설정
- **Python 환경**: Conda 가상환경 `chulstock` 사용
- **인터프리터 경로**: `/opt/homebrew/Caskroom/miniconda/base/envs/chulstock/bin/python`
- **주요 패키지**: pykrx, python-dotenv

## 중요 파일
- `.env`: API 키 등 민감정보 저장 (Git 제외)
- `main.py`: 메인 실행 파일

## AI 어시스턴트 지침
1. Python 초보자에게 설명하듯 쉽게 설명
2. 전문 용어 사용 시 반드시 설명 추가
3. 코드 변경 시 "왜" 그렇게 하는지 설명
4. 에러 발생 시 원인과 해결법을 상세히 설명
5. Unity 개념에 비유하면 이해가 빠름
