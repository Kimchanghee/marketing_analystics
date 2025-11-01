# 소셜 미디어 OAuth 연동 설정 가이드

이 문서는 Creator Control Center에서 각 소셜 미디어 플랫폼의 OAuth 인증을 설정하는 방법을 상세히 설명합니다.

## 목차
- [전체 개요](#전체-개요)
- [Instagram](#instagram)
- [Facebook](#facebook)
- [Threads](#threads)
- [YouTube](#youtube)
- [Twitter/X](#twitterx)
- [TikTok](#tiktok)
- [문제 해결](#문제-해결)

---

## 전체 개요

### 작동 방식
1. 사용자가 "채널 연결" 버튼 클릭
2. OAuth 인증 페이지로 리디렉션
3. 사용자가 권한 승인
4. 콜백 URL로 인증 코드 반환
5. 서버가 액세스 토큰 교환
6. 토큰 암호화 저장 및 데이터 수집 시작

### 필수 요구사항
- HTTPS 필수 (프로덕션 환경)
- 각 플랫폼의 개발자 계정
- 콜백 URL 설정: `https://yourdomain.com/channels/callback/{platform}`

---

## Instagram

### 1. Meta 개발자 계정 설정

#### Step 1: 앱 생성
1. [Meta Developers](https://developers.facebook.com/)에 로그인
2. **My Apps** > **Create App** 클릭
3. Use case 선택: **Other**
4. App type: **Business**
5. 앱 이름 입력 (예: "Creator Control Center")

#### Step 2: Instagram 제품 추가
1. Dashboard에서 **Add Product** 클릭
2. **Instagram Graph API** 선택 및 **Set Up** 클릭
   - 또는 **Instagram Basic Display** (간단한 접근용)
   - Meta Graph API v20.0 엔드포인트 기준으로 설정

> **참고**: 본 가이드는 2024년 7월 릴리스된 Meta Graph API v20.0을 기준으로 작성했습니다. v18.x~19.x 토큰은 2025년 7월 이후 지원이 종료되므로 새 앱 등록과 검수는 반드시 v20.0으로 진행하세요.

#### Step 3: OAuth 설정
1. 좌측 메뉴에서 **Instagram Graph API** > **Basic Settings**
2. **OAuth Redirect URIs** 추가:
   ```
   https://yourdomain.com/channels/callback/instagram
   http://localhost:8000/channels/callback/instagram (개발용)
   ```
3. **Valid OAuth Redirect URIs** 저장

#### Step 4: 자격 증명 복사
1. **Settings** > **Basic** 메뉴
2. **App ID** 복사
3. **App Secret** 표시 후 복사
4. `.env` 파일에 추가:
   ```env
   FACEBOOK_APP_ID=your_app_id
   FACEBOOK_APP_SECRET=your_app_secret
   ```

### 2. Instagram Business 계정 설정

#### 필수 조건:
- Instagram 계정을 **Business** 또는 **Creator** 계정으로 전환
- Facebook 페이지와 연결

#### 전환 방법:
1. Instagram 앱 > **Settings** > **Account**
2. **Switch to Professional Account** 선택
3. **Business** 또는 **Creator** 선택
4. Facebook 페이지 연결

### 3. 필요한 권한

```
instagram_basic
instagram_manage_insights
pages_show_list
pages_read_engagement
```

### 4. 앱 검수 (프로덕션)
- 테스트 환경: 개발자 및 테스터만 사용 가능
- 프로덕션: Facebook 앱 검수 필요 (2-14일 소요)
- 검수 항목:
  - `instagram_basic`
  - `instagram_manage_insights`
  - `pages_show_list`

### 5. 테스트
```bash
curl "https://graph.facebook.com/v20.0/me/accounts?access_token=YOUR_TOKEN"
```

---

## Facebook

### 1. 앱 설정 (Instagram과 동일한 앱 사용 가능)

#### Step 1: Facebook Login 제품 추가
1. Dashboard > **Add Product** > **Facebook Login**
2. **Settings** 선택

#### Step 2: OAuth 설정
1. **Valid OAuth Redirect URIs** 추가:
   ```
   https://yourdomain.com/channels/callback/facebook
   ```
2. **Client OAuth Settings** 활성화:
   - ✓ Web OAuth Login
   - ✓ Use Strict Mode for Redirect URIs

> **참고**: Facebook Graph API 호출도 v20.0 기준으로 테스트되었습니다. v18.x 토큰은 2025년 중 지원이 종료되므로 호출 URL과 검수 정보도 v20.0으로 맞추어 주세요.

#### Step 3: 권한 설정
필요한 권한:
```
pages_show_list
pages_read_engagement
pages_read_user_content
read_insights
```

### 2. Facebook 페이지 필요
- 관리자 권한이 있는 Facebook 페이지 필요
- 페이지 설정 > **Settings** > **Instagram** 에서 Instagram 계정 연결 가능

### 3. 테스트
```bash
curl "https://graph.facebook.com/v20.0/me/accounts?fields=id,name,followers_count&access_token=YOUR_TOKEN"
```

---

## Threads

### 1. 개요

#### 현재 상태 (2024년 하반기 기준)
- Meta Threads Graph API가 2024년 7월부터 공개 베타로 제공됩니다.
- Instagram Graph API와 동일한 Meta 앱에서 Threads API 제품을 추가한 뒤 승인을 받아야 합니다.
- 프로덕션 사용을 위해서는 Business Verification과 권한 검수가 필수입니다.

#### Step 1: Threads API 신청
1. [Meta Developers](https://developers.facebook.com/)
2. 기존 앱에서 **Add Product** > **Threads API** 선택 후 **Set Up**
3. 승인 소요: 평균 5~10 영업일 (검수 답변에 따라 변동)

#### Step 2: OAuth 설정
```
https://yourdomain.com/channels/callback/threads
```
> **참고**: Threads API도 Graph API v20.0 엔드포인트를 사용하며, 승인 완료 전까지는 테스트 모드 토큰만 호출할 수 있습니다.

### 2. 필요 권한
```
threads_basic
threads_content_publish
threads_manage_insights
```

### 3. 승인 팁
- Threads 계정은 Instagram 비즈니스/크리에이터 계정과 연결되어 있어야 합니다.
- 콘텐츠 정책과 모더레이션 계획을 검수 답변에 포함하세요.
- 초기에는 읽기 전용 권한만 허용될 수 있으니 대시보드 활용 범위를 명확히 설명합니다.

---

## YouTube

> **참고**: 2024년 기준 YouTube Data API는 여전히 v3가 최신이며, Analytics API는 별도 활성화가 필요합니다.

### 1. Google Cloud 프로젝트 생성

#### Step 1: 프로젝트 생성
1. [Google Cloud Console](https://console.cloud.google.com/) 로그인
2. 상단의 프로젝트 선택 > **New Project**
3. 프로젝트 이름 입력 (예: "Creator Control Center")

#### Step 2: YouTube Data API v3 활성화
1. **APIs & Services** > **Library**
2. "YouTube Data API v3" 검색
3. **Enable** 클릭
4. "YouTube Analytics API" 도 활성화 (선택사항)

#### Step 3: OAuth 2.0 클라이언트 생성
1. **APIs & Services** > **Credentials**
2. **Create Credentials** > **OAuth client ID**
3. Application type: **Web application**
4. Name: "CCC Web Client"
5. **Authorized redirect URIs** 추가:
   ```
   https://yourdomain.com/channels/callback/youtube
   http://localhost:8000/channels/callback/youtube (개발용)
   ```
6. **Create** 클릭

#### Step 4: 자격 증명 다운로드
1. 생성된 OAuth 2.0 Client ID 클릭
2. Client ID와 Client Secret 복사
3. `.env` 파일에 추가:
   ```env
   GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=xxx
   ```

### 2. OAuth 동의 화면 설정

#### Step 1: 동의 화면 구성
1. **OAuth consent screen** 메뉴
2. User Type: **External** (테스트는 Internal도 가능)
3. 앱 정보 입력:
   - App name
   - User support email
   - Developer contact email
4. **Save and Continue**

#### Step 2: 스코프 추가
```
https://www.googleapis.com/auth/youtube.readonly
https://www.googleapis.com/auth/yt-analytics.readonly
```

#### Step 3: 테스트 사용자 추가 (개발 중)
- 본인 및 테스터의 Google 계정 이메일 추가

### 3. 프로덕션 배포
- **Publishing status**를 **In Production**으로 변경
- 앱 검증 필요 (민감한 스코프 사용 시)
- 검증 기간: 4-6주

### 4. 테스트
```bash
curl "https://www.googleapis.com/youtube/v3/channels?part=statistics&mine=true&access_token=YOUR_TOKEN"
```

---

## Twitter/X

### 1. X 개발자 계정 생성

#### Step 1: 개발자 포털 접근
1. [X Developer Platform](https://developer.x.com/) 로그인
2. **Sign Up** > **Apply for access** 메뉴에서 신청
3. 데이터 사용 목적과 정책 준수 계획을 구체적으로 작성 (비즈니스 사이트 URL 포함)

#### Step 2: 앱 생성
1. **Projects & Apps** > **Create App**
2. App name 입력 (고유값 권장)
3. Environment: **Development** 또는 **Production**

#### Step 3: OAuth 2.0 설정
1. 생성한 앱에서 **Settings** 이동
2. **User authentication settings** > **Set up** 클릭
3. App permissions:
   - Read
4. Type of App: **Web App, Automated App or Bot**
5. App info:
   - **Callback URI / Redirect URL**:
     ```
     https://yourdomain.com/channels/callback/twitter
     ```
   - **Website URL**: https://yourdomain.com

#### Step 4: 자격 증명 복사
1. **Keys and tokens** 메뉴 이동
2. **OAuth 2.0 Client ID and Client Secret** 생성
3. `.env` 파일에 추가:
   ```env
   TWITTER_CLIENT_ID=your_client_id
   TWITTER_CLIENT_SECRET=your_client_secret
   ```

### 2. API Access Level

#### Free (테스트용)
- 월 1,500건 이하의 POST(쓰기) 요청만 허용, 읽기 엔드포인트는 제공되지 않음
- 로그인/봇 테스트 용도로만 사용 가능

#### Basic ($100/월)
- 월 50,000건 읽기 + 10,000건 쓰기 한도 (2024년 8월 갱신 기준)
- tweet.read, users.read, follows.read 엔드포인트 이용 가능

#### Pro ($5,000/월 이상)
- 최대 1,000,000건 이상 읽기, 실시간 웹훅 및 엔터프라이즈 지원 포함
- SLA와 복수 앱 운영이 필요할 때 권장

> **참고**: 최신 한도는 [X Developer Pricing](https://developer.x.com/en/products/x-api)에서 반드시 확인하세요.

### 3. 필요 Scope
```
tweet.read
users.read
follows.read
offline.access
```

### 4. 테스트
```bash
curl "https://api.twitter.com/2/users/me" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## TikTok

### 1. TikTok for Developers 계정

#### Step 1: 개발자 등록
1. [TikTok for Developers](https://developers.tiktok.com/) 로그인
2. **Register** 클릭
3. 개발자 약관 동의

#### Step 2: 앱 생성
1. **My Apps** > **Create an App**
2. App name 입력
3. App description 작성

#### Step 3: Login Kit 설정
1. 생성된 앱 > **Login Kit** 선택
2. **Add Product** 클릭
3. Redirect URL 추가:
   ```
   https://yourdomain.com/channels/callback/tiktok
   ```

#### Step 4: 자격 증명 복사
1. **Basic information** 탭
2. **Client Key** 복사
3. **Client Secret** 복사
4. `.env` 파일에 추가:
   ```env
   TIKTOK_CLIENT_KEY=your_client_key
   TIKTOK_CLIENT_SECRET=your_client_secret
   ```

### 2. 앱 심사

#### 제출 요구사항:
- 앱 로고 (512x512px)
- 사용 사례 설명
- 스크린샷
- 데이터 사용 정책

#### 심사 기간:
- 일반적으로 3-10 영업일
- 추가 정보 요청 가능

### 3. 필요한 스코프
```
user.info.basic
video.list
video.insights
```

### 4. 제한 사항
- **비즈니스 계정**에서만 일부 API 사용 가능
- 데이터 접근이 제한적
- 높은 승인 기준

### 5. 테스트
```bash
curl "https://open.tiktokapis.com/v2/user/info/?fields=open_id,union_id,avatar_url" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 문제 해결

### 공통 문제

#### 1. "Redirect URI mismatch" 오류
**원인**: 콜백 URL이 등록된 URL과 일치하지 않음

**해결**:
```env
# 프로덕션
https://yourdomain.com/channels/callback/{platform}

# 개발 (localhost)
http://localhost:8000/channels/callback/{platform}
```

#### 2. "Invalid client_id" 오류
**원인**: 환경 변수가 제대로 설정되지 않음

**확인**:
```bash
# .env 파일 확인
cat .env | grep CLIENT_ID

# 서버 재시작
```

#### 3. Token Expired
**원인**: 액세스 토큰 만료

**해결**: 채널 관리 페이지에서 "갱신" 버튼 클릭

### 플랫폼별 문제

#### Instagram: "Instagram account is not a Business account"
- Instagram 설정에서 Professional 계정으로 전환 필요

#### YouTube: "The request is missing a valid API key"
- YouTube Data API v3가 활성화되었는지 확인
- API 키 할당량 확인

#### Twitter/X: "You currently have Essential access"
- Free 티어는 읽기 엔드포인트가 제공되지 않으므로 Basic 이상으로 업그레이드 필요
- 권한 요청 사유와 데이터 사용 범위를 명확히 기재

#### TikTok: "App is still in review"
- TikTok 앱 심사 완료 대기
- Sandbox 환경에서 테스트 불가

---

## 로컬 개발 환경 설정

### 1. ngrok을 사용한 HTTPS 터널링

```bash
# ngrok 설치
brew install ngrok  # Mac
# 또는 https://ngrok.com/download

# 터널 시작
ngrok http 8000

# 출력된 HTTPS URL을 각 플랫폼의 콜백 URL로 등록
# 예: https://abc123.ngrok.io/channels/callback/instagram
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 각 플랫폼의 자격 증명 입력
nano .env
```

### 3. 서버 실행

```bash
# 가상 환경 활성화
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 서버 시작
uvicorn app.main:app --reload --port 8000
```

### 4. 테스트

```bash
# 채널 관리 페이지 접속
open http://localhost:8000/channels/manage

# 또는 ngrok URL
open https://abc123.ngrok.io/channels/manage
```

---

## 프로덕션 배포 체크리스트

- [ ] 모든 OAuth 클라이언트 ID/Secret 설정
- [ ] 프로덕션 도메인의 HTTPS 콜백 URL 등록
- [ ] `.env` 파일의 `ENVIRONMENT=production` 설정
- [ ] `SECRET_KEY` 강력한 랜덤 문자열로 변경
- [ ] 각 플랫폼의 앱 상태를 "프로덕션"으로 변경
- [ ] 필요한 권한에 대한 앱 검수 완료
- [ ] 데이터베이스를 PostgreSQL로 변경
- [ ] API 할당량 및 비용 모니터링 설정
- [ ] 에러 로깅 및 알림 설정
- [ ] 토큰 갱신 크론잡 설정 (선택사항)

---

## 참고 자료

### 공식 문서
- [Meta Developers - Instagram API](https://developers.facebook.com/docs/instagram-api)
- [Google Cloud - YouTube API](https://developers.google.com/youtube/v3)
- [X Developer Platform - X API](https://developer.x.com/en/products/x-api)
- [TikTok for Developers](https://developers.tiktok.com/doc/overview)

### 유용한 도구
- [JWT Debugger](https://jwt.io/)
- [Postman](https://www.postman.com/) - API 테스트
- [ngrok](https://ngrok.com/) - 로컬 HTTPS 터널링

---

## 지원

문제가 발생하면:
1. 로그 확인: 서버 콘솔 출력 및 에러 메시지
2. 환경 변수 확인: `.env` 파일의 모든 값이 올바른지 확인
3. 각 플랫폼의 개발자 대시보드에서 API 사용량 및 에러 확인
4. GitHub Issues에 문의

**이메일**: support@yourcompany.com

