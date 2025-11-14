# Gmail API 설정 가이드

이 프로젝트는 Gmail API를 사용하여 이메일 전송 및 수신 기능을 제공합니다.
SMTP/IMAP 방식보다 더 안정적이고 높은 할당량을 제공합니다.

---

## 📊 Gmail API vs SMTP/IMAP 비교

| 기능 | Gmail API | SMTP/IMAP |
|------|-----------|-----------|
| **할당량** | 10,000+ 메일/일 | 500 메일/일 |
| **인증** | OAuth2 (더 안전) | 앱 비밀번호 |
| **속도** | 빠름 | 느림 |
| **고급 기능** | 라벨, 검색, 필터 | 기본 기능만 |
| **설정 난이도** | 중간 | 쉬움 |

---

## 🚀 빠른 시작 (2가지 방법)

### 방법 1: Service Account (추천 - 서버용)
프로덕션 환경에서 자동화된 이메일 전송에 적합

### 방법 2: OAuth2 User Credentials
개발 환경이나 개인 Gmail 계정 사용 시

---

## 📝 방법 1: Service Account 설정

### 1.1. Google Cloud 프로젝트 생성

```bash
# Google Cloud Console 접속
https://console.cloud.google.com/

# 새 프로젝트 생성
프로젝트 이름: creator-control-center
프로젝트 ID: creator-control-2025 (고유한 ID 사용)
```

### 1.2. Gmail API 활성화

```bash
# API 및 서비스 → 라이브러리
1. "Gmail API" 검색
2. "사용 설정" 클릭
```

### 1.3. Service Account 생성

```bash
# IAM 및 관리자 → 서비스 계정
1. "서비스 계정 만들기" 클릭
2. 서비스 계정 이름: gmail-sender
3. 서비스 계정 설명: Creator Control Center Email Service
4. "만들기 및 계속하기" 클릭
5. 역할 선택: "기본" → "소유자" (개발용) 또는 커스텀 역할
6. "완료" 클릭
```

### 1.4. 서비스 계정 키 생성

```bash
# 생성된 서비스 계정 클릭
1. "키" 탭 → "키 추가" → "새 키 만들기"
2. 키 유형: JSON
3. "만들기" 클릭
4. 다운로드된 JSON 파일을 프로젝트 루트에 저장
   예: credentials/service-account.json
```

### 1.5. Google Workspace Domain-wide Delegation (조직용)

**Google Workspace를 사용하는 경우에만 필요**

```bash
# 1. Service Account에서 Domain-wide Delegation 활성화
IAM 및 관리자 → 서비스 계정 → 해당 계정 선택
"Domain-wide Delegation 사용 설정" 체크
고유 ID 복사 (예: 123456789012345678901)

# 2. Google Workspace Admin Console에서 API 클라이언트 승인
https://admin.google.com/
보안 → API 제어 → DOMAIN 전체 위임 관리
클라이언트 ID: (위에서 복사한 고유 ID)
OAuth 범위:
  https://www.googleapis.com/auth/gmail.send
  https://www.googleapis.com/auth/gmail.readonly
```

### 1.6. 환경 변수 설정

```bash
# .env 파일에 추가

# Gmail API - Service Account 방식
GMAIL_SENDER_EMAIL=your-email@your-domain.com
GOOGLE_SERVICE_ACCOUNT_FILE=./credentials/service-account.json

# Google Workspace Domain-wide Delegation (선택)
GMAIL_DELEGATED_EMAIL=admin@your-domain.com
```

### 1.7. 테스트

```bash
# Python 셸에서 테스트
python -c "
from app.services.gmail_service import get_gmail_service, send_notification_email

# 테스트 이메일 전송
result = send_notification_email(
    to_email='recipient@example.com',
    subject='테스트 이메일',
    message='Gmail API 연동 테스트입니다.',
)
print('전송 성공!' if result else '전송 실패')
"
```

---

## 📝 방법 2: OAuth2 User Credentials (개발용)

### 2.1. OAuth 동의 화면 구성

