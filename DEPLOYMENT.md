# Google Cloud Run 배포 가이드

## 현재 문제: Internal Server Error

Cloud Run에서 Internal Server Error가 발생하는 경우, 다음 단계로 문제를 해결하세요.

## 1단계: Cloud Run 로그 확인

### Google Cloud Console에서 로그 확인

1. **Google Cloud Console 접속**:
   - https://console.cloud.google.com/run/detail/europe-west1/marketing-analystics/logs

2. **로그 필터링**:
   - Severity: Error 선택
   - 최근 에러 메시지 확인

3. **일반적인 에러 원인**:
   - `ModuleNotFoundError`: 의존성 패키지 누락
   - `FileNotFoundError`: 파일 경로 문제
   - `DatabaseError`: 데이터베이스 연결 실패
   - 환경 변수 누락

### gcloud CLI로 로그 확인

```bash
# gcloud 설치 후
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 실시간 로그 스트리밍
gcloud run services logs read marketing-analystics \
  --region europe-west1 \
  --limit 50

# 에러만 필터링
gcloud run services logs read marketing-analystics \
  --region europe-west1 \
  --limit 50 \
  --log-filter="severity>=ERROR"
```

## 2단계: 최신 코드 재배포

최신 코드(SEO 모듈 포함)를 Cloud Run에 배포합니다.

### 방법 1: gcloud CLI 사용

```bash
# 프로젝트 루트 디렉토리에서 실행
cd /path/to/marketing_analystics

# 1. Docker 이미지 빌드 및 푸시
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/marketing-analystics

# 2. Cloud Run에 배포
gcloud run deploy marketing-analystics \
  --image gcr.io/YOUR_PROJECT_ID/marketing-analystics \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=YOUR_DATABASE_URL,SECRET_KEY=YOUR_SECRET_KEY,SUPER_ADMIN_ACCESS_TOKEN=YOUR_TOKEN"
```

### 방법 2: GitHub Actions (자동 배포)

`.github/workflows/deploy.yml` 파일을 생성하면 GitHub에 push할 때마다 자동으로 배포됩니다.

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Setup Cloud SDK
      uses: google-github-actions/setup-gcloud@v1
      with:
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        project_id: ${{ secrets.GCP_PROJECT_ID }}

    - name: Build and Push Docker Image
      run: |
        gcloud builds submit --tag gcr.io/${{ secrets.GCP_PROJECT_ID }}/marketing-analystics

    - name: Deploy to Cloud Run
      run: |
        gcloud run deploy marketing-analystics \
          --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/marketing-analystics \
          --platform managed \
          --region europe-west1 \
          --allow-unauthenticated \
          --set-env-vars "DATABASE_URL=${{ secrets.DATABASE_URL }},SECRET_KEY=${{ secrets.SECRET_KEY }},SUPER_ADMIN_ACCESS_TOKEN=${{ secrets.SUPER_ADMIN_TOKEN }}"
```

### 방법 3: Google Cloud Console UI

1. **Cloud Run 서비스 페이지 접속**:
   - https://console.cloud.google.com/run/detail/europe-west1/marketing-analystics

2. **"새 버전 수정 및 배포" 클릭**

3. **"Cloud Build를 사용하여 컨테이너 이미지 빌드" 선택**

4. **소스 저장소 연결**:
   - GitHub 저장소: `Kimchanghee/marketing_analystics`
   - Branch: `main`
   - Dockerfile: `/Dockerfile`

5. **환경 변수 설정** (중요!):
   ```
   DATABASE_URL=your_database_connection_string
   SECRET_KEY=your_secret_key
   SUPER_ADMIN_ACCESS_TOKEN=your_admin_token
   ```

6. **"배포" 클릭**

## 3단계: 환경 변수 확인

Cloud Run에 다음 환경 변수가 올바르게 설정되어 있는지 확인:

### 필수 환경 변수

```bash
# Cloud Run 환경 변수 확인
gcloud run services describe marketing-analystics \
  --region europe-west1 \
  --format="value(spec.template.spec.containers[0].env)"
