# 구글 시트 API 설정 가이드

## 1. Google Cloud Console 설정

### 1.1 프로젝트 생성
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. "새 프로젝트" 클릭
3. 프로젝트 이름: "AutoStock-Trading" 입력
4. "만들기" 클릭

### 1.2 API 활성화
1. 왼쪽 메뉴에서 "API 및 서비스" → "라이브러리" 클릭
2. 다음 API들을 검색하여 활성화:
   - Google Sheets API
   - Google Drive API

### 1.3 서비스 계정 생성
1. "API 및 서비스" → "사용자 인증 정보" 클릭
2. "사용자 인증 정보 만들기" → "서비스 계정" 선택
3. 서비스 계정 정보 입력:
   - 서비스 계정 이름: autostock-service
   - 서비스 계정 ID: 자동 생성됨
4. "완료" 클릭

### 1.4 JSON 키 생성
1. 생성된 서비스 계정 클릭
2. "키" 탭 → "키 추가" → "새 키 만들기"
3. "JSON" 선택 → "만들기"
4. 다운로드된 파일을 프로젝트 폴더에 `credentials.json`으로 저장

## 2. 구글 시트 설정

### 2.1 새 시트 생성
1. [Google Sheets](https://sheets.google.com) 접속
2. "새 시트" 생성
3. 시트 이름을 "AutoStock 거래기록 2026"으로 변경

### 2.2 서비스 계정에 권한 부여
1. 시트 우측 상단 "공유" 버튼 클릭
2. `credentials.json`에서 `client_email` 값 복사
   (예: autostock-service@autostock-trading.iam.gserviceaccount.com)
3. 이메일 주소 입력 후 "편집자" 권한 부여
4. "보내기" 클릭

### 2.3 시트 ID 확인
- 시트 URL에서 ID 확인:
  `https://docs.google.com/spreadsheets/d/[시트ID]/edit`
- 이 ID를 코드에서 사용

## 3. 환경 변수 설정

`.env` 파일에 추가:
```
GOOGLE_SHEET_ID=your_sheet_id_here
GOOGLE_CREDENTIALS_FILE=credentials.json
```

## 4. 테스트
1. `python google_sheet_recorder.py` 실행
2. 구글 시트에서 데이터 확인
3. 모바일 구글 시트 앱에서 실시간 확인

## 주의사항
- `credentials.json` 파일은 절대 Git에 커밋하지 마세요
- `.gitignore`에 추가 필수
- 서비스 계정 이메일로 시트 공유 필수