```bash
# Google Cloud Console → API 및 서비스 → OAuth 동의 화면
1. 사용자 유형: "외부" 선택 (개발용) 또는 "내부" (Google Workspace)
2. "만들기" 클릭

# 앱 정보
앱 이름: Creator Control Center
사용자 지원 이메일: your-email@gmail.com
개발자 연락처: your-email@gmail.com

# 범위 추가
"범위 추가 또는 삭제" 클릭
검색: gmail
선택:
  ✅ https://www.googleapis.com/auth/gmail.send
  ✅ https://www.googleapis.com/auth/gmail.readonly

# 테스트 사용자 추가 (개발 단계)
your-email@gmail.com 추가
```

### 2.2. OAuth 클라이언트 ID 생성

```bash
# API 및 서비스 → 사용자 인증 정보
1. "사용자 인증 정보 만들기" → "OAuth 클라이언트 ID"
2. 애플리케이션 유형: "데스크톱 앱"
3. 이름: Gmail Desktop Client
4. "만들기" 클릭
5. 클라이언트 ID와 클라이언트 보안 비밀번호 저장
```

### 2.3. OAuth2 토큰 생성 스크립트

```python
# scripts/generate_gmail_token.py
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly'
]

def main():
    creds = None

    # 이전에 저장된 토큰 확인
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # 유효한 토큰이 없으면 새로 생성
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # credentials.json은 OAuth 클라이언트 ID JSON 파일
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials/client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # 토큰 저장
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

        # .env에 넣을 JSON 출력
        import json
        creds_dict = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }

        print("\n=== .env에 추가할 내용 ===")
        print(f"GMAIL_CREDENTIALS_JSON='{json.dumps(creds_dict)}'")
        print("\n토큰 생성 완료!")

if __name__ == '__main__':
    main()
```

### 2.4. 토큰 생성 실행

```bash
# 필요한 패키지 설치
pip install google-auth-oauthlib

# OAuth 클라이언트 JSON 저장
# Google Cloud Console에서 다운로드한 JSON 파일을
# credentials/client_secrets.json에 저장

# 스크립트 실행
python scripts/generate_gmail_token.py

# 브라우저가 열리면:
# 1. Google 계정 선택
# 2. "Creator Control Center에서 Gmail 계정에 액세스하려고 합니다" 확인
# 3. "허용" 클릭

# 출력된 GMAIL_CREDENTIALS_JSON 값을 .env에 복사
```

### 2.5. 환경 변수 설정

```bash
# .env 파일에 추가

# Gmail API - OAuth2 방식
GMAIL_SENDER_EMAIL=your-email@gmail.com
GMAIL_CREDENTIALS_JSON='{"token": "ya29...", "refresh_token": "1//...", ...}'
```

---

## 🔧 필수 패키지 설치

```bash
# requirements.txt에 추가
google-api-python-client==2.108.0
google-auth-httplib2==0.2.0
google-auth-oauthlib==1.2.0
```

```bash
# 설치 실행
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

---

## 🧪 테스트 방법

### 단위 테스트

```python
# tests/test_gmail_service.py
import pytest
from app.services.gmail_service import GmailService, send_notification_email

def test_gmail_service_configured():
    """Gmail 서비스 설정 확인"""
    assert GmailService.is_configured() == True

def test_send_email():
    """이메일 전송 테스트"""
    result = send_notification_email(
        to_email="test@example.com",
        subject="Test Email",
        message="This is a test message"
    )
    assert result == True

def test_send_html_email():
    """HTML 이메일 전송 테스트"""
    service = GmailService()
    html_body = "<h1>테스트</h1><p>HTML 이메일입니다.</p>"

    result = service.send_html_email(
        to_email="test@example.com",
        subject="HTML 테스트",
        html_body=html_body
    )

    assert 'id' in result
```

### 수동 테스트

```bash
# Python 인터랙티브 셸
python