```

### 필요한 환경 변수 목록

1. **DATABASE_URL**: PostgreSQL/MySQL 연결 문자열
   ```
   postgresql://user:password@host:port/database
   ```

2. **SECRET_KEY**: JWT 토큰 암호화 키
   ```
   openssl rand -hex 32
   ```

3. **SUPER_ADMIN_ACCESS_TOKEN**: 슈퍼 관리자 접근 토큰
   ```
   openssl rand -hex 32
   ```

4. **(선택) 소셜 로그인 키**:
   - GOOGLE_CLIENT_ID
   - GOOGLE_CLIENT_SECRET
   - APPLE_CLIENT_ID
   - APPLE_CLIENT_SECRET

### 환경 변수 업데이트

```bash
gcloud run services update marketing-analystics \
  --region europe-west1 \
  --set-env-vars "DATABASE_URL=new_value,SECRET_KEY=new_value"
```

## 4단계: 데이터베이스 마이그레이션

새로운 모델(ManagerAPIKey, CreatorInquiry 등)이 추가되었으므로 데이터베이스 테이블을 생성해야 합니다.

### Cloud Shell에서 마이그레이션 실행

```bash
# Cloud Shell 열기
# 프로젝트 클론
git clone https://github.com/Kimchanghee/marketing_analystics.git
cd marketing_analystics

# 환경 변수 설정
export DATABASE_URL="your_database_url"

# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 초기화 (테이블 생성)
python -c "from app.database import init_db; init_db()"

# 테스트 계정 생성
python create_test_accounts.py
```

## 5단계: Docker 로컬 테스트

배포 전에 로컬에서 Docker 이미지를 테스트할 수 있습니다.

```bash
# Docker 이미지 빌드
docker build -t marketing-analystics .

# 로컬에서 실행
docker run -p 8080:8080 \
  -e DATABASE_URL="your_database_url" \
  -e SECRET_KEY="your_secret_key" \
  -e SUPER_ADMIN_ACCESS_TOKEN="your_token" \
  marketing-analystics

# 브라우저에서 접속
# http://localhost:8080
```

## 6단계: 헬스 체크

배포 후 다음을 확인:

1. **홈페이지 접속**:
   ```
   curl https://marketing-analystics-573434207823.europe-west1.run.app/
   ```

2. **로그인 페이지**:
   ```
   curl https://marketing-analystics-573434207823.europe-west1.run.app/login
   ```

3. **Sitemap**:
   ```
   curl https://marketing-analystics-573434207823.europe-west1.run.app/sitemap.xml
   ```

4. **Robots.txt**:
   ```
   curl https://marketing-analystics-573434207823.europe-west1.run.app/robots.txt
   ```

## 일반적인 문제 해결

### 문제 1: ModuleNotFoundError

**원인**: requirements.txt의 패키지가 설치되지 않음

**해결**:
```bash
# requirements.txt 확인
cat requirements.txt

# 재배포
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/marketing-analystics
```

### 문제 2: FileNotFoundError (SEO JSON 파일)

**원인**: Docker 이미지에 app/seo/locales/ 폴더가 포함되지 않음

**해결**: Dockerfile에서 `COPY . .` 명령이 모든 파일을 복사하는지 확인

### 문제 3: Database Connection Error

**원인**: DATABASE_URL이 잘못되었거나 Cloud Run에서 데이터베이스에 접근할 수 없음

**해결**:
1. Cloud SQL을 사용하는 경우 Cloud SQL Proxy 설정
2. 외부 데이터베이스의 경우 방화벽에서 Cloud Run IP 허용
3. DATABASE_URL 형식 확인

### 문제 4: Internal Server Error (500)

**원인**: 코드 런타임 에러

**해결**:
1. Cloud Run 로그에서 정확한 에러 메시지 확인
2. 로컬에서 Docker 이미지 테스트
3. 환경 변수 누락 확인

## 빠른 재배포 명령

```bash
# 한 번에 빌드 + 배포
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/marketing-analystics && \
gcloud run deploy marketing-analystics \
  --image gcr.io/YOUR_PROJECT_ID/marketing-analystics \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated
```

## 도움이 필요한 경우

1. Cloud Run 로그 전체 내용 확인
2. 에러 메시지를 정확히 파악
3. 환경 변수가 모두 설정되어 있는지 확인
4. 데이터베이스 연결이 정상인지 확인
