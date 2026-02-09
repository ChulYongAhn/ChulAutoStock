# 🖥️ 새 컴퓨터 설정 가이드

## 1. Git Clone
```bash
git clone [your-repo-url]
cd ChulAutoStock
```

## 2. Python 환경 설정
```bash
# 가상환경 생성 (권장)
python -m venv venv

# 가상환경 활성화
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

## 3. 필수 파일 생성

### 3.1 `.env` 파일 생성
프로젝트 루트에 `.env` 파일을 생성하고 아래 내용 입력:
```
# 모드 설정 (true=실전투자, false=모의투자)
IS_REAL_TRADING=true

# 실전투자용
KIS_APP_KEY=your_app_key_here
KIS_APP_SECRET=your_app_secret_here
KIS_ACCOUNT_NO=your_account_number

# 모의투자용 (선택)
KIS_APP_KEY_VIRTUAL=your_virtual_key
KIS_APP_SECRET_VIRTUAL=your_virtual_secret
KIS_ACCOUNT_NO_VIRTUAL=your_virtual_account

# Slack Webhook
SLACK_WEBHOOK=your_webhook_url

# 구글 시트 설정
GOOGLE_SHEET_ID=161qmtgCq6mDcckqrQj9hyLhGjOTvHtzeJq53Rrry5fo
GOOGLE_CREDENTIALS_FILE=credentials.json
```

### 3.2 `credentials.json` 파일
1. 기존 컴퓨터에서 `credentials.json` 파일 복사
2. 프로젝트 루트에 붙여넣기
3. **절대 Git에 올리지 말 것!**

## 4. 테스트
```bash
# API 연결 테스트
python phase0_auth.py

# 구글 시트 테스트
python google_sheet_recorder.py
```

## 5. 실행
```bash
# 24시간 자동 트레이딩
python main.py
```

## ⚠️ 보안 주의사항
- `.env` 파일은 절대 Git에 Push하지 마세요
- `credentials.json` 파일도 Git에 Push 금지
- API 키는 안전하게 관리하세요
- 실전/모의 모드 설정을 반드시 확인하세요

## 📱 모바일 확인
구글 시트 앱에서 실시간 거래 내역 확인:
https://docs.google.com/spreadsheets/d/161qmtgCq6mDcckqrQj9hyLhGjOTvHtzeJq53Rrry5fo