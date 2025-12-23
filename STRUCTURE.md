# 프로젝트 구조 가이드

이 문서는 Marketing Analytics 프로젝트의 모듈화된 파일 구조를 설명합니다.

## 디렉토리 구조 개요

```
marketing_analystics/
├── app/                          # 백엔드 애플리케이션
│   ├── main.py                   # FastAPI 앱 진입점
│   ├── config.py                 # 환경설정
│   ├── database.py               # DB 연결
│   ├── models.py                 # ORM 모델
│   ├── dependencies.py           # 의존성 주입
│   ├── auth.py                   # 인증 유틸리티
│   │
│   ├── routers/                  # API 라우터
│   │   ├── auth/                 # 인증 관련 (분리됨)
│   │   │   ├── __init__.py       # 라우터 통합
│   │   │   ├── helpers.py        # 공통 헬퍼
│   │   │   ├── login.py          # 로그인/로그아웃
│   │   │   ├── signup.py         # 회원가입
│   │   │   ├── oauth.py          # 소셜 로그인
│   │   │   ├── recovery.py       # 계정 복구
│   │   │   └── credentials.py    # 비밀번호 설정
│   │   │
│   │   ├── admin/                # 관리자 관련 (분리됨)
│   │   │   ├── __init__.py       # 라우터 통합
│   │   │   ├── helpers.py        # 공통 헬퍼
│   │   │   ├── super_admin.py    # 슈퍼관리자 대시보드
│   │   │   ├── email.py          # 이메일 관리
│   │   │   ├── users.py          # 사용자 관리
│   │   │   ├── payments.py       # 결제 관리
│   │   │   ├── inquiries.py      # 문의 관리
│   │   │   └── ai_settings.py    # AI 설정
│   │   │
│   │   ├── auth.py               # [레거시] 기존 인증 라우터
│   │   ├── admin.py              # [레거시] 기존 관리자 라우터
│   │   ├── dashboard.py          # 대시보드
│   │   ├── channels.py           # 채널 관리
│   │   ├── ai_pd.py              # AI PD 기능
│   │   └── subscriptions.py      # 구독 관리
│   │
│   ├── services/                 # 비즈니스 로직
│   │   ├── __init__.py           # 서비스 통합
│   │   │
│   │   ├── email/                # 이메일 서비스 (분리됨)
│   │   │   ├── __init__.py
│   │   │   ├── gmail_service.py
│   │   │   ├── resend_email.py
│   │   │   ├── super_admin_email.py
│   │   │   └── email_verification.py
│   │   │
│   │   ├── ai/                   # AI 서비스 (분리됨)
│   │   │   ├── __init__.py
│   │   │   ├── gemini_ai.py
│   │   │   ├── ai_pd_service.py
│   │   │   └── ai_recommendations.py
│   │   │
│   │   ├── social/               # 소셜 서비스 (분리됨)
│   │   │   ├── __init__.py
│   │   │   ├── social_auth.py
│   │   │   ├── social_oauth.py
│   │   │   ├── social_fetcher.py
│   │   │   └── channel_connectors.py
│   │   │
│   │   ├── account_recovery.py   # 계정 복구
│   │   ├── login_throttle.py     # 로그인 제한
│   │   ├── localization.py       # 다국어
│   │   ├── crypto.py             # 암호화
│   │   ├── pdf_generator.py      # PDF 생성
│   │   └── config_status.py      # 설정 상태
│   │
│   ├── middleware/               # 미들웨어
│   │   ├── security.py           # 보안 미들웨어
│   │   └── security_headers.py   # HTTP 보안 헤더
│   │
│   ├── seo/                      # SEO/AEO/GEO
│   │   ├── seo_service.py
│   │   ├── sitemap_generator.py
│   │   └── locales/
│   │
│   └── locales/                  # 다국어 리소스
│       ├── ko.json
│       ├── en.json
│       └── ja.json
│
├── ui/                           # 프론트엔드
│   ├── templates/                # Jinja2 템플릿
│   │   ├── layouts/              # 레이아웃
│   │   │   ├── base.html
│   │   │   ├── auth_layout.html
│   │   │   └── dashboard_layout.html
│   │   │
│   │   ├── components/           # 재사용 컴포넌트
│   │   │   ├── _alert_messages.html
│   │   │   ├── _auth_social_buttons.html
│   │   │   └── _pricing_card.html
│   │   │
│   │   ├── auth/                 # 인증 페이지 (분리됨)
│   │   │   ├── login.html
│   │   │   ├── signup.html
│   │   │   ├── recovery.html
│   │   │   └── profile.html
│   │   │
│   │   ├── admin/                # 관리자 페이지 (분리됨)
│   │   │   ├── super_admin.html
│   │   │   ├── manager_dashboard.html
│   │   │   ├── manager_inquiries.html
│   │   │   └── creator_detail.html
│   │   │
│   │   ├── dashboard/            # 대시보드 페이지 (분리됨)
│   │   │   └── channels_manage.html
│   │   │
│   │   ├── public/               # 공개 페이지 (분리됨)
│   │   │   ├── landing.html
│   │   │   ├── business.html
│   │   │   ├── personal.html
│   │   │   ├── services.html
│   │   │   ├── support.html
│   │   │   └── contact.html
│   │   │
│   │   ├── legal/                # 법적 문서 (분리됨)
│   │   │   ├── terms.html
│   │   │   └── privacy.html
│   │   │
│   │   └── errors/               # 에러 페이지 (분리됨)
│   │       ├── 404.html
│   │       └── 500.html
│   │
│   └── static/                   # 정적 파일
│       ├── css/
│       ├── js/
│       └── img/
```

