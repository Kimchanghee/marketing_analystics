# 권한 관리 가이드

## 🎯 개요

Creator Control Center는 **역할 기반 권한(RBAC)**과 **구독 티어 기반 기능 제한**을 사용합니다.

---

## 👥 사용자 역할 (User Roles)

### 1. CREATOR (개인 크리에이터) 👤

**접근 가능한 페이지:**
- ✅ `/dashboard` - 개인 대시보드
- ✅ `/channels/manage` - 채널 관리
- ✅ `/profile` - 프로필 관리
- ✅ `/ai-pd` - AI PD (PRO 이상 구독 필요)
- ❌ `/manager/dashboard` - 접근 불가

**특징:**
- 개인 SNS 채널 분석
- 자신의 채널만 관리
- 기업 관리자의 관리를 받을 수 있음

### 2. MANAGER (기업 관리자) 🏢

**접근 가능한 페이지:**
- ✅ `/manager/dashboard` - 기업 대시보드
- ✅ `/manager/inquiries` - 문의 관리
- ✅ `/manager/creator/{id}` - 크리에이터 상세
- ✅ `/manager/export/pdf` - PDF 리포트
- ✅ `/profile` - 프로필 관리
- ✅ `/ai-pd` - AI PD (PRO 이상 구독 필요)
- ❌ `/dashboard` - 접근 불가 (개인 대시보드)

**특징:**
- 여러 크리에이터 통합 관리
- 팀 협업 기능
- 포트폴리오 분석

### 3. SUPER_ADMIN (슈퍼 관리자) ⭐

**접근 가능한 페이지:**
- ✅ **모든 페이지 접근 가능**
- ✅ `/super-admin` - 슈퍼 관리자 콘솔
- ✅ 모든 구독 티어 기능 사용 가능

**특징:**
- 시스템 관리
- 모든 사용자 관리
- 결제 및 구독 관리

---

## 💳 구독 티어 (Subscription Tiers)

### FREE (무료) 🆓

**포함된 기능:**
- ✅ 기본 대시보드
- ✅ 채널 1개 연동
- ✅ 기본 통계 분석
- ✅ 이메일 지원
- ❌ AI 추천
- ❌ AI PD 비서
- ❌ 데이터 내보내기

**제한:**
- 최대 채널: 1개
- AI 기능: 사용 불가
- 고급 분석: 사용 불가

### PRO (프로) 💎

**포함된 기능:**
- ✅ 모든 FREE 기능
- ✅ 채널 5개 연동
- ✅ **AI 추천** 기능
- ✅ **AI PD 비서** 기능
- ✅ **고급 분석** 기능
- ✅ **데이터 내보내기** (CSV, PDF)
- ✅ 우선 지원
- ❌ API 접근
- ❌ 무제한 채널

**제한:**
- 최대 채널: 5개

### ENTERPRISE (기업) 🏢

**포함된 기능:**
- ✅ 모든 PRO 기능
- ✅ **무제한 채널** 연동
- ✅ **API 접근** 권한
- ✅ **팀 협업** 기능
- ✅ **전담 지원**
- ✅ 커스텀 기능 개발
- ✅ 온프레미스 배포 옵션

**제한:**
- 없음

---

## 🛡️ 권한 체크 구현

### 역할 기반 권한 체크

```python
from ..dependencies import require_roles
from ..models import UserRole

# 개인 크리에이터만 접근 가능
@router.get("/dashboard")
def dashboard(user: User = Depends(require_roles(UserRole.CREATOR))):
    ...

# 기업 관리자만 접근 가능
@router.get("/manager/dashboard")
def manager_dashboard(user: User = Depends(require_roles(UserRole.MANAGER))):
    ...

# 여러 역할 허용
@router.get("/some-page")
def some_page(user: User = Depends(require_roles(UserRole.CREATOR, UserRole.MANAGER))):
    ...
```

### 구독 티어 기반 권한 체크

```python
from ..dependencies import check_feature_access, require_subscription_tier
from ..models import SubscriptionTier

# 특정 기능 접근 체크
@router.get("/ai-pd")
def ai_pd_dashboard(
    _feature_access: bool = Depends(check_feature_access("ai_pd"))
):
    ...

# 특정 티어 이상 필요
@router.post("/export/advanced")
def export_advanced(
    subscription: Subscription = Depends(require_subscription_tier(SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE))
):
    ...
```

### 기능별 필요 구독 티어

| 기능 | FREE | PRO | ENTERPRISE |
|------|------|-----|------------|
| 기본 대시보드 | ✅ | ✅ | ✅ |
| AI 추천 | ❌ | ✅ | ✅ |
| AI PD | ❌ | ✅ | ✅ |
| 고급 분석 | ❌ | ✅ | ✅ |
| 데이터 내보내기 | ❌ | ✅ | ✅ |
| API 접근 | ❌ | ❌ | ✅ |
| 무제한 채널 | ❌ | ❌ | ✅ |
| 팀 협업 | ❌ | ❌ | ✅ |

---

## 🔐 로그인 후 리다이렉트

### 역할별 자동 리다이렉트

로그인 성공 후 사용자 역할에 따라 자동으로 적절한 페이지로 이동합니다:

```python
# auth.py - 로그인 처리
if user.role == UserRole.SUPER_ADMIN:
    redirect_to = f"/super-admin?admin_token={settings.super_admin_access_token}"
elif user.role == UserRole.MANAGER:
    redirect_to = "/manager/dashboard"
else:  # CREATOR
    redirect_to = "/dashboard"
```

### 권한 없는 페이지 접근 시

잘못된 페이지에 접근하면 다음과 같은 HTTP 응답을 받습니다:

- **401 Unauthorized**: 로그인하지 않음
- **403 Forbidden**: 권한 없음 (역할 부족)
- **402 Payment Required**: 구독 티어 부족

---

## 📝 회원가입 흐름

### 1. 회원 유형 선택

사용자는 회원가입 시 다음 중 하나를 선택:

- **개인 크리에이터** (CREATOR 역할)
- **기업 관리자** (MANAGER 역할)

### 2. 역할 저장

선택한 유형에 따라 `User.role` 필드에 저장:

```python
# signup.html - 역할 선택
<input type="radio" name="role_type" value="creator" checked>
<input type="radio" name="role_type" value="manager">

# auth.py - 회원가입 처리
user = User(
    email=email,
    role=role,  # CREATOR 또는 MANAGER
    ...
)
```

### 3. 기본 구독 생성

회원가입 시 자동으로 FREE 티어 구독이 생성됩니다:

```python
subscription = Subscription(
    user_id=user.id,
    tier=SubscriptionTier.FREE,
    max_accounts=1,
    active=True
)
```

---

## 🧪 테스트 계정

### 개인 크리에이터 (FREE)

```
이메일: creator@test.com
비밀번호: password123
역할: CREATOR
구독: FREE
```

### 기업 관리자 (ENTERPRISE)

```
이메일: manager@test.com
비밀번호: password123
역할: MANAGER
구독: ENTERPRISE
```

### 슈퍼 관리자

```
이메일: admin@creatorscontrol.com
비밀번호: Ckdgml9788@
역할: SUPER_ADMIN
구독: N/A (모든 기능 접근 가능)
```

---

## 🚀 구독 업그레이드

### 업그레이드 프로세스

1. 사용자가 `/pricing` 또는 대시보드에서 업그레이드 클릭
2. 결제 페이지로 이동
3. 결제 완료 후 `Subscription.tier` 업데이트
4. 즉시 고급 기능 사용 가능

### 관리자가 수동으로 업그레이드

슈퍼 관리자는 사용자의 구독을 수동으로 변경할 수 있습니다:

```
1. /super-admin 접속
2. 사용자 검색
3. 구독 티어 변경
4. 저장
```

---

## 📊 권한 확인 방법

### 템플릿에서 확인

```html
<!-- 역할 확인 -->
{% if user.role == UserRole.CREATOR %}
    개인 크리에이터 전용 콘텐츠
{% elif user.role == UserRole.MANAGER %}
    기업 관리자 전용 콘텐츠
{% endif %}

<!-- 구독 티어 확인 -->
{% if subscription.tier == SubscriptionTier.FREE %}
    <a href="/pricing">업그레이드하여 AI 기능 사용하기</a>
{% elif subscription.tier == SubscriptionTier.PRO %}
    PRO 회원 혜택
{% endif %}
```

### Python 코드에서 확인

```python
# 역할 확인
if user.role == UserRole.CREATOR:
    # 개인 크리에이터 로직
    pass

# 구독 티어 확인
if subscription.tier in [SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE]:
    # AI 기능 실행
    pass
else:
    # 업그레이드 안내
    pass
```

---

## 🐛 트러블슈팅

### 문제 1: 로그인 후 403 Forbidden

**원인**: 역할과 맞지 않는 페이지 접근

**해결**:
1. 로그아웃 후 다시 로그인
2. 올바른 대시보드 URL로 이동
   - CREATOR: `/dashboard`
   - MANAGER: `/manager/dashboard`

### 문제 2: 402 Payment Required

**원인**: 구독 티어 부족

**해결**:
1. `/pricing` 페이지에서 업그레이드
2. 또는 슈퍼 관리자에게 문의

### 문제 3: 회원가입 시 역할 선택이 저장 안됨

**확인 사항**:
1. `signup.html`의 `role_type` 라디오 버튼 확인
2. JavaScript가 `roleInput` hidden field 업데이트하는지 확인
3. 서버 로그에서 `role` 파라미터 확인

---

## 📚 관련 파일

- **권한 정의**: [app/models.py](app/models.py) - `UserRole`, `SubscriptionTier`
- **권한 체크**: [app/dependencies.py](app/dependencies.py) - `require_roles`, `check_feature_access`
- **인증 로직**: [app/routers/auth.py](app/routers/auth.py) - 로그인/회원가입
- **대시보드**: [app/routers/dashboard.py](app/routers/dashboard.py) - 개인 대시보드
- **관리자**: [app/routers/admin.py](app/routers/admin.py) - 기업 대시보드

---

## 🎉 요약

✅ **역할 분리**: CREATOR는 개인 대시보드, MANAGER는 기업 대시보드만 접근
✅ **구독 티어**: FREE는 기본 기능, PRO는 AI 기능, ENTERPRISE는 모든 기능
✅ **자동 리다이렉트**: 로그인 후 역할에 맞는 페이지로 자동 이동
✅ **권한 체크**: 모든 중요 엔드포인트에서 역할 및 구독 확인
✅ **유연한 업그레이드**: 언제든지 구독 티어 변경 가능
