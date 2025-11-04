# OAuth 소셜 로그인 설정 가이드

## 🎯 개요

Creator Control Center는 **기업/개인 역할을 구분한 소셜 로그인**을 지원합니다.

### ✅ 이미 구현된 기능

- **역할 선택**: 회원가입 시 개인 크리에이터 👤 또는 기업 관리자 🏢 선택
- **소셜 OAuth 플로우**: Google, Apple 지원
- **역할 자동 할당**: 소셜 로그인 시 선택한 역할로 계정 생성

### ⚙️ 설정 필요

각 소셜 제공자(Google, Apple 등)의 OAuth 인증 정보를 환경 변수에 설정해야 합니다.

---

## 🚀 추천 순서

1. **Google** ⭐ 가장 간단 (5-10분)
2. **Apple** (10-15분)
3. **Facebook** (선택)

---

## 1️⃣ Google OAuth 설정 ⭐ 추천

### 단계 1: Google Cloud Console 프로젝트 설정

1. **Google Cloud Console 접속**
   - https://console.cloud.google.com/

2. **기존 프로젝트 선택 또는 새 프로젝트 생성**
   - 현재 프로젝트: `marketing-analytics-475700` (이미 있음)
   - 또는 새로 만들기

3. **OAuth 동의 화면 구성**
   - 왼쪽 메뉴: **API 및 서비스 > OAuth 동의 화면**
   - User Type: **외부(External)** 선택
   - 앱 이름: `Creator Control Center`
   - 사용자 지원 이메일: 본인 이메일
   - 앱 로고: (선택사항)
   - 승인된 도메인:
     ```
     creatorscontrol.com
     ```
   - 개발자 연락처 이메일: 본인 이메일
   - **저장 후 계속**

4. **범위 추가**
   - **범위 추가 또는 삭제** 클릭
   - 다음 범위 선택:
     - ✅ `userinfo.email`
     - ✅ `userinfo.profile`
     - ✅ `openid`
   - **업데이트** 클릭

5. **테스트 사용자 추가** (선택사항)
   - 개발 중에는 테스트 사용자 추가
   - 본인 Gmail 주소 추가
   - **저장 후 계속**

### 단계 2: OAuth 2.0 클라이언트 ID 생성

1. **왼쪽 메뉴: API 및 서비스 > 사용자 인증 정보**

2. **+ 사용자 인증 정보 만들기 > OAuth 2.0 클라이언트 ID**

3. **애플리케이션 유형**: `웹 애플리케이션` 선택

4. **이름**: `Creator Control Center - Production`

5. **승인된 리디렉션 URI** 추가:
   ```
   https://creatorscontrol.com/oauth/google/callback
   ```

6. **만들기** 클릭

7. **클라이언트 ID와 클라이언트 보안 비밀** 복사:
   ```
   클라이언트 ID: 1234567890-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com
   클라이언트 보안 비밀: GOCSPX-xxxxxxxxxxxxxxxxxxxxxx
   ```

### 단계 3: 환경 변수 설정

#### 로컬 개발 (.env 파일)

`.env` 파일에 추가:

```env
# Google OAuth
GOOGLE_CLIENT_ID=1234567890-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxxx
```

#### Cloud Run (프로덕션)

**방법 A: gcloud 명령어**

```bash
gcloud run services update marketing-analystics \
  --region asia-northeast3 \
  --set-env-vars "GOOGLE_CLIENT_ID=YOUR_CLIENT_ID" \
  --set-env-vars "GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET"
```

**방법 B: Cloud Console**

1. https://console.cloud.google.com/run 접속
2. `marketing-analystics` 서비스 클릭
3. 상단 **"새 버전 수정 및 배포"** 클릭
4. **"변수 및 보안 비밀"** 탭
5. 환경 변수 추가:
   - `GOOGLE_CLIENT_ID`: (복사한 클라이언트 ID)
   - `GOOGLE_CLIENT_SECRET`: (복사한 클라이언트 보안 비밀)
6. **배포** 클릭

### 단계 4: 테스트

1. **회원가입 페이지 접속**
   ```
   https://creatorscontrol.com/signup
   ```

2. **역할 선택**
   - 👤 개인 크리에이터 또는
   - 🏢 기업 관리자 선택

3. **"Google로 계속하기" 버튼 클릭**

4. **Google 계정 선택 및 권한 승인**

5. **자동 로그인 및 리다이렉트**
   - 개인 크리에이터 → `/dashboard`
   - 기업 관리자 → `/manager/dashboard`

