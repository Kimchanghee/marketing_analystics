# 데이터베이스 계정 생성 가이드

Cloud Run에서 데이터베이스에 테스트 계정을 생성하는 3가지 방법을 설명합니다.

---

## 방법 1: Cloud Shell 사용 (가장 간단, 추천)

Cloud Shell은 Google Cloud Console에서 바로 사용할 수 있는 무료 온라인 터미널입니다.

### 1단계: Cloud Shell 열기

1. **Google Cloud Console 접속**:
   \`\`\`
   https://console.cloud.google.com/
   \`\`\`

2. **프로젝트 선택**:
   - 상단에서 현재 프로젝트 선택
   - 프로젝트 ID 확인

3. **Cloud Shell 열기**:
   - 우측 상단의 **터미널 아이콘** (>_) 클릭
   - 또는 단축키: `Alt+Shift+M` (Windows), `Option+Shift+M` (Mac)
   - 화면 하단에 터미널 창이 열립니다

### 2단계: 환경 변수 확인

Cloud Run 서비스에 설정된 DATABASE_URL을 확인합니다.

\`\`\`bash
# Cloud Shell에서 실행
gcloud run services describe marketing-analystics \
  --region europe-west1 \
  --format="value(spec.template.spec.containers[0].env)" \
  | grep DATABASE_URL
\`\`\`

출력 예시:
\`\`\`
DATABASE_URL=postgresql://user:password@/dbname?host=/cloudsql/project:region:instance
\`\`\`

또는 **Cloud Console UI에서 확인**:
1. https://console.cloud.google.com/run/detail/europe-west1/marketing-analystics/variables
2. "Variables & Secrets" 탭
3. DATABASE_URL 값 복사

### 3단계: 저장소 클론 및 설정

\`\`\`bash
# Cloud Shell에서 실행

# 1. 저장소 클론
git clone https://github.com/Kimchanghee/marketing_analystics.git
cd marketing_analystics

# 2. 환경 변수 설정 (위에서 확인한 DATABASE_URL 사용)
export DATABASE_URL="postgresql://user:password@host:port/database"

# 또는 Cloud SQL Unix Socket 형식인 경우:
# export DATABASE_URL="postgresql://user:password@/dbname?host=/cloudsql/project:region:instance"

# 3. 환경 변수 확인
echo $DATABASE_URL
\`\`\`

### 4단계: Python 패키지 설치

\`\`\`bash
# Cloud Shell에서 실행

# Python 버전 확인
python3 --version

# 패키지 설치
pip3 install -r requirements.txt
\`\`\`

설치 시간: 약 1-2분

### 5단계: 계정 생성 스크립트 실행

\`\`\`bash
# Cloud Shell에서 실행

python3 create_test_accounts.py
\`\`\`

**성공 시 출력**:
\`\`\`
✅ Creator 계정 생성 완료: creator@test.com / password123
✅ Manager 계정 생성 완료: manager@test.com / password123
✅ Super Admin 계정 생성 완료: admin@test.com / password123
✅ 마스터 관리자 계정 생성 완료: kckc93@creatorcontrol.center / Ckdgml9788@

============================================================
테스트 계정 생성 완료!
============================================================

📋 로그인 정보:

1️⃣ Creator (개인 크리에이터)
   이메일: creator@test.com
   비밀번호: password123
   ...

4️⃣ 마스터 관리자 (모든 대시보드 접근 가능)
   이메일: kckc93@creatorcontrol.center
   비밀번호: Ckdgml9788@
   접속: http://127.0.0.1:8000/login
   → 개인 대시보드: http://127.0.0.1:8000/dashboard
   → 기업 대시보드: http://127.0.0.1:8000/manager/dashboard
   → 슈퍼 관리자: http://127.0.0.1:8000/super-admin?admin_token=YOUR_TOKEN
   ✨ SUPER_ADMIN 권한으로 모든 페이지 접근 가능!
\`\`\`

### 6단계: 접속 테스트

1. **로그인 페이지 접속**:
   \`\`\`
   https://marketing-analystics-573434207823.europe-west1.run.app/login
   \`\`\`

2. **로그인**:
   - 이메일: `kckc93@creatorcontrol.center`
   - 비밀번호: `Ckdgml9788@`

3. **대시보드 접속**:
   - https://marketing-analystics-573434207823.europe-west1.run.app/dashboard
   - https://marketing-analystics-573434207823.europe-west1.run.app/manager/dashboard

---

## 방법 2: Cloud Run Jobs 사용 (프로덕션 권장)

일회성 작업을 Cloud Run Jobs로 실행하는 방법입니다.

### 1단계: Cloud Run Job 생성

\`\`\`bash
# gcloud CLI에서 실행

gcloud run jobs create create-accounts \
  --image gcr.io/YOUR_PROJECT_ID/marketing-analystics \
  --region europe-west1 \
  --set-env-vars DATABASE_URL="your_database_url" \
  --command python3 \
  --args create_test_accounts.py
\`\`\`

### 2단계: Job 실행

\`\`\`bash
# Job 실행
gcloud run jobs execute create-accounts --region europe-west1

# 로그 확인
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=create-accounts" \
  --limit 50 \
  --format "table(timestamp, textPayload)"
\`\`\`

### 3단계: Job 삭제 (선택)

\`\`\`bash
# 계정 생성 완료 후 Job 삭제
gcloud run jobs delete create-accounts --region europe-west1
\`\`\`

---

## 방법 3: Cloud Console UI에서 실행

UI를 통해 Cloud Shell에서 스크립트를 실행합니다.

### 상세 단계

#### 1. Cloud Console 접속
- https://console.cloud.google.com/ 접속
- 프로젝트 선택

#### 2. Cloud Shell 활성화
- 우측 상단 **Cloud Shell 아이콘** (>_) 클릭
- 터미널 화면이 하단에 나타남

#### 3. 환경 변수 가져오기
\`\`\`bash
# Cloud Run 서비스의 환경 변수 확인
gcloud run services describe marketing-analystics \
  --region europe-west1 \
  --format="value(spec.template.spec.containers[0].env)"
\`\`\`

출력에서 DATABASE_URL 값을 복사합니다.

#### 4. 저장소 클론
\`\`\`bash
git clone https://github.com/Kimchanghee/marketing_analystics.git
cd marketing_analystics
\`\`\`

#### 5. 환경 변수 설정
\`\`\`bash
# 복사한 DATABASE_URL 값 사용
export DATABASE_URL="여기에_DATABASE_URL_값_붙여넣기"
\`\`\`

#### 6. 의존성 설치
\`\`\`bash
pip3 install -r requirements.txt
\`\`\`

#### 7. 스크립트 실행
\`\`\`bash
python3 create_test_accounts.py
\`\`\`

#### 8. 결과 확인
성공하면 4개의 계정이 생성됩니다:
- creator@test.com
- manager@test.com
- admin@test.com
- kckc93@creatorcontrol.center ⭐ (마스터 관리자)

---

## 문제 해결

### 문제 1: DATABASE_URL을 모르겠어요

**해결 방법 A - Cloud Console UI**:
1. https://console.cloud.google.com/run/detail/europe-west1/marketing-analystics
2. "Variables & Secrets" 탭 클릭
3. DATABASE_URL 값 확인

**해결 방법 B - gcloud CLI**:
\`\`\`bash
gcloud run services describe marketing-analystics \
  --region europe-west1 \
  --format="value(spec.template.spec.containers[0].env)"
\`\`\`

### 문제 2: ModuleNotFoundError

**원인**: Python 패키지가 설치되지 않음

**해결**:
\`\`\`bash
pip3 install -r requirements.txt
\`\`\`

### 문제 3: Database Connection Error

**원인**: DATABASE_URL이 잘못되었거나 Cloud SQL 접근 권한 없음

**해결**:

**A. Cloud SQL 연결 설정 확인**:
\`\`\`bash
# Cloud SQL 인스턴스 확인
gcloud sql instances list

# 연결 이름 확인
gcloud sql instances describe INSTANCE_NAME
\`\`\`

**B. Cloud SQL Proxy 사용** (외부 데이터베이스가 아닌 경우):
\`\`\`bash
# Cloud SQL Proxy 설치
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy

# Proxy 실행 (별도 터미널)
./cloud_sql_proxy -instances=PROJECT:REGION:INSTANCE=tcp:5432

# 다른 터미널에서 스크립트 실행
export DATABASE_URL="postgresql://user:password@127.0.0.1:5432/database"
python3 create_test_accounts.py
\`\`\`

**C. IP 허용 목록 확인** (외부 데이터베이스 사용 시):
- 데이터베이스 방화벽에서 Cloud Shell IP 허용
- Cloud Shell IP 확인: `curl ifconfig.me`

### 문제 4: "계정이 이미 존재합니다" 메시지

**원인**: 계정이 이미 생성되어 있음 (정상)

**확인**: 로그인 시도해보기
- https://marketing-analystics-573434207823.europe-west1.run.app/login

**재생성 필요 시**:
데이터베이스에서 기존 계정 삭제 후 다시 실행하거나, 다른 이메일로 계정 생성

### 문제 5: Permission Denied

**원인**: Cloud SQL 접근 권한 없음

**해결**:
\`\`\`bash
# 현재 사용자 확인
gcloud auth list

# Cloud SQL Admin 권한 추가
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:YOUR_EMAIL" \
  --role="roles/cloudsql.client"
\`\`\`

---

## 계정 확인 방법

### 데이터베이스에서 직접 확인

#### Cloud SQL인 경우:
\`\`\`bash
# Cloud Shell에서 실행
gcloud sql connect INSTANCE_NAME --user=postgres

# SQL 쿼리
SELECT email, name, role FROM user;
\`\`\`

#### PostgreSQL 외부 데이터베이스:
\`\`\`bash
# Cloud Shell에서 psql 설치
sudo apt-get update && sudo apt-get install -y postgresql-client

# 데이터베이스 접속
psql "$DATABASE_URL"

# 계정 확인 쿼리
SELECT email, name, role, is_active FROM "user";
\`\`\`

---

## 완료 체크리스트

계정 생성이 완료되었는지 확인:

- [ ] Cloud Shell에서 스크립트 실행 성공
- [ ] "✅ 마스터 관리자 계정 생성 완료" 메시지 확인
- [ ] 로그인 페이지 접속 가능
- [ ] kckc93@creatorcontrol.center로 로그인 성공
- [ ] /dashboard 접속 가능
- [ ] /manager/dashboard 접속 가능

모든 항목이 체크되면 성공입니다!

---

## 요약: 가장 빠른 방법

\`\`\`bash
# 1. Cloud Console에서 Cloud Shell 열기 (우측 상단 >_ 아이콘)

# 2. 환경 변수 확인
gcloud run services describe marketing-analystics \
  --region europe-west1 \
  --format="value(spec.template.spec.containers[0].env)" | grep DATABASE_URL

# 3. 저장소 클론 및 설정
git clone https://github.com/Kimchanghee/marketing_analystics.git
cd marketing_analystics
export DATABASE_URL="복사한_DATABASE_URL_값"

# 4. 패키지 설치 및 실행
pip3 install -r requirements.txt
python3 create_test_accounts.py

# 5. 로그인 테스트
# https://marketing-analystics-573434207823.europe-west1.run.app/login
# 이메일: kckc93@creatorcontrol.center
# 비밀번호: Ckdgml9788@
\`\`\`

**예상 소요 시간**: 5-10분
