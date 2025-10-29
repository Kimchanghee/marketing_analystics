# Cloud Run 환경 변수 설정 가이드

## 🚨 중요: Internal Server Error 해결

"Internal Server Error"가 발생하는 주요 원인은 **환경 변수 미설정**입니다.

---

## 필수 환경 변수

### 1. DATABASE_URL (필수!)
PostgreSQL 데이터베이스 연결 문자열입니다.

```bash
DATABASE_URL=postgresql://username:password@host:port/database
```

**예시:**
```bash
DATABASE_URL=postgresql://myuser:mypassword@34.89.123.456:5432/marketing_db
```

⚠️ **Cloud Run은 읽기 전용 파일 시스템**이므로 SQLite를 사용할 수 없습니다!
반드시 PostgreSQL 또는 MySQL 같은 외부 데이터베이스를 사용해야 합니다.

### 2. SECRET_KEY (필수!)
JWT 토큰 생성에 사용되는 비밀 키입니다.

```bash
SECRET_KEY=your-super-secret-key-here-change-this-in-production
```

**생성 방법:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. ENVIRONMENT (권장)
배포 환경을 지정합니다.

```bash
ENVIRONMENT=production
```

- `production`: HTTPS secure 쿠키 활성화 (Cloud Run 기본값)
- `development`: HTTP용 쿠키 (로컬 개발용)

### 4. SUPER_ADMIN_ACCESS_TOKEN (선택)
슈퍼 관리자 페이지 접근 토큰입니다.

```bash
SUPER_ADMIN_ACCESS_TOKEN=Ckdgml9788@
```

### 5. GEMINI_API_KEY (선택)
AI 기능을 사용하려면 Google Gemini API 키가 필요합니다.

```bash
GEMINI_API_KEY=your-gemini-api-key-here
```

---

## Cloud Run에 환경 변수 설정하기

### 방법 1: gcloud 명령어로 설정

```bash
gcloud run services update marketing-analystics \
  --region europe-west1 \
  --set-env-vars "DATABASE_URL=postgresql://user:pass@host:port/db" \
  --set-env-vars "SECRET_KEY=your-secret-key-here" \
  --set-env-vars "ENVIRONMENT=production" \
  --set-env-vars "SUPER_ADMIN_ACCESS_TOKEN=Ckdgml9788@"
```

### 방법 2: Cloud Console에서 설정