---

## 2️⃣ Apple OAuth 설정

### 단계 1: Apple Developer 계정 준비

1. **Apple Developer Program 가입** (연 $99)
   - https://developer.apple.com/programs/

2. **Apple Developer 콘솔 접속**
   - https://developer.apple.com/account/

### 단계 2: App ID 생성

1. **Certificates, Identifiers & Profiles** 선택

2. **Identifiers** 클릭

3. **+ 버튼** 클릭하여 새 Identifier 생성

4. **App IDs** 선택 → **Continue**

5. **App** 선택 → **Continue**

6. **정보 입력**:
   - Description: `Creator Control Center`
   - Bundle ID: `com.creatorscontrol.app` (또는 원하는 ID)
   - **Sign in with Apple** 체크 ✅
   - **Continue** → **Register**

### 단계 3: Services ID 생성

1. **Identifiers** → **+ 버튼**

2. **Services IDs** 선택 → **Continue**

3. **정보 입력**:
   - Description: `Creator Control Center Web`
   - Identifier: `com.creatorscontrol.service`
   - **Continue** → **Register**

4. **Services ID 구성**:
   - 생성한 Services ID 클릭
   - **Sign in with Apple** 체크 ✅
   - **Configure** 클릭
   - Primary App ID: 앞서 만든 App ID 선택
   - Domains and Subdomains:
     ```
     creatorscontrol.com
     ```
   - Return URLs:
     ```
     https://creatorscontrol.com/oauth/apple/callback
     ```
   - **Save** → **Continue** → **Register**

### 단계 4: Key 생성

1. **Keys** → **+ 버튼**

2. **Key Name**: `Creator Control Center Apple Sign In Key`

3. **Sign in with Apple** 체크 ✅

4. **Configure** 클릭 → Primary App ID 선택

5. **Save** → **Continue** → **Register**

6. **Download** 클릭하여 `.p8` 키 파일 다운로드
   - ⚠️ 한 번만 다운로드 가능!
   - Key ID 복사 (예: `A1B2C3D4E5`)

7. **Team ID 확인**
   - 우측 상단 계정 이름 클릭
   - Team ID 복사 (예: `X1Y2Z3A4B5`)

### 단계 5: Private Key 변환

다운로드한 `.p8` 파일을 환경 변수에 사용할 수 있도록 변환:

```bash
# .p8 파일 내용을 한 줄로 변환 (줄바꿈을 \n으로)
cat AuthKey_A1B2C3D4E5.p8 | awk '{printf "%s\\n", $0}' | pbcopy
```

### 단계 6: 환경 변수 설정

#### 로컬 (.env)

```env
# Apple OAuth
APPLE_CLIENT_ID=com.creatorscontrol.service
APPLE_TEAM_ID=X1Y2Z3A4B5
APPLE_KEY_ID=A1B2C3D4E5
APPLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\nMIGTAgEAMBMG...(한 줄로 변환된 키)\n-----END PRIVATE KEY-----
```

#### Cloud Run

```bash
gcloud run services update marketing-analystics \
  --region asia-northeast3 \
  --set-env-vars "APPLE_CLIENT_ID=com.creatorscontrol.service" \
  --set-env-vars "APPLE_TEAM_ID=X1Y2Z3A4B5" \
  --set-env-vars "APPLE_KEY_ID=A1B2C3D4E5" \
  --set-env-vars "APPLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n..."
```

---

## 3️⃣ Facebook OAuth 설정 (선택사항)

### 단계 1: Facebook 앱 생성

1. **Facebook Developers 접속**
   - https://developers.facebook.com/

2. **내 앱 > 앱 만들기**

3. **앱 유형**: `소비자` 선택

4. **앱 정보 입력**:
   - 앱 이름: `Creator Control Center`
   - 앱 연락처 이메일: 본인 이메일

5. **앱 만들기**

### 단계 2: Facebook 로그인 추가

1. **제품 추가 > Facebook 로그인 > 설정**

2. **웹 선택**

3. **사이트 URL**:
   ```
   https://creatorscontrol.com
   ```

4. **저장**

5. **Facebook 로그인 > 설정**:
   - 유효한 OAuth 리디렉션 URI:
     ```
     https://creatorscontrol.com/oauth/facebook/callback
     ```
   - **변경 내용 저장**

### 단계 3: 앱 ID 및 시크릿 복사

1. **설정 > 기본 설정**

2. **앱 ID** 복사

3. **앱 시크릿** 표시 → 복사

