# Google Analytics 배포 가이드

## ✅ 완료된 작업

1. ✅ **Google Analytics 태그 추가** - [app/templates/base.html:7-14](app/templates/base.html#L7-L14)
   - 태그 ID: `G-FSSVWFPHHY`
   - 위치: `<head>` 태그 바로 아래

2. ✅ **Git 커밋 및 푸시 완료**
   - 커밋: `aa2c46e - feat: add Google Analytics tracking`
   - GitHub에 푸시 완료

---

## 🚀 Cloud Run 재배포 방법

### 방법 1: Google Cloud Console (웹 UI) ⭐ 추천

1. **Cloud Build 트리거 확인**
   - https://console.cloud.google.com/cloud-build/triggers 접속
   - GitHub 연동 트리거가 있으면 자동 배포됨
   - 없으면 수동 배포 필요 (방법 2)

2. **빌드 상태 확인**
   - https://console.cloud.google.com/cloud-build/builds 접속
   - 최신 빌드가 진행 중인지 확인
   - 성공하면 자동으로 Cloud Run에 배포됨

3. **Cloud Run 서비스 확인**
   - https://console.cloud.google.com/run 접속
   - `marketing-analystics` 서비스 클릭
   - 최신 리비전이 배포되었는지 확인

---

### 방법 2: Cloud Shell에서 수동 배포

#### 1단계: Cloud Shell 열기

1. https://console.cloud.google.com/ 접속
2. 우측 상단 **Cloud Shell 아이콘** 클릭 (터미널 아이콘)

#### 2단계: 프로젝트 설정 확인

\`\`\`bash
# 현재 프로젝트 확인
gcloud config get-value project

# 프로젝트 ID가 없으면 설정 (marketing-analytics-475700 등)
gcloud config set project marketing-analytics-475700
\`\`\`

#### 3단계: 저장소 클론 (처음만)

\`\`\`bash
# 홈 디렉토리로 이동
cd ~

# 저장소 클론 (처음만 실행)
git clone https://github.com/Kimchanghee/marketing_analystics.git

# 디렉토리 이동
cd marketing_analystics
\`\`\`

#### 4단계: 최신 코드 가져오기

\`\`\`bash
# 저장소 이동
cd ~/marketing_analystics

# 최신 코드 가져오기
git pull origin main
\`\`\`

#### 5단계: Cloud Run 배포

\`\`\`bash
# 배포 명령 실행
gcloud run deploy marketing-analystics \
  --source . \
  --region asia-northeast3 \
  --platform managed \
  --allow-unauthenticated
\`\`\`

**예상 소요 시간**: 3-5분

#### 6단계: 배포 완료 확인

배포가 완료되면 서비스 URL이 표시됩니다:
\`\`\`
Service [marketing-analystics] revision [marketing-analystics-00xxx] has been deployed and is serving 100 percent of traffic.
Service URL: https://marketing-analystics-xxxxxxxxxx-an.a.run.app
\`\`\`

---

### 방법 3: 로컬에서 gcloud 사용 (gcloud 설치 필요)

#### 1단계: gcloud 설치

- **Windows**: https://cloud.google.com/sdk/docs/install
- **macOS**: `brew install --cask google-cloud-sdk`
- **Linux**: https://cloud.google.com/sdk/docs/install

#### 2단계: 인증 및 배포

\`\`\`bash
# Google 계정으로 로그인
gcloud auth login

# 프로젝트 설정
gcloud config set project marketing-analytics-475700

# 현재 디렉토리에서 배포
gcloud run deploy marketing-analystics \
  --source . \
  --region asia-northeast3 \
  --platform managed \
  --allow-unauthenticated
\`\`\`

---

## 🧪 배포 후 확인 사항

### 1. 웹사이트 접속 테스트

\`\`\`
https://creatorscontrol.com
\`\`\`

브라우저에서 정상적으로 열리는지 확인

### 2. Google Analytics 태그 확인

#### 브라우저 개발자 도구로 확인:

1. **Chrome/Edge**:
   - `F12` 키 또는 `Ctrl + Shift + I`
   - **Network** 탭 클릭
   - 페이지 새로고침 (`F5`)
   - `gtag/js?id=G-FSSVWFPHHY` 검색
   - ✅ 200 OK 응답 확인

2. **Console 탭에서 확인**:
   \`\`\`javascript
   // 콘솔에서 실행
   console.log(window.gtag);
   // 출력: ƒ gtag(){dataLayer.push(arguments);}
   \`\`\`

#### Google Analytics 실시간 보고서:

1. https://analytics.google.com/ 접속
2. **보고서 > 실시간** 클릭
3. creatorscontrol.com에 접속
4. ✅ 실시간 사용자 수 증가 확인 (1명 이상)

### 3. Google Analytics 태그 검증

https://analytics.google.com/ 에서:

1. **관리 > 데이터 스트림** 클릭
2. `creatorscontrol.com` 스트림 선택
3. **태그 설정 안내 > 태그 설치 확인** 클릭
4. **"다시 테스트"** 버튼 클릭
5. ✅ **"태그가 감지되었습니다"** 메시지 확인

---

## 📊 배포 상태 모니터링

### Cloud Run 로그 확인

\`\`\`bash
# 실시간 로그 보기
gcloud run services logs tail marketing-analystics \
  --region asia-northeast3

# 최근 로그 50줄
gcloud run services logs read marketing-analystics \
  --region asia-northeast3 \
  --limit 50
\`\`\`

### Cloud Build 로그 확인

https://console.cloud.google.com/cloud-build/builds

---

## 🔧 트러블슈팅

### 문제 1: 배포가 실패함

**확인 사항:**
1. Dockerfile이 올바른지 확인
2. 환경 변수가 설정되어 있는지 확인
3. 빌드 로그 확인

**해결 방법:**
\`\`\`bash
# 빌드 로그 확인
gcloud builds list --limit=5
gcloud builds log <BUILD_ID>
\`\`\`

### 문제 2: 태그가 여전히 감지되지 않음

**확인 사항:**
1. 배포가 완료되었는지 확인
2. 브라우저 캐시 삭제 (`Ctrl + Shift + Delete`)
3. 시크릿 모드로 접속해서 테스트
4. 개발자 도구 Network 탭에서 `gtag/js` 확인

### 문제 3: 실시간 데이터가 보이지 않음

**해결 방법:**
1. 배포 후 5-10분 대기 (데이터 수집 시간)
2. 직접 creatorscontrol.com 접속
3. Google Analytics 실시간 보고서 새로고침

---

## 📋 체크리스트

배포 후 다음을 확인하세요:

- [ ] Cloud Run 배포 완료
- [ ] creatorscontrol.com 접속 가능
- [ ] 개발자 도구에서 gtag/js 로딩 확인 (200 OK)
- [ ] Google Analytics 실시간 보고서에서 데이터 확인
- [ ] "태그가 감지되었습니다" 메시지 확인
- [ ] 페이지뷰 데이터 수집 시작

---

## 🎉 완료!

모든 체크리스트를 완료하면:
- ✅ Google Analytics 태그가 정상 작동
- ✅ 사용자 방문 데이터 수집 시작
- ✅ 실시간 및 과거 데이터 분석 가능

---

## 📞 도움 필요 시

**참고 자료:**
- Cloud Run 문서: https://cloud.google.com/run/docs
- Google Analytics 문서: https://support.google.com/analytics/
- Cloud Build 문서: https://cloud.google.com/build/docs

**배포 명령어 빠른 참조:**

\`\`\`bash
# Cloud Shell에서 실행
cd ~/marketing_analystics
git pull origin main
gcloud run deploy marketing-analystics \
  --source . \
  --region asia-northeast3 \
  --platform managed \
  --allow-unauthenticated
\`\`\`
