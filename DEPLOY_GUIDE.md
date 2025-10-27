# 🚀 Cloud Run 배포 가이드

## ⚠️ 배포 전 체크리스트

### 1. 올바른 디렉토리 확인
배포 명령은 **프로젝트 루트 디렉토리**에서 실행해야 합니다.

```bash
# 현재 위치 확인
pwd

# 프로젝트 디렉토리로 이동
cd marketing_analystics

# 프로젝트 구조 확인
ls -la
```

**확인해야 할 파일들:**
- ✅ `app/` 디렉토리
- ✅ `requirements.txt`
- ✅ `Procfile` (또는 시작 명령 설정)
- ✅ `.gcloudignore` (옵션)

---

## 📋 배포 단계별 가이드

### Step 1: Git Repository에서 최신 코드 받기

```bash
# Cloud Shell에서 실행
cd ~
git clone https://github.com/Kimchanghee/marketing_analystics.git
cd marketing_analystics

# 또는 이미 클론했다면 업데이트
cd ~/marketing_analystics
git pull origin claude/fix-admin-permissions-011CUXPaXFEH5HyriuJfw1ry
```

### Step 2: 환경 변수 설정

`.env` 파일 생성 또는 Cloud Run 환경 변수 설정:

```bash
# .env 파일 생성 (옵션)
cat > .env << 'EOF'
DATABASE_URL=your-database-url
JWT_SECRET=your-jwt-secret
SUPER_ADMIN_ACCESS_TOKEN=your-super-admin-token
GEMINI_API_KEY=your-gemini-api-key
EOF
```

**또는 Cloud Run에서 환경 변수 직접 설정:**

```bash
gcloud run deploy marketing-analystics \
  --source . \
  --region europe-west1 \
  --set-env-vars "DATABASE_URL=your-db-url,JWT_SECRET=your-secret,SUPER_ADMIN_ACCESS_TOKEN=your-token"
```

### Step 3: 프로젝트 설정 확인

```bash
# Google Cloud 프로젝트 확인
gcloud config get-value project

# 프로젝트 설정 (필요시)
gcloud config set project marketing-analytics-475700
```

### Step 4: 배포 실행

```bash
# 프로젝트 루트에서 실행
cd ~/marketing_analystics

# 배포
gcloud run deploy marketing-analystics \
  --source . \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated
```

---

## 🛠️ 필수 파일 확인

### 1. `requirements.txt`

FastAPI 앱에 필요한 의존성:

```txt
fastapi
uvicorn[standard]
sqlmodel
python-multipart
python-jose[cryptography]
passlib[bcrypt]
pydantic[email]
jinja2
# ... 기타 필요한 패키지
```

### 2. `Procfile` 또는 시작 명령

**Procfile** (프로젝트 루트):
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**또는 배포 시 명령어 지정:**
```bash
gcloud run deploy marketing-analystics \
  --source . \
  --region europe-west1 \
  --command uvicorn \
  --args app.main:app,--host,0.0.0.0,--port,$PORT
```

### 3. `.gcloudignore` (옵션)

불필요한 파일 제외:
```
.git
.gitignore
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache
.venv/
venv/
env/
*.egg-info
.DS_Store
```

---

## 🐛 일반적인 오류 해결

### 오류 1: "Build failed"

**원인:**
- 잘못된 디렉토리에서 실행
- 필수 파일 누락
- 의존성 오류

**해결:**
```bash
# 1. 올바른 디렉토리 확인
pwd  # /home/user/marketing_analystics 이어야 함

# 2. 필수 파일 확인
ls -la requirements.txt app/main.py

# 3. requirements.txt 검증
python3 -m pip install -r requirements.txt --dry-run
```

### 오류 2: "Permission denied"

**해결:**
```bash
# 인증 다시 확인
gcloud auth login
gcloud auth application-default login
```

### 오류 3: "Service not found"

**해결:**
```bash
# 서비스가 없다면 첫 배포는 다음과 같이:
gcloud run deploy marketing-analystics \
  --source . \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10
```

---

## 📊 배포 후 확인

### 1. 서비스 상태 확인
```bash
gcloud run services describe marketing-analystics \
  --region europe-west1 \
  --format="value(status.url)"
```

### 2. 로그 확인
```bash
gcloud run services logs read marketing-analystics \
  --region europe-west1 \
  --limit=50
```

### 3. 환경 변수 확인
```bash
gcloud run services describe marketing-analystics \
  --region europe-west1 \
  --format="value(spec.template.spec.containers[0].env)"
```

---

## 🔐 환경 변수 설정 (중요!)

### Cloud Run에서 환경 변수 업데이트

```bash
gcloud run services update marketing-analystics \
  --region europe-west1 \
  --set-env-vars "DATABASE_URL=postgresql://user:pass@host/db" \
  --set-env-vars "JWT_SECRET=your-secret-key" \
  --set-env-vars "SUPER_ADMIN_ACCESS_TOKEN=your-admin-token" \
  --set-env-vars "GEMINI_API_KEY=your-gemini-key"
```

### Secret Manager 사용 (권장)

```bash
# Secret 생성
echo -n "your-secret-value" | gcloud secrets create super-admin-token --data-file=-

# Cloud Run에서 Secret 사용
gcloud run services update marketing-analystics \
  --region europe-west1 \
  --set-secrets="SUPER_ADMIN_ACCESS_TOKEN=super-admin-token:latest"
```

---

## 🎯 빠른 재배포

이미 배포된 서비스 업데이트:

```bash
cd ~/marketing_analystics
git pull origin main
gcloud run deploy marketing-analystics \
  --source . \
  --region europe-west1
```

---

## 📞 빌드 로그 확인

배포 실패 시 로그 URL 확인:
```
https://console.cloud.google.com/cloud-build/builds?project=marketing-analytics-475700
```

또는 CLI로:
```bash
gcloud builds list --limit=1
gcloud builds log <BUILD_ID>
```

---

## ✅ 성공적인 배포 후

1. **웹사이트 접속**: 배포 완료 후 나오는 URL로 접속
2. **테스트 계정으로 로그인**:
   - 마스터: kckc93@creatorcontrol.center / Ckdgml9788@
   - 크리에이터: creator@test.com / password123
   - 매니저: manager@test.com / password123
3. **각 대시보드 확인**
4. **환경 변수 설정 확인** (슈퍼 관리자 페이지 접속 시 필요)

---

## 🆘 여전히 오류가 발생한다면

1. **빌드 로그 확인**
2. **프로젝트 구조 재확인**
3. **의존성 버전 확인** (requirements.txt)
4. **데이터베이스 연결 확인**
5. **환경 변수 누락 확인**

문의: 로그를 공유해주시면 구체적인 해결책을 제시해드립니다.