### 단계 4: 환경 변수 설정

```env
# Facebook OAuth
FACEBOOK_APP_ID=123456789012345
FACEBOOK_APP_SECRET=abcdef1234567890abcdef1234567890
```

---

## 🧪 테스트 체크리스트

### Google 로그인 테스트

- [ ] 회원가입 페이지에서 "Google로 계속하기" 버튼 보임
- [ ] 개인 크리에이터 선택 → Google 로그인 → `/dashboard`로 이동
- [ ] 기업 관리자 선택 → Google 로그인 → `/manager/dashboard`로 이동
- [ ] 프로필에 Google 이메일 및 이름 저장 확인
- [ ] 재로그인 시 기존 계정으로 로그인 확인

### Apple 로그인 테스트

- [ ] 회원가입 페이지에서 "Apple로 계속하기" 버튼 보임
- [ ] 개인 크리에이터 선택 → Apple 로그인 → `/dashboard`로 이동
- [ ] 기업 관리자 선택 → Apple 로그인 → `/manager/dashboard`로 이동
- [ ] "이메일 가리기" 기능 정상 작동 확인

---

## 🔧 트러블슈팅

### 문제 1: "Redirect URI mismatch" 오류

**원인**: OAuth 제공자에 등록한 리디렉션 URI가 일치하지 않음

**해결**:
1. OAuth 제공자 콘솔에서 리디렉션 URI 확인:
   ```
   https://creatorscontrol.com/oauth/google/callback
   https://creatorscontrol.com/oauth/apple/callback
   ```
2. 프로토콜(https), 도메인, 경로 모두 정확히 일치해야 함
3. 슬래시(/) 주의

### 문제 2: 소셜 로그인 버튼이 보이지 않음

**원인**: OAuth 제공자가 설정되지 않음

**확인**:
```bash
# 로컬에서 확인
python -c "from app.config import get_settings; s = get_settings(); print('Google:', bool(s.google_client_id))"
```

**해결**: 환경 변수 설정 후 서버 재시작

### 문제 3: "invalid_client" 오류

**원인**: 클라이언트 ID 또는 시크릿이 잘못됨

**해결**:
1. OAuth 콘솔에서 ID와 시크릿 재확인
2. 환경 변수에 정확히 복사했는지 확인
3. 공백이나 줄바꿈이 없는지 확인

### 문제 4: 역할이 잘못 저장됨

**원인**: JavaScript에서 역할 파라미터가 전달되지 않음

**확인**:
1. 브라우저 개발자 도구(F12) → Network 탭
2. OAuth 요청 URL에 `role=creator` 또는 `role=manager` 파라미터 확인

**해결**: [signup.html:272-285](app/templates/signup.html#L272-L285) JavaScript 확인

---

## 📊 OAuth 제공자 비교

| 제공자 | 난이도 | 비용 | 역할 분리 | 추천도 |
|--------|--------|------|-----------|--------|
| **Google** | ⭐ 쉬움 | 무료 | ✅ 지원 | ⭐⭐⭐⭐⭐ |
| **Apple** | ⭐⭐ 보통 | $99/년 | ✅ 지원 | ⭐⭐⭐⭐ |
| **Facebook** | ⭐⭐ 보통 | 무료 | ✅ 지원 | ⭐⭐⭐ |

---

## 🎯 권장 설정

### 최소 (필수)
- ✅ **Google** - 가장 널리 사용되는 소셜 로그인

### 추천
- ✅ **Google**
- ✅ **Apple** - iOS 사용자를 위한 필수

### 완전
- ✅ **Google**
- ✅ **Apple**
- ✅ **Facebook** - SNS 연동 서비스라면 추천

---

## 📝 관련 파일

- **OAuth 설정**: [app/config.py](app/config.py#L25-L36)
- **OAuth 플로우**: [app/routers/auth.py](app/routers/auth.py#L216-L349)
- **회원가입 UI**: [app/templates/signup.html](app/templates/signup.html#L14-L285)
- **OAuth 서비스**: [app/services/social_oauth.py](app/services/social_oauth.py)

---

## 🎉 완료!

OAuth 설정을 완료하면:
- ✅ 사용자가 **소셜 계정으로 빠르게 가입** 가능
- ✅ **개인/기업 역할을 선택**하여 회원가입
- ✅ 이메일/비밀번호 없이도 **간편하게 로그인**
- ✅ 보안성과 편의성 모두 향상

**다음 단계**: Google OAuth 설정부터 시작하세요! (5-10분 소요)