## 모듈별 책임

### 라우터 (app/routers/)

| 모듈 | 책임 | 주요 엔드포인트 |
|------|------|----------------|
| `auth/login` | 로그인/로그아웃 | `/login`, `/logout` |
| `auth/signup` | 회원가입 | `/signup`, `/signup/request-code` |
| `auth/oauth` | 소셜 로그인 | `/oauth/{provider}`, `/oauth/{provider}/callback` |
| `auth/recovery` | 계정 복구 | `/recover`, `/recover/password` |
| `auth/credentials` | 비밀번호 관리 | `/credentials/set-password` |
| `admin/super_admin` | 슈퍼관리자 | `/super-admin` |
| `admin/email` | 이메일 관리 | `/super-admin/email/send` |
| `admin/users` | 사용자 관리 | `/super-admin/promote`, `/super-admin/status` |
| `admin/payments` | 결제 관리 | `/super-admin/payment/create` |
| `admin/inquiries` | 문의 관리 | `/manager/inquiries` |
| `admin/ai_settings` | AI 설정 | `/super-admin/ai/system-prompt` |

### 서비스 (app/services/)

| 모듈 | 책임 |
|------|------|
| `email/` | Gmail, Resend, 이메일 인증 |
| `ai/` | Gemini AI, 추천, AI PD |
| `social/` | OAuth, 채널 연동, 데이터 수집 |
| `account_recovery` | 비밀번호 재설정 |
| `login_throttle` | 로그인 시도 제한 |
| `localization` | 다국어 지원 |
| `pdf_generator` | PDF 리포트 생성 |

### 템플릿 (ui/templates/)

| 폴더 | 용도 |
|------|------|
| `layouts/` | 기본 레이아웃 (base, auth, dashboard) |
| `components/` | 재사용 가능한 UI 컴포넌트 |
| `auth/` | 인증 관련 페이지 |
| `admin/` | 관리자 페이지 |
| `dashboard/` | 대시보드 페이지 |
| `public/` | 공개 페이지 (랜딩, 서비스 등) |
| `legal/` | 이용약관, 개인정보처리방침 |
| `errors/` | 404, 500 에러 페이지 |

## 마이그레이션 가이드

### 기존 import 변경

기존 코드에서 import를 새 구조로 변경하는 방법:

```python
# 이전
from app.routers.auth import router as auth_router

# 이후 (새 모듈 구조)
from app.routers.auth import router as auth_router  # 동일 - __init__.py에서 통합됨

# 또는 개별 모듈 import
from app.routers.auth.login import router as login_router
from app.routers.auth.oauth import router as oauth_router
```

```python
# 이전
from app.services.gmail_service import GmailService

# 이후
from app.services.email import GmailService
# 또는
from app.services.email.gmail_service import GmailService
```

### 템플릿 경로 변경

라우터에서 템플릿 렌더링 시 새 경로 사용:

```python
# 이전
return templates.TemplateResponse("login.html", context)

# 이후
return templates.TemplateResponse("auth/login.html", context)
```

### 레거시 파일 유지

기존 `auth.py`, `admin.py` 파일은 하위 호환성을 위해 유지됩니다.
점진적으로 새 모듈 구조로 마이그레이션하세요.

## 명명 규칙

- **라우터**: `{기능}.py` (예: `login.py`, `signup.py`)
- **서비스**: `{기능}_service.py` 또는 `{기능}.py`
- **헬퍼**: `helpers.py` (각 모듈 폴더에)
- **템플릿**: `{페이지명}.html` (폴더로 그룹화)

## 확장 가이드

새 기능을 추가할 때:

1. 적절한 서비스 폴더에 비즈니스 로직 작성
2. 해당 라우터 폴더에 API 엔드포인트 추가
3. `__init__.py`에서 새 라우터 포함
4. 필요시 새 템플릿 폴더/파일 생성
