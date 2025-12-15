# 🎨 디자인 시스템 가이드

## 📋 개요

v0.dev로 제작한 모던 디자인 시스템을 FastAPI 프로젝트에 적용했습니다.

---

## 🎨 색상 시스템

### 라이트 모드
\`\`\`css
--bg-page: #fff5f2;                    /* 페이지 배경 */
--surface-primary: #ffffff;            /* 카드 배경 */
--surface-elevated: #ffecef;           /* 강조 영역 */
--text-primary: #14203b;               /* 주 텍스트 */
--text-secondary: #3b3762;             /* 보조 텍스트 */
--accent: #e63946;                     /* 강조 색상 (Instagram 핑크) */
--accent-soft: #5a8bf5;                /* 부드러운 강조 (Facebook 블루) */
--success: #1bb978;                    /* 성공 */
--danger: #ef4444;                     /* 위험 (YouTube 레드) */
\`\`\`

### 다크 모드
\`\`\`css
--bg-page: #0f172a;                    /* 페이지 배경 */
--surface-primary: rgba(17, 24, 39, 0.95);  /* 카드 배경 */
--surface-elevated: rgba(30, 41, 59, 0.88); /* 강조 영역 */
--text-primary: #f8f9ff;               /* 주 텍스트 */
--text-secondary: #d8c8ff;             /* 보조 텍스트 */
--accent: #ff7a18;                     /* 강조 색상 (Instagram 오렌지) */
--accent-soft: #6d28d9;                /* 부드러운 강조 (보라) */
\`\`\`

### SNS 브랜드 색상
\`\`\`css
--accent-instagram-orange: #ff7a18;
--accent-instagram-pink: #e63946;
--accent-instagram-purple: #6d28d9;
--accent-facebook: #2563eb;
--accent-youtube: #ef4444;
\`\`\`

---

## 📐 레이아웃

### Radius (둥근 모서리)
\`\`\`css
--radius-sm: 0.75rem;   /* 12px */
--radius-md: 1rem;      /* 16px */
--radius-lg: 1.5rem;    /* 24px */
\`\`\`

### 그림자
\`\`\`css
--shadow-soft: 0 16px 40px rgba(230, 57, 70, 0.18);
--shadow-strong: 0 40px 80px rgba(239, 68, 68, 0.22);
--card-shadow: 0 26px 52px rgba(221, 42, 123, 0.16);
\`\`\`

### 전환 효과
\`\`\`css
--transition-base: 0.3s ease;
\`\`\`

---

## 🔘 버튼 스타일

### Primary 버튼
\`\`\`html
<a class="btn primary" href="/signup">시작하기</a>
\`\`\`
- 배경: `#ff4d6d` (밝은 핑크)
- 그림자: 강조 효과
- 호버: 위로 -2px 이동

### Secondary 버튼
\`\`\`html
<a class="btn secondary" href="/business">기업 상담</a>
\`\`\`
- 배경: 투명 + 테두리
- 호버: 배경 살짝 채워짐

### Tertiary 버튼
\`\`\`html
<a class="btn tertiary" href="/services">자세히 보기</a>
\`\`\`
- 배경: 투명
- 테두리: 기본 테두리 색상

---

## 📦 컴포넌트 사용법

### 알림 메시지
\`\`\`html
{% include 'components/_alert_messages.html' %}
\`\`\`

### 소셜 로그인 버튼
\`\`\`html
{% include 'components/_auth_social_buttons.html' with auth_mode='login' %}
\`\`\`

### 요금제 카드
\`\`\`html
{% include 'components/_pricing_card.html' with plan='pro' %}
\`\`\`

---

## 🏗️ 섹션 스타일

### Hero 섹션
\`\`\`html
<section class="hero-section">
    <div class="hero-wrapper">
        <div class="hero-content">
            <h1 class="hero-title">제목</h1>
            <p class="hero-subtitle">부제목</p>
            <div class="hero-cta-group">
                <a class="btn primary">CTA</a>
            </div>
        </div>
        <div class="hero-visual">
            <!-- 이미지 또는 대시보드 미리보기 -->
        </div>
    </div>
</section>
\`\`\`

### 메트릭 섹션
\`\`\`html
<section class="metrics-section">
    <div class="metrics-grid">
        <div class="metric-stat">
            <div class="stat-icon">🎯</div>
            <div class="stat-content">
                <span class="stat-value">35%</span>
                <span class="stat-label">성장률</span>
                <p class="stat-description">설명</p>
            </div>
        </div>
    </div>
</section>
\`\`\`

### 기능 섹션
\`\`\`html
<section class="features-section">
    <div class="section-header">
        <h2>주요 기능</h2>
        <p>설명</p>
    </div>
    <div class="features-grid">
        <article class="feature-card">
            <div class="feature-icon">✨</div>
            <div class="feature-body">
                <h3>기능 제목</h3>
                <p>기능 설명</p>
            </div>
        </article>
    </div>
</section>
\`\`\`

---

## 📱 반응형 디자인

### 브레이크포인트
- **모바일**: < 768px
- **태블릿**: 768px - 1024px
- **데스크톱**: > 1024px

### 자동 적용
- Grid 레이아웃: `repeat(auto-fit, minmax(300px, 1fr))`
- Hero: 2컬럼 → 1컬럼
- CTA 버튼: flex → column

---

## 🎯 사용 예시

### 새 페이지 만들기
\`\`\`html
{% extends "layouts/base.html" %}
{% block content %}
<section class="hero-section">
    <!-- Hero 내용 -->
</section>

<section class="features-section">
    <!-- 기능 소개 -->
</section>
{% endblock %}
\`\`\`

### 인증 페이지
\`\`\`html
{% extends "layouts/auth_layout.html" %}
{% block auth_content %}
    {% include 'components/_alert_messages.html' %}
    {% include 'components/_auth_social_buttons.html' with auth_mode='login' %}
    
    <form method="post">
        <!-- 폼 내용 -->
    </form>
{% endblock %}
\`\`\`

### 대시보드 페이지
\`\`\`html
{% extends "layouts/dashboard_layout.html" %}
{% block dashboard_content %}
    <div class="dashboard-card">
        <!-- 대시보드 내용 -->
    </div>
{% endblock %}
\`\`\`

---

## 🚀 적용 완료된 디자인

### ✅ 적용된 페이지:
- 랜딩 페이지 (v0 디자인)
- 모든 페이지에 style-modern.css 적용

### ⏳ 향후 적용 예정:
- 대시보드 페이지 UI 개선
- 요금제 페이지 리디자인
- 로그인/회원가입 페이지 모던화

---

## 📚 참고 자료

### v0 원본 저장소
https://github.com/Kimchanghee/v0-saa-s-landing-page

### 디자인 파일
- CSS: `ui/static/css/style-modern.css`
- 컴포넌트: `ui/components/`
- 레이아웃: `ui/layouts/`

---

**마지막 업데이트**: 2025-11-06  
**디자인 시스템 버전**: v2.0 (v0 기반)
