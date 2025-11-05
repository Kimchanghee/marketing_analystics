# 🎯 Creator Control Center - 계정 및 페이지 정리

## 📋 등록된 테스트 계정

### 1️⃣ 개인 크리에이터 (Creator)
```
이메일: creator@test.com
비밀번호: password123
역할: CREATOR
구독: FREE (최대 1개 채널)
```

**접속 방법:**
1. 로그인: `https://marketing-analystics-573434207823.europe-west1.run.app/login`
2. 로그인 후 자동 리다이렉트: `/dashboard`

---

### 2️⃣ 기업 관리자 (Manager)
```
이메일: manager@test.com
비밀번호: password123
역할: MANAGER
구독: ENTERPRISE (최대 20개 채널)
```

**접속 방법:**
1. 로그인: `https://marketing-analystics-573434207823.europe-west1.run.app/login`
2. 로그인 후: `/manager/dashboard`

---

### 3️⃣ 슈퍼 관리자 (Super Admin)
```
이메일: admin@test.com
비밀번호: password123
역할: SUPER_ADMIN
```

**접속 방법:**
1. 로그인: `https://marketing-analystics-573434207823.europe-west1.run.app/login`
2. 로그인 후 자동 리다이렉트: `/dashboard` (모든 페이지 접근 가능 ✅)
3. 슈퍼 관리자 페이지: `/super-admin?admin_token=YOUR_SUPER_ADMIN_TOKEN`
   - ⚠️ `SUPER_ADMIN_ACCESS_TOKEN` 환경 변수 필요
   - 직접 URL로 접속해야 함

---

### 4️⃣ 마스터 관리자 (모든 페이지 접근 가능)
```
이메일: kckc93@creatorscontrol.com
비밀번호: Ckdgml9788@
역할: SUPER_ADMIN
```

**접속 방법:**
1. 로그인: `https://marketing-analystics-573434207823.europe-west1.run.app/login`
2. 로그인 후 자동 리다이렉트: `/dashboard`
3. **모든 대시보드 자유롭게 접근 가능** (SUPER_ADMIN 권한)
   - 개인 대시보드: `/dashboard` ✅
   - 기업 대시보드: `/manager/dashboard` ✅
   - AI PD 대시보드: `/ai-pd` ✅
   - 슈퍼 관리자: `/super-admin?admin_token=YOUR_TOKEN` ✅ (수동 접속)

---

## 🌐 웹사이트 페이지 구조

### 🏠 공개 페이지 (로그인 불필요)
| URL | 설명 |
|-----|------|
| `/` | 랜딩 페이지 (홈) |
| `/services` | 서비스 소개 |
| `/personal` | 개인 요금제 안내 |
| `/business` | 기업 요금제 안내 |
| `/support` | 고객 지원 |
| `/login` | 로그인 페이지 |
| `/signup` | 회원가입 페이지 |
| `/sitemap.xml` | 사이트맵 |
| `/robots.txt` | 로봇 파일 |

---

### 👤 개인 크리에이터 대시보드 (CREATOR 권한)
**기본 URL:** `/dashboard`

#### 주요 기능:
- ✅ **채널 관리**: YouTube, Instagram, TikTok, Facebook, Threads 연결
- 📊 **성과 분석**: 구독자, 성장률, 참여율, 최근 게시물
- 📈 **차트 시각화**:
  - 활동 타임라인
  - 참여율 추세
  - 플랫폼별 비교
  - 게시물 성과 분석
- 🤖 **AI PD 비서**: 채널 성과 분석 및 개선 방안 제안
- 📥 **데이터 내보내기**:
  - CSV: `/dashboard/export/csv`
  - JSON: `/dashboard/export/json`
  - PDF: `/dashboard/export/pdf`

#### 채널 인증 관리:
- API Token 방식
- OAuth2 방식
- User/Password 방식

#### 🤖 AI PD 비서 (PRO 이상):
- **유료 기능**: PRO 또는 ENTERPRISE 구독 필요
- **위치**: 개인 대시보드 하단에 통합
- **기능**: 채널 성과 분석, 성장 전략 제안, 실시간 AI 상담

**AI 질문 예시:**
- "어떤 플랫폼에 더 집중해야 할까요?"
- "최근 게시물 반응이 좋은 이유는?"
- "구독자를 늘리는 방법을 알려주세요"
- "참여율을 개선하려면?"

**FREE 사용자**: 업그레이드 안내 메시지 표시

---

### 🏢 기업 관리자 대시보드 (MANAGER 권한)
**기본 URL:** `/manager/dashboard`

#### 주요 기능:
- 👥 **크리에이터 관리**:
  - 승인된 크리에이터 목록
  - 승인 대기 큐
  - 크리에이터별 상세 정보