1. [Cloud Run 콘솔](https://console.cloud.google.com/run) 접속
2. `marketing-analystics` 서비스 클릭
3. 상단의 **"새 버전 수정 및 배포"** 클릭
4. **"변수 및 보안 비밀"** 탭 선택
5. **"환경 변수"** 섹션에서 추가:
   - `DATABASE_URL`: `postgresql://...`
   - `SECRET_KEY`: `your-secret-key`
   - `ENVIRONMENT`: `production`
   - `SUPER_ADMIN_ACCESS_TOKEN`: `Ckdgml9788@`
6. **"배포"** 클릭

---

## PostgreSQL 데이터베이스 설정

### Google Cloud SQL 사용 (권장)

#### 1. Cloud SQL 인스턴스 생성
```bash
gcloud sql instances create marketing-db \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=europe-west1
```

#### 2. 데이터베이스 생성
```bash
gcloud sql databases create marketing_analytics \
  --instance=marketing-db
```

#### 3. 사용자 생성
```bash
gcloud sql users create dbuser \
  --instance=marketing-db \
  --password=your-secure-password
```

#### 4. Cloud Run에서 Cloud SQL 연결

**방법 A: Public IP 사용**
```bash
# Cloud SQL의 Public IP 확인
gcloud sql instances describe marketing-db --format="value(ipAddresses[0].ipAddress)"

# DATABASE_URL 설정
DATABASE_URL=postgresql://dbuser:your-password@PUBLIC_IP:5432/marketing_analytics
```

**방법 B: Unix Socket 사용 (권장)**
```bash
# Cloud Run에 Cloud SQL 연결 추가
gcloud run services update marketing-analystics \
  --region europe-west1 \
  --add-cloudsql-instances=PROJECT_ID:europe-west1:marketing-db

# DATABASE_URL 설정
DATABASE_URL=postgresql://dbuser:your-password@/marketing_analytics?host=/cloudsql/PROJECT_ID:europe-west1:marketing-db
```

### 외부 PostgreSQL 사용

외부 PostgreSQL을 사용하는 경우:
```bash
DATABASE_URL=postgresql://username:password@external-host.com:5432/database_name
```

---

## 현재 설정 확인하기

```bash
# 현재 환경 변수 확인
gcloud run services describe marketing-analystics \
  --region europe-west1 \
  --format="value(spec.template.spec.containers[0].env)"

# 서비스 상태 확인
gcloud run services describe marketing-analystics \
  --region europe-west1 \
  --format="value(status.url,status.conditions)"
```

---

## 로그 확인하기

Internal Server Error 발생 시 로그를 확인하세요:

```bash
# 실시간 로그 보기
gcloud run services logs tail marketing-analystics \
  --region europe-west1

# 최근 로그 50줄 보기
gcloud run services logs read marketing-analystics \
  --region europe-west1 \
  --limit=50
```

**중요한 로그 메시지:**
- `Database initialization failed`: DATABASE_URL 확인 필요
- `Invalid token`: SECRET_KEY 확인 필요
- `Connection refused`: 데이터베이스 연결 확인 필요

---

## 트러블슈팅

### 문제 1: "Internal Server Error" 계속 발생

**확인 사항:**
1. DATABASE_URL이 설정되어 있나요?
   ```bash
   gcloud run services describe marketing-analystics \
     --region europe-west1 \
     --format="value(spec.template.spec.containers[0].env)" | grep DATABASE_URL
   ```

2. PostgreSQL에 연결할 수 있나요?
   ```bash
   # 로컬에서 테스트
   psql "postgresql://user:pass@host:port/db"
   ```

3. 데이터베이스가 초기화되었나요?
   - 로그에서 "Database initialization completed successfully" 메시지 확인

### 문제 2: "Not authenticated" 계속 발생

**확인 사항:**
1. ENVIRONMENT=production으로 설정되어 있나요?
2. SECRET_KEY가 설정되어 있나요?
3. 쿠키가 브라우저에서 차단되지 않았나요? (시크릿 모드 테스트)

### 문제 3: 로그인 후 빈 페이지

**확인 사항:**
1. 데이터베이스에 User 테이블이 생성되었나요?
2. 테스트 계정이 생성되어 있나요?
   ```bash
   # Cloud Shell에서 컨테이너에 접속
   gcloud run services exec marketing-analystics --region europe-west1

   # Python 스크립트 실행
   python create_test_accounts.py
   ```

---

## 최소 설정 예시

```bash
# 최소한 이 두 개는 반드시 설정해야 합니다!
gcloud run services update marketing-analystics \
  --region europe-west1 \
  --set-env-vars "DATABASE_URL=postgresql://user:pass@host:port/db,SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

---

## 체크리스트

배포 전에 다음을 확인하세요:

- [ ] Cloud SQL 인스턴스 생성 완료
- [ ] 데이터베이스 생성 완료
- [ ] DATABASE_URL 환경 변수 설정 완료
- [ ] SECRET_KEY 환경 변수 설정 완료
- [ ] ENVIRONMENT=production 설정 완료
- [ ] Cloud Run 서비스 재배포 완료
- [ ] 로그에서 "Database initialization completed successfully" 확인
- [ ] 로그인 테스트 성공

---

## 도움이 필요하면

1. **로그 확인**: `gcloud run services logs tail marketing-analystics --region europe-west1`
2. **환경 변수 확인**: `gcloud run services describe marketing-analystics --region europe-west1`
3. **데이터베이스 연결 테스트**: 로컬에서 DATABASE_URL로 psql 연결 시도

문제가 계속되면 로그 전체를 공유해주세요!
