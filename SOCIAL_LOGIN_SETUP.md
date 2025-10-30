# 소셜 로그인 설정 가이드

구글과 애플 로그인은 OAuth 2.0 / OpenID Connect 흐름을 사용합니다. 아래 단계에 따라 각 제공자 콘솔에서 자격 정보를 발급하고 `.env` 또는 실행 환경 변수에 값을 주입한 뒤 서버를 재시작하세요.

## 1. 필수 환경 변수

| 변수명 | 설명 |
| --- | --- |
| `GOOGLE_CLIENT_ID` | Google Cloud Console에서 발급한 OAuth 클라이언트 ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 클라이언트 비밀키 |
| `APPLE_CLIENT_ID` | Apple Developer Portal의 Service ID (eg. `com.example.login`) |
| `APPLE_TEAM_ID` | Apple Developer 계정 Team ID |
| `APPLE_KEY_ID` | Apple에서 발급한 Sign In with Apple 키의 Key ID |
| `APPLE_PRIVATE_KEY` | Apple 인증서(.p8)의 PEM 문자열. 여러 줄일 경우 `\n` 대신 실제 줄바꿈을 포함하여 입력 |

> **참고**  
> Cloud Run 등에 배포할 때는 환경 변수로 직접 넣거나 Secret Manager를 사용해 주입하세요. 로컬 개발이라면 `.env` 파일에 추가하고 `uvicorn` 실행 전에 `source` 또는 `python-dotenv`가 로드되도록 합니다.

## 2. 구글 로그인 설정

1. [Google Cloud Console](https://console.cloud.google.com/apis/credentials)에서 프로젝트를 생성하거나 선택합니다.
2. `사용자 인증 정보` → `사용자 인증 정보 만들기` → `OAuth 클라이언트 ID`를 선택합니다.  
   - **애플리케이션 유형**은 `웹 애플리케이션`으로 지정합니다.  
   - **승인된 리디렉션 URI**에 다음 주소를 추가합니다.
     ```
     http://localhost:8000/oauth/google/callback
     https://{배포도메인}/oauth/google/callback
     ```
3. 생성이 완료되면 `클라이언트 ID`와 `클라이언트 보안 비밀` 값을 위 표의 환경 변수에 매핑합니다.
4. OAuth 동의 화면에서 앱 이름과 스코프(기본 이메일/프로필) 등을 설정하고 게시합니다.

## 3. 애플 로그인 설정

1. [Apple Developer](https://developer.apple.com/account/resources/certificates/list) 계정에 로그인합니다.
2. `Identifiers`에서 `Service IDs`를 생성합니다.  
   - Identifier 예: `com.example.login`  
   - `Sign In with Apple`을 활성화하고 **Web Domain** 및 **Return URL**에 다음 주소를 입력합니다.
     ```
     https://{배포도메인}/oauth/apple/callback
     http://localhost:8000/oauth/apple/callback
     ```
3. `Keys` 메뉴에서 `Sign in with Apple`을 선택해 새로운 키를 발급합니다.  
   - 발급 시 `Service ID`를 연결해야 합니다.  
   - 생성한 `.p8` 파일을 안전한 위치에 보관합니다.
4. 위에서 발급한 정보를 환경 변수에 매핑합니다.
   - `APPLE_CLIENT_ID` → Service ID 값  
   - `APPLE_TEAM_ID` → Apple Developer 계정의 Team ID  
   - `APPLE_KEY_ID` → 생성한 키의 Key ID  
   - `APPLE_PRIVATE_KEY` → `.p8` 파일 내용을 그대로 복사하여 줄바꿈 포함 문자열로 저장
5. Apple은 24시간 이내 최초 로그인에서만 이름을 전달하므로, 초기 연결 후에는 프로필 이름이 비어 있을 수 있습니다.

## 4. 서버 재시작 및 검증

1. 환경 변수 설정 후 서버를 재시작합니다.
2. `/login` 또는 `/signup` 화면에서 Google / Apple 버튼을 클릭하여 OAuth 흐름이 정상적으로 리다이렉트되는지 확인합니다.
3. 콘솔 로그에 `login_social_google`, `login_social_apple` 활동 로그가 기록되는지 확인하면 완료입니다.