- 📊 **통합 성과 분석**:
  - 전체 관리 채널 통계
  - 플랫폼별 성과
  - 크리에이터별 성과
- 🤖 **Gemini API 설정**:
  - AI 답변 초안 생성용
  - 암호화된 API 키 저장
- 💬 **문의 관리**: `/manager/inquiries`
  - AI 답변 초안 생성
  - 문의 상태 관리
  - 최종 답변 전송
- 📥 **리포트 내보내기**:
  - 통합 PDF: `/manager/export/pdf`
  - 크리에이터별 CSV: `/manager/creator/{id}/export/csv`
  - 크리에이터별 PDF: `/manager/creator/{id}/export/pdf`

#### 크리에이터 관리:
| 엔드포인트 | 설명 |
|-----------|------|
| `/manager/approve` | 크리에이터 승인/거절 |
| `/manager/invite` | 크리에이터 초대 링크 생성 |
| `/manager/creator/{id}` | 크리에이터 상세 정보 |

#### 🤖 AI PD 비서 - 포트폴리오 분석 (PRO 이상):
- **유료 기능**: PRO 또는 ENTERPRISE 구독 필요
- **위치**: 기업 대시보드 하단에 통합
- **기능**: 포트폴리오 분석, 크리에이터별 성과 비교, 전략적 인사이트

**AI 질문 예시:**
- "어떤 크리에이터가 가장 좋은 성과를 내고 있나요?"
- "전체 포트폴리오의 강점과 약점은?"
- "크리에이터별 맞춤 전략을 제안해주세요"
- "다음 분기 액션 아이템은?"

**FREE 사용자**: 업그레이드 안내 메시지 표시

---

### 🔐 슈퍼 관리자 대시보드 (SUPER_ADMIN 권한)
**기본 URL:** `/super-admin?admin_token=YOUR_TOKEN`

⚠️ **중요**: `SUPER_ADMIN_ACCESS_TOKEN` 환경 변수 필요

#### 주요 기능:
- 👥 **전체 회원 관리**:
  - 회원 목록 (기업/개인 구분)
  - 회원 상태 관리 (활성/비활성)
  - 역할 변경 (CREATOR, MANAGER, ADMIN, SUPER_ADMIN)
- 💳 **구독 관리**:
  - 구독 플랜 변경 (FREE, PRO, ENTERPRISE)
  - 최대 채널 수 설정
  - 구독 활성화/비활성화
- 💰 **결제 관리**:
  - 결제 내역 조회
  - 수동 결제 생성
  - 결제 상태 변경 (PENDING, PAID, FAILED, REFUNDED)
  - 총 수익 통계
- 🤖 **AI PD 서비스 관리**:
  - Gemini API 키 설정 상태
  - 시스템 프롬프트 확인
  - API 키 설정 가이드
  - AI PD 대시보드 링크: `/ai-pd`

#### 슈퍼 관리자 엔드포인트:
| 엔드포인트 | 설명 |
|-----------|------|
| `POST /super-admin/promote` | 사용자 역할 변경 |
| `POST /super-admin/status` | 사용자 활성 상태 변경 |
| `POST /super-admin/subscription` | 구독 정보 수정 |
| `POST /super-admin/payment/create` | 결제 수동 생성 |
| `POST /super-admin/payment/status` | 결제 상태 변경 |

---

### 🤖 AI PD 비서 (유료 기능 - PRO+)
**위치:** 개인/기업 대시보드에 통합됨

⚠️ **중요**: `/ai-pd` 별도 대시보드는 제거되었습니다. AI PD 기능은 각 대시보드에 완전히 통합되어 있습니다.

#### 접근 권한:
- **FREE 사용자**: ❌ 사용 불가 (업그레이드 안내 표시)
- **PRO 사용자**: ✅ 사용 가능
- **ENTERPRISE 사용자**: ✅ 사용 가능
- **SUPER_ADMIN**: ✅ 항상 사용 가능

#### 크리에이터용 (개인 대시보드):
- ✅ 개인 채널 성과 분석
- ✅ 실시간 AI 상담 채팅
- ✅ 맞춤형 성장 전략 제안
- ✅ 데이터 기반 인사이트
- 📍 위치: `/dashboard` 하단

#### 매니저용 (기업 대시보드):
- ✅ 포트폴리오 전체 분석
- ✅ 크리에이터별 성과 비교
- ✅ 전략적 인사이트 제공
- ✅ 포트폴리오 최적화 가이드
- 📍 위치: `/manager/dashboard` 하단

#### API 엔드포인트:
- `POST /ai-pd/ask`: AI에게 질문하기 (PRO+ 구독 필요)

