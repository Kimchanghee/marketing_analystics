# 🎨 UI 파일 리팩토링 계획

## 📊 현재 상태 (16개 파일)

### 기본
1. `base.html` - 기본 레이아웃

### 공개 페이지
2. `landing.html` - 랜딩 페이지
3. `services.html` - 서비스 소개
4. `personal.html` - 개인 요금제
5. `business.html` - 기업 요금제
6. `support.html` - 지원

### 인증
7. `login.html` - 로그인
8. `signup.html` - 회원가입
9. `recovery.html` - 비밀번호 복구

### 대시보드
10. `dashboard.html` - 개인 대시보드
11. `manager_dashboard.html` - 기업 대시보드
12. `super_admin.html` - 슈퍼 관리자
13. `channels_manage.html` - 채널 관리
14. `profile.html` - 프로필

### 관리 도구
15. `creator_detail.html` - 크리에이터 상세
16. `manager_inquiries.html` - 문의 관리

---

## 🎯 리팩토링 후 (10개 파일)

### 1. `base.html` ✅ 유지
- 기본 레이아웃 (헤더, 푸터, 네비게이션)

### 2. `landing.html` ✅ 유지
- 메인 홈 페이지

### 3. `auth.html` 🆕 통합
- **통합:** `login.html` + `signup.html` + `recovery.html`
- **방식:** 동적 모드 전환 (`?mode=login|signup|recovery`)
- **장점:** 인증 관련 로직 중앙화

### 4. `dashboard.html` ✅ 유지
- 개인 크리에이터 대시보드 (AI PD 통합)

### 5. `manager_dashboard.html` ✅ 유지
- 기업 관리자 대시보드 (AI PD 통합)

### 6. `super_admin.html` ✅ 유지
- 슈퍼 관리자 콘솔

### 7. `channels.html` 🔄 이름 변경
- **이전:** `channels_manage.html`
- 채널 관리 페이지

### 8. `profile.html` ✅ 유지
- 프로필 설정

### 9. `pricing.html` 🆕 통합
- **통합:** `personal.html` + `business.html`
- **방식:** 탭 전환 또는 동적 모드
- **장점:** 요금제 비교 용이

### 10. `info.html` 🆕 통합
- **통합:** `services.html` + `support.html` + `creator_detail.html` + `manager_inquiries.html`
- **방식:** 동적 섹션 로드
- **장점:** 정보성 페이지 통합 관리

---

## 🔧 구현 방법

### 동적 템플릿 로딩
\`\`\`python
# 예시: auth.html
@router.get("/auth")
def auth_page(mode: str = "login"):
    # mode: login, signup, recovery
    return templates.TemplateResponse("auth.html", {
        "mode": mode,
        ...
    })
\`\`\`

### 조건부 렌더링
\`\`\`html
<!-- auth.html -->
{% if mode == 'login' %}
    <!-- 로그인 폼 -->
{% elif mode == 'signup' %}
    <!-- 회원가입 폼 -->
{% elif mode == 'recovery' %}
    <!-- 비밀번호 복구 폼 -->
{% endif %}
\`\`\`

---

## 📈 이점

1. **유지보수 용이:** 관련 기능이 한 파일에
2. **코드 중복 감소:** 공통 레이아웃 재사용
3. **일관성 향상:** 유사 페이지 스타일 통일
4. **파일 수 감소:** 16개 → 10개 (37.5% 감소)

---

## ⚠️ 주의사항

1. **라우팅 업데이트 필요**
   - `app/routers/auth.py` 수정
   - `app/routers/dashboard.py` 수정
   - `app/main.py` 수정

2. **기존 URL 호환성**
   - 리다이렉트 추가 필요
   - `/login` → `/auth?mode=login`
   - `/signup` → `/auth?mode=signup`

3. **테스트 필요**
   - 모든 페이지 렌더링 확인
   - 폼 제출 동작 확인
   - SEO 영향 확인

---

## 🚀 마이그레이션 단계

1. ✅ 계획 수립
2. ⏳ `auth.html` 통합
3. ⏳ `pricing.html` 통합
4. ⏳ `info.html` 통합
5. ⏳ 라우터 업데이트
6. ⏳ 리다이렉트 추가
7. ⏳ 테스트
8. ⏳ 배포
