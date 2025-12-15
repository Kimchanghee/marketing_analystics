# 🚀 빌드 및 배포 가이드

## 📋 최근 변경사항 (2025-11-05)

### ✅ 주요 수정 내용:
1. **AI PD 유료화 완료**
   - PRO/ENTERPRISE 구독 필요
   - FREE 사용자는 업그레이드 안내 표시
   - `/ai-pd/ask` 엔드포인트에 구독 체크 추가

2. **`/ai-pd` 별도 대시보드 제거**
   - AI PD 기능은 개인/기업 대시보드에 완전 통합
   - `app/templates/ai_pd_dashboard.html` 삭제

3. **SUPER_ADMIN 로그인 수정**
   - 로그인 후 `/dashboard`로 자동 리다이렉트
   - `/super-admin`은 수동으로 접속 필요
   - 404 에러 해결

4. **대시보드 개선**
   - 개인 대시보드: AI PD 유료 기능 UI 추가
   - 기업 대시보드: AI PD 유료 기능 UI + 구독 정보 추가

---

## 🔧 로컬 테스트

### 1. 의존성 설치
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 2. 환경 변수 설정
`.env` 파일 확인:
\`\`\`bash
DATABASE_URL=your-database-url
JWT_SECRET=your-jwt-secret
GEMINI_API_KEY=your-gemini-api-key
SUPER_ADMIN_ACCESS_TOKEN=your-super-admin-token
\`\`\`

### 3. 로컬 서버 실행
\`\`\`bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

### 4. 테스트 계정으로 로그인
- **FREE 사용자**: `creator@test.com` / `password123`
- **PRO 사용자**: AI PD 기능 테스트용 (구독 업그레이드 필요)
- **기업 관리자**: `manager@test.com` / `password123`
- **슈퍼 관리자**: `kckc93@creatorscontrol.com` / `Ckdgml9788@`

---

## 🐳 Docker 빌드 (선택사항)

\`\`\`bash
# 이미지 빌드
docker build -t marketing-analytics:latest .

# 컨테이너 실행
docker run -p 8080:8080 --env-file .env marketing-analytics:latest
\`\`\`

---

## ☁️ Cloud Run 배포

### 1. Google Cloud 프로젝트 설정
\`\`\`bash
# 프로젝트 ID 확인
gcloud config get-value project

# 프로젝트 설정 (필요시)
gcloud config set project YOUR_PROJECT_ID
\`\`\`

### 2. Container Registry에 이미지 빌드 및 푸시
\`\`\`bash
# Cloud Build 사용 (권장)
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/marketing-analytics

# 또는 로컬에서 빌드 후 푸시
docker build -t gcr.io/YOUR_PROJECT_ID/marketing-analytics .
docker push gcr.io/YOUR_PROJECT_ID/marketing-analytics
\`\`\`

### 3. Cloud Run에 배포
\`\`\`bash
gcloud run deploy marketing-analystics \
  --image gcr.io/YOUR_PROJECT_ID/marketing-analytics \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=YOUR_DB_URL,JWT_SECRET=YOUR_SECRET,GEMINI_API_KEY=YOUR_KEY,SUPER_ADMIN_ACCESS_TOKEN=YOUR_TOKEN"
\`\`\`

### 4. 환경 변수 업데이트 (Secret Manager 사용 권장)
\`\`\`bash
# Secret 생성
echo -n "your-secret-value" | gcloud secrets create SECRET_NAME --data-file=-

# Cloud Run에서 Secret 사용
gcloud run services update marketing-analystics \
  --update-secrets DATABASE_URL=database-url:latest \
  --region europe-west1
\`\`\`

---

## ✅ 배포 후 체크리스트

### 1. 기본 페이지 접속 확인
- [ ] 홈 페이지: `/`
- [ ] 로그인 페이지: `/login`
- [ ] 회원가입 페이지: `/signup`

### 2. 크리에이터 대시보드 (FREE)
- [ ] 로그인: `creator@test.com`
- [ ] 대시보드 접속: `/dashboard`
- [ ] AI PD 섹션에 업그레이드 안내 표시 확인
- [ ] 채널 추가/제거 기능 확인

### 3. 크리에이터 대시보드 (PRO)
- [ ] PRO 구독 설정 (슈퍼 관리자에서)
- [ ] AI PD 채팅 기능 사용 가능 확인
- [ ] AI 질문/답변 테스트

### 4. 기업 관리자 대시보드
- [ ] 로그인: `manager@test.com`
- [ ] 대시보드 접속: `/manager/dashboard`
- [ ] 크리에이터 관리 기능 확인
- [ ] AI PD 포트폴리오 분석 확인
- [ ] Gemini API 키 설정 확인

### 5. 슈퍼 관리자
- [ ] 로그인: `kckc93@creatorscontrol.com`
- [ ] 로그인 후 `/dashboard`로 리다이렉트 확인
- [ ] 수동으로 `/super-admin` 접속
- [ ] 회원 관리 기능 확인
- [ ] 구독 관리 기능 확인
- [ ] 결제 관리 기능 확인

### 6. AI 기능 테스트
- [ ] 개인 대시보드 AI PD 채팅
- [ ] 기업 대시보드 AI PD 포트폴리오 분석
- [ ] CS 문의 AI 답변 생성

---

## 🐛 트러블슈팅

### 문제 1: SUPER_ADMIN 로그인 후 404 에러
**해결됨**: 로그인 후 `/dashboard`로 자동 리다이렉트되도록 수정

### 문제 2: AI PD 기능 사용 시 402 에러
**원인**: 구독이 FREE 티어  
**해결**: 슈퍼 관리자에서 사용자 구독을 PRO/ENTERPRISE로 업그레이드

### 문제 3: Gemini API 키 오류
**원인**: API 키 미설정 또는 잘못된 키  
**해결**: 
- 시스템 전역: `.env`에서 `GEMINI_API_KEY` 설정
- 기업 관리자: 대시보드에서 개별 API 키 등록

### 문제 4: 데이터베이스 연결 실패
**원인**: DATABASE_URL 환경 변수 미설정  
**해결**: Cloud Run 환경 변수 또는 Secret Manager에서 설정

---

## 📊 모니터링

### Cloud Run 로그 확인
\`\`\`bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=marketing-analystics" --limit 50 --format json
\`\`\`

### 에러 로그 필터링
\`\`\`bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=marketing-analystics AND severity>=ERROR" --limit 50
\`\`\`

---

## 🔄 롤백

문제 발생 시 이전 버전으로 롤백:
\`\`\`bash
# 이전 리비전 확인
gcloud run revisions list --service marketing-analystics --region europe-west1

# 특정 리비전으로 롤백
gcloud run services update-traffic marketing-analystics \
  --to-revisions REVISION_NAME=100 \
  --region europe-west1
\`\`\`

---

## 📞 지원

문제가 지속되면 다음을 확인하세요:
1. `ACCOUNTS_AND_PAGES.md` - 계정 및 권한 정보
2. `PERMISSION_GUIDE.md` - 권한 관리 가이드
3. Cloud Run 로그 - 서버 에러 확인
4. 브라우저 콘솔 - 클라이언트 에러 확인

---

**마지막 업데이트**: 2025-11-05  
**배포 URL**: https://marketing-analystics-573434207823.europe-west1.run.app
