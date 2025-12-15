# 빠른 환경 변수 설정 가이드

## 🚀 Cloud Run 데이터베이스 설정 (자동)

### 1. Google Cloud Shell 열기
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 상단 오른쪽의 **Cloud Shell 활성화** 버튼 클릭 (>_ 아이콘)

### 2. 저장소 클론 (처음만)
\`\`\`bash
cd ~
git clone https://github.com/Kimchanghee/marketing_analystics.git
cd marketing_analystics
\`\`\`

### 3. 자동 설정 스크립트 실행
\`\`\`bash
chmod +x setup_database.sh
./setup_database.sh
\`\`\`

이 스크립트는 자동으로:
- ✅ Cloud SQL 인스턴스 생성 (없으면)
- ✅ 데이터베이스 생성
- ✅ 사용자 생성
- ✅ SECRET_KEY 생성
- ✅ Cloud Run 환경 변수 설정

**완료까지 약 10분 소요됩니다.**

---

## 🔧 수동 설정 (고급)

자동 스크립트를 사용하지 않으려면:

### 1. Cloud SQL 인스턴스 생성
\`\`\`bash
gcloud sql instances create marketing-db \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=europe-west1
\`\`\`

### 2. 데이터베이스 생성
\`\`\`bash
gcloud sql databases create marketing_analytics \
  --instance=marketing-db
\`\`\`

### 3. 사용자 생성
\`\`\`bash
gcloud sql users create dbuser \
  --instance=marketing-db \
  --password=YourSecurePassword123
\`\`\`

### 4. Public IP 확인
\`\`\`bash
gcloud sql instances describe marketing-db \
  --format="value(ipAddresses[0].ipAddress)"
\`\`\`

### 5. Cloud Run 환경 변수 설정
\`\`\`bash
# PUBLIC_IP를 위에서 확인한 IP로 변경
gcloud run services update marketing-analystics \
  --region europe-west1 \
  --set-env-vars "DATABASE_URL=postgresql://dbuser:YourSecurePassword123@PUBLIC_IP:5432/marketing_analytics" \
  --set-env-vars "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')" \
  --set-env-vars "ENVIRONMENT=production" \
  --set-env-vars "SUPER_ADMIN_ACCESS_TOKEN=Ckdgml9788@"
\`\`\`

---

## 💻 로컬 개발 환경 설정

### 1. .env 파일 생성
\`\`\`bash
cp .env.example .env
\`\`\`

### 2. .env 파일 수정
\`\`\`bash
ENVIRONMENT=development
DATABASE_URL=sqlite:///./app/app.db
SECRET_KEY=your-local-secret-key
SUPER_ADMIN_ACCESS_TOKEN=Ckdgml9788@
\`\`\`

### 3. 테스트 계정 생성
\`\`\`bash
python create_test_accounts.py
\`\`\`

### 4. 로컬 서버 실행
\`\`\`bash
uvicorn app.main:app --reload --port 8000
\`\`\`

---

## ✅ 설정 확인

### 1. 헬스체크
\`\`\`
https://marketing-analystics-573434207823.europe-west1.run.app/health
\`\`\`

**정상 응답:**
\`\`\`json
{
  "status": "healthy",
  "database": "connected",
  "environment": "production",
  "database_configured": true
}
\`\`\`

### 2. 로그인 테스트
\`\`\`
URL: https://marketing-analystics-573434207823.europe-west1.run.app/login
이메일: kckc93@creatorcontrol.center
비밀번호: Ckdgml9788@
\`\`\`

---

## 🆘 문제 해결

### "database": "disconnected"
\`\`\`bash
# 환경 변수 확인
gcloud run services describe marketing-analystics \
  --region europe-west1 \
  --format="value(spec.template.spec.containers[0].env)"
\`\`\`

### 로그 확인
\`\`\`bash
gcloud run services logs tail marketing-analystics \
  --region europe-west1
\`\`\`

### Cloud SQL 연결 오류
\`\`\`bash
# Cloud SQL 상태 확인
gcloud sql instances describe marketing-db

# Cloud SQL 재시작
gcloud sql instances restart marketing-db
\`\`\`

---

## 📊 비용 안내

**Cloud SQL (db-f1-micro):**
- 무료 tier 아님
- 월 약 $10-15
- 개발/테스트용으로 적합

**Cloud Run:**
- 요청당 과금
- 무료 tier 있음 (월 200만 요청)

---

## 🔐 보안 권장사항

1. **SECRET_KEY는 절대 공개하지 마세요**
2. **데이터베이스 비밀번호는 강력하게 설정하세요**
3. **Cloud SQL은 Private IP 사용을 권장합니다** (추가 설정 필요)
4. **프로덕션에서는 Secret Manager 사용을 권장합니다**

---

## 📚 더 자세한 정보

- [CLOUD_RUN_ENV_SETUP.md](CLOUD_RUN_ENV_SETUP.md) - 전체 설정 가이드
- [DATABASE_SETUP.md](DATABASE_SETUP.md) - 데이터베이스 상세 가이드
