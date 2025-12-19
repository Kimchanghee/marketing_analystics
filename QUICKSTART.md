# 🚀 Quick Start Guide

## 5분 안에 로컬 환경에서 실행하기

### Prerequisites
- Python 3.9+
- Node.js 18+ (Next.js를 사용할 경우)
- Git

---

## Step 1: 저장소 클론 (30초)

```bash
git clone <your-repo-url>
cd marketing_analystics
```

---

## Step 2: 보안 설정 (2분) ⚠️ 필수!

### 2.1 환경 변수 파일 생성
```bash
cp .env.example .env
```

### 2.2 보안 키 생성
```bash
# SECRET_KEY 생성
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# SUPER_ADMIN_ACCESS_TOKEN 생성
python -c "import secrets; print('SUPER_ADMIN_ACCESS_TOKEN=' + secrets.token_urlsafe(32))"
```

### 2.3 .env 파일 편집
위에서 생성된 키를 복사하여 `.env` 파일에 붙여넣기:
```bash
SECRET_KEY=<생성된_키>
SUPER_ADMIN_ACCESS_TOKEN=<생성된_토큰>
```

---

## Step 3: Python 백엔드 설정 (1분)

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 의존성 설치
pip install fastapi uvicorn sqlmodel pydantic-settings python-multipart
```

---

## Step 4: 데이터베이스 초기화 (30초)

```bash
# FastAPI 서버를 한 번 실행하면 자동으로 DB 생성됨
uvicorn app.main:app --reload
```

서버가 시작되면 `Ctrl+C`로 중단

---

## Step 5: 서버 실행 (10초)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ 브라우저에서 열기: http://localhost:8000

---

## 🎨 Next.js 프론트엔드 (선택사항)

Next.js를 사용하려면:

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

✅ 브라우저에서 열기: http://localhost:3000

⚠️ **주의:** Next.js 페이지가 아직 완성되지 않았습니다. 완전한 기능을 보려면 FastAPI (8000 포트)를 사용하세요.

---

## 📍 주요 엔드포인트

### FastAPI + Jinja (완전 구현됨)
- **랜딩:** http://localhost:8000/
- **로그인:** http://localhost:8000/login
- **회원가입:** http://localhost:8000/signup
- **대시보드:** http://localhost:8000/dashboard
- **서비스:** http://localhost:8000/services
- **API 문서:** http://localhost:8000/docs

### Next.js (부분 구현)
- **랜딩:** http://localhost:3000/
- ⚠️ 나머지 페이지 미구현 (404 에러)

---

## 🧪 테스트 계정 생성

```bash
# 회원가입 페이지에서 수동으로 생성하거나
# API를 통해 생성:

curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "name": "Test User"
  }'
```

---

## 🔧 자주 발생하는 문제

### 1. "SECRET_KEY not found" 에러
✅ **정상입니다!** `.env` 파일을 생성하고 보안 키를 입력하세요.
👉 [IMMEDIATE_ACTIONS.md](IMMEDIATE_ACTIONS.md) 참고

### 2. "No module named 'fastapi'" 에러
```bash
pip install fastapi uvicorn sqlmodel
```

### 3. "Port 8000 already in use" 에러
```bash
# 다른 포트 사용
uvicorn app.main:app --reload --port 8080
```

### 4. 데이터베이스 에러
```bash
# DB 파일 삭제 후 재생성
rm app/app.db
uvicorn app.main:app --reload
```

### 5. Next.js 페이지 404 에러
✅ **예상된 동작입니다.** FastAPI 버전을 사용하세요.
👉 [DEPLOYMENT_DECISION.md](DEPLOYMENT_DECISION.md) 참고

---

## 📦 전체 의존성 설치

### Python
```bash
pip install -r requirements.txt
```

requirements.txt가 없다면 주요 패키지 설치:
```bash
pip install \
  fastapi \
  uvicorn[standard] \
  sqlmodel \
  pydantic-settings \
  python-multipart \
  python-jose[cryptography] \
  passlib[bcrypt] \
  jinja2 \
  aiofiles
```

### Node.js
```bash
npm install
```

---

## 🗂️ 프로젝트 구조

```
marketing_analystics/
├── app/                    # FastAPI 백엔드
│   ├── main.py            # 메인 애플리케이션
│   ├── config.py          # 설정 (⚠️ 보안 키 제거 필요)
│   ├── models.py          # 데이터베이스 모델
│   ├── routers/           # API 라우트
│   ├── services/          # 비즈니스 로직
│   └── middleware/        # 미들웨어
│
├── ui/templates/          # Jinja 템플릿 (완성됨)
│   ├── base.html
│   ├── landing.html
│   ├── login.html
│   └── ...
│
├── app/ (Next.js)         # Next.js 프론트엔드 (미완성)
│   ├── page.tsx           # 랜딩 페이지만 존재
│   └── layout.tsx
│
├── lib/                   # 공유 라이브러리
│   └── translations.ts    # 다국어 번역
│
├── .env.example           # 환경 변수 템플릿
├── .gitignore             # Git 무시 파일
└── package.json           # Node 의존성
```

---

## 🎯 다음 단계

1. ✅ 로컬에서 실행 확인
2. 📖 [DEPLOYMENT_DECISION.md](DEPLOYMENT_DECISION.md) - 프론트엔드 스택 선택
3. 🔒 [IMMEDIATE_ACTIONS.md](IMMEDIATE_ACTIONS.md) - 보안 설정 완료
4. 🚨 [SECURITY_ISSUES.md](SECURITY_ISSUES.md) - 보안 이슈 해결
5. 📋 [README_FIXES.md](README_FIXES.md) - 전체 수정 사항 확인

---

## 🆘 도움말

### 공식 문서
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/docs)
- [SQLModel](https://sqlmodel.tiangolo.com/)

### 프로젝트 문서
- **즉시 조치:** [IMMEDIATE_ACTIONS.md](IMMEDIATE_ACTIONS.md)
- **보안 가이드:** [SECURITY_ISSUES.md](SECURITY_ISSUES.md)
- **배포 결정:** [DEPLOYMENT_DECISION.md](DEPLOYMENT_DECISION.md)
- **수정 내역:** [README_FIXES.md](README_FIXES.md)

---

**예상 소요 시간:** 5분
**난이도:** ⭐⭐☆☆☆

첫 실행 시 문제가 생기면 위의 "자주 발생하는 문제" 섹션을 확인하세요!