---

## 🔑 인증 및 권한 구조

### 사용자 역할 (UserRole):
```python
CREATOR = "creator"          # 개인 크리에이터
MANAGER = "manager"          # 기업 관리자
ADMIN = "admin"              # 일반 관리자
SUPER_ADMIN = "super_admin"  # 슈퍼 관리자
```

### 접근 권한:
| 페이지 | CREATOR | MANAGER | SUPER_ADMIN |
|-------|---------|---------|-------------|
| `/dashboard` | ✅ | ❌ | ✅ |
| `/manager/dashboard` | ❌ | ✅ | ✅ |
| `/super-admin` | ❌ | ❌ | ✅ (token 필요) |
| `/profile` | ✅ | ✅ | ✅ |

**주의**: `/ai-pd` 별도 페이지는 제거됨 - AI PD는 각 대시보드에 통합되어 있으며 PRO+ 구독 필요

---

## 🔧 환경 변수 설정

### 필수 환경 변수:
```bash
# 슈퍼 관리자 접속 토큰
SUPER_ADMIN_ACCESS_TOKEN=your-secret-token-here

# Gemini AI API 키 (옵션)
GEMINI_API_KEY=your-gemini-api-key-here

# 데이터베이스
DATABASE_URL=your-database-url

# JWT 시크릿
JWT_SECRET=your-jwt-secret
```

### 슈퍼 관리자 접속 방법:
1. `.env` 파일에 `SUPER_ADMIN_ACCESS_TOKEN` 설정
2. URL에 토큰 추가: `/super-admin?admin_token=YOUR_TOKEN`
3. 또는 쿠키에 저장된 토큰 사용 (첫 접속 후 자동)

---

## 📊 구독 플랜

| 플랜 | 최대 채널 수 | 대상 |
|------|-------------|------|
| FREE | 1 | 개인 크리에이터 |
| PRO | 5 | 프로 크리에이터 |
| ENTERPRISE | 20+ | 기업 관리자 |

---

## 🚀 배포 URL

**Production:** `https://marketing-analystics-573434207823.europe-west1.run.app`

### 주요 페이지 링크:
- 🏠 홈: https://marketing-analystics-573434207823.europe-west1.run.app/
- 🔐 로그인: https://marketing-analystics-573434207823.europe-west1.run.app/login
- 👤 개인 대시보드: https://marketing-analystics-573434207823.europe-west1.run.app/dashboard (AI PD 통합)
- 🏢 기업 대시보드: https://marketing-analystics-573434207823.europe-west1.run.app/manager/dashboard (AI PD 통합)
- 👑 슈퍼 관리자: https://marketing-analystics-573434207823.europe-west1.run.app/super-admin?admin_token=TOKEN

---

## 🛠️ 테스트 계정 생성

로컬에서 테스트 계정 생성:
```bash
python create_test_accounts.py
```

---

## 📝 주요 업데이트 내역

### 최근 수정 (2025-11-05)
- ✅ **AI PD 유료화**: PRO 이상 구독 필요 (FREE 사용자는 업그레이드 안내 표시)
- ✅ **`/ai-pd` 별도 대시보드 제거**: AI PD 기능은 개인/기업 대시보드에 완전 통합
- ✅ **구독 체크 강화**: `/ai-pd/ask` 엔드포인트에 구독 확인 추가
- ✅ 개인 대시보드에 AI PD 유료 기능 UI 추가
- ✅ 기업 대시보드에 AI PD 유료 기능 UI 추가
- ✅ 기업 관리자 대시보드에 구독 정보 전달 추가

### 이전 수정 (2025-10-27)
- ✅ 슈퍼관리자 권한 오류 수정 (`admin_token`만으로 접근 가능)
- ✅ 개인/기업 대시보드에 AI-PD 채팅창 통합 완료
- ✅ 매니저 대시보드 정상 작동 확인
- ✅ **SUPER_ADMIN 로그인 오류 수정**: 로그인 후 `/dashboard`로 리다이렉트 (모든 페이지 접근 가능)
  - MANAGER는 `/manager/dashboard`로 리다이렉트
  - CREATOR, SUPER_ADMIN 등은 `/dashboard`로 리다이렉트
  - `/super-admin`은 `admin_token` 필요하므로 수동 접속

---

## 🎯 다음 단계

1. **Cloud Run 재배포** 필요 (변경사항 반영)
2. **환경 변수 설정** 확인 (`SUPER_ADMIN_ACCESS_TOKEN`)
3. **Gemini API 키** 등록 (AI 기능 사용 시)
4. **테스트 계정으로 각 페이지 테스트**