>>> from app.services.gmail_service import get_gmail_service
>>> service = get_gmail_service()
>>>
>>> # 간단한 텍스트 이메일
>>> result = service.send_email(
...     to_email="recipient@example.com",
...     subject="테스트 이메일",
...     body="Gmail API 테스트입니다."
... )
>>> print(f"Message ID: {result['id']}")
>>>
>>> # HTML 이메일
>>> html = """
... <html>
... <body>
...     <h1>안녕하세요!</h1>
...     <p>Creator Control Center에서 보낸 이메일입니다.</p>
... </body>
... </html>
... """
>>> service.send_html_email(
...     to_email="recipient@example.com",
...     subject="HTML 테스트",
...     html_body=html
... )
>>>
>>> # 받은 메일 조회
>>> messages = service.list_messages(max_results=5)
>>> for msg in messages:
...     print(f"{msg.subject} - {msg.sender}")
```

---

## 🔒 보안 권장사항

### 1. Service Account 키 보호

```bash
# .gitignore에 추가
credentials/
*.json
token.pickle

# 절대 커밋하지 말 것:
# - service-account.json
# - client_secrets.json
# - token.pickle
```

### 2. 환경 변수 암호화 (프로덕션)

```bash
# Google Cloud Secret Manager 사용
gcloud secrets create gmail-service-account \
  --data-file=credentials/service-account.json

# Cloud Run에서 사용
gcloud run services update creator-control-center \
  --update-secrets=GOOGLE_SERVICE_ACCOUNT_FILE=/secrets/gmail-service-account:latest
```

### 3. 최소 권한 원칙

```bash
# Service Account에 필요한 최소 권한만 부여
- gmail.send (이메일 전송)
- gmail.readonly (수신함 읽기)

# 불필요한 권한 제거:
- gmail.modify
- gmail.compose
```

---

## 🐛 문제 해결

### 1. "API has not been used in project" 오류

```bash
해결:
1. Google Cloud Console → API 및 서비스 → 라이브러리
2. "Gmail API" 검색
3. "사용 설정" 클릭
4. 5-10분 대기 후 재시도
```

### 2. "insufficient authentication scopes" 오류

```bash
해결:
1. OAuth2 방식: token.pickle 삭제 후 재생성
2. Service Account: Domain-wide Delegation 설정 확인
3. 필요한 범위:
   - https://www.googleapis.com/auth/gmail.send
   - https://www.googleapis.com/auth/gmail.readonly
```

### 3. "Quota exceeded" 오류

```bash
확인:
1. Google Cloud Console → API 및 서비스 → 할당량
2. Gmail API 할당량 확인
   - 기본: 10,000 메일/일
   - 초당 요청: 100/초

해결:
- 할당량 증가 요청
- 대량 전송 시 배치 처리 사용
```

### 4. Fallback to SMTP/IMAP

```bash
Gmail API 실패 시 자동으로 SMTP/IMAP으로 전환:

# .env에 추가 (백업용)
SUPER_ADMIN_EMAIL=your-email@gmail.com
SUPER_ADMIN_EMAIL_PASSWORD=your-app-password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

---

## 📊 모니터링

### Gmail API 사용량 확인

```bash
# Google Cloud Console
API 및 서비스 → 대시보드 → Gmail API

확인 항목:
- 일일 요청 수
- 오류율
- 응답 시간
```

### 로그 확인

```python
# app/services/gmail_service.py는 자동으로 로깅
import logging
logger = logging.getLogger('app.services.gmail_service')

# 로그 레벨 설정
logger.setLevel(logging.INFO)
```

---

## 🎯 다음 단계

1. ✅ Gmail API 설정 완료
2. ✅ 이메일 전송 테스트
3. ⬜ HTML 템플릿 작성
4. ⬜ 자동화된 이메일 워크플로우 구축
5. ⬜ 프로덕션 배포

---

## 📚 참고 자료

- [Gmail API 공식 문서](https://developers.google.com/gmail/api/guides)
- [Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)
- [Service Account 가이드](https://cloud.google.com/iam/docs/service-accounts)
- [OAuth2 가이드](https://developers.google.com/identity/protocols/oauth2)

---

## 💬 지원

문제가 발생하면:
1. 로그 확인: `tail -f logs/gmail_service.log`
2. 이슈 생성: GitHub Issues
3. 문서 확인: 위 참고 자료 링크
