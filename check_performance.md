# Cloud Run 로딩 속도 체크 및 개선 가이드

## 1. Cloud Shell에서 로딩 속도 체크 방법

### A. Cloud Run 로그 확인
```bash
# 최근 100개 로그 확인
gcloud run services logs read marketing-analytics \
  --region=asia-northeast3 \
  --limit=100

# 특정 시간대 로그 확인 (느린 요청 찾기)
gcloud run services logs read marketing-analytics \
  --region=asia-northeast3 \
  --limit=500 \
  --format="table(timestamp,severity,textPayload)" \
  | grep -E "(slow|timeout|error)"
```

### B. 응답 시간 측정
```bash
# 여러 번 요청해서 평균 속도 측정
for i in {1..10}; do
  echo "Request $i:"
  time curl -s -o /dev/null -w "Time: %{time_total}s\n" https://YOUR_CLOUD_RUN_URL.a.run.app
done

# 더 자세한 타이밍 정보
curl -w "@-" -o /dev/null -s https://YOUR_CLOUD_RUN_URL.a.run.app <<'EOF'
    time_namelookup:  %{time_namelookup}s\n
       time_connect:  %{time_connect}s\n
    time_appconnect:  %{time_appconnect}s\n
   time_pretransfer:  %{time_pretransfer}s\n
      time_redirect:  %{time_redirect}s\n
 time_starttransfer:  %{time_starttransfer}s\n
                    ----------\n
         time_total:  %{time_total}s\n
EOF
```

### C. Cloud Run 메트릭 확인
```bash
# 컨테이너 인스턴스 상태 확인
gcloud run services describe marketing-analytics \
  --region=asia-northeast3 \
  --format="yaml(status)"

# 현재 실행 중인 인스턴스 수
gcloud run services describe marketing-analytics \
  --region=asia-northeast3 \
  --format="value(status.traffic[0].latestRevision)"
```

### D. Python 프로파일링 스크립트
```bash
# performance_test.py 생성
cat > performance_test.py << 'EOF'
import requests
import time
import statistics

url = "https://YOUR_CLOUD_RUN_URL.a.run.app"
times = []

print("Testing 10 requests...")
for i in range(10):
    start = time.time()
    response = requests.get(url)
    elapsed = time.time() - start
    times.append(elapsed)
    print(f"Request {i+1}: {elapsed:.2f}s - Status: {response.status_code}")

print(f"\n평균: {statistics.mean(times):.2f}s")
print(f"최소: {min(times):.2f}s")
print(f"최대: {max(times):.2f}s")
print(f"중간값: {statistics.median(times):.2f}s")
EOF

python performance_test.py
```

## 2. 로딩이 느린 주요 원인

### A. Cold Start (콜드 스타트)
- **증상**: 첫 요청이 5-10초 이상 걸림
- **확인 방법**:
```bash
# 로그에서 cold start 확인
gcloud run services logs read marketing-analytics \
  --region=asia-northeast3 | grep "cold"
```

### B. 데이터베이스 쿼리
- **증상**: 로그인 후 대시보드 로딩이 느림
- **확인 방법**:
```bash
# 앱에 타이밍 로그 추가 필요
# 아래 코드를 main.py에 추가
```

### C. 외부 API 호출
- **증상**: 특정 페이지만 느림
- **확인**: OAuth, Gemini API 호출 시간

## 3. 개선 방법

### A. Cold Start 개선

#### 1) 최소 인스턴스 설정 (비용 발생)
```bash
gcloud run services update marketing-analytics \
  --region=asia-northeast3 \
  --min-instances=1
```

#### 2) CPU 항상 할당 (비용 발생)
```bash
gcloud run services update marketing-analytics \
  --region=asia-northeast3 \
  --cpu-always-allocated
```

#### 3) 가벼운 베이스 이미지 사용
```dockerfile
# Dockerfile 수정
FROM python:3.11-slim  # 현재
# 더 가벼운 옵션
FROM python:3.11-alpine
```

### B. 데이터베이스 최적화

#### 1) 쿼리 최적화 추가
```python
# app/routers/dashboard.py에 추가
from sqlmodel import select
from sqlalchemy.orm import selectinload

# 기존 코드
accounts = session.exec(select(SocialMediaAccount)).all()

# 개선 코드 (관계 미리 로드)
accounts = session.exec(
    select(SocialMediaAccount)
    .options(selectinload(SocialMediaAccount.credential))
).all()
```

#### 2) 인덱스 확인
```bash
# SQLite는 자동 인덱스가 있지만, 확인 필요
sqlite3 analytics.db "SELECT * FROM sqlite_master WHERE type='index';"
```

### C. 로딩 속도 모니터링 추가

#### app/middleware.py 생성
```python
from fastapi import Request
import time
import logging

logger = logging.getLogger(__name__)

async def log_request_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path} "
        f"completed in {process_time:.2f}s"
    )

    response.headers["X-Process-Time"] = str(process_time)
    return response
```

#### app/main.py에 적용
```python
from app.middleware import log_request_time

app.middleware("http")(log_request_time)
```

### D. 정적 파일 최적화

#### 1) CSS/JS 압축
```bash
# 빌드 시 자동 압축 (선택사항)
pip install csscompressor jsmin
```

#### 2) 이미지 최적화
```bash
# SVG는 이미 최적화되어 있으므로 PNG/JPG만
# 필요시 tinypng.com 사용
```

### E. 비동기 작업 최적화

```python
# app/services/data_fetcher.py
import asyncio

# 기존 동기 코드를 비동기로 변경
async def fetch_all_snapshots(accounts):
    tasks = [fetch_snapshot(account) for account in accounts]
    return await asyncio.gather(*tasks)
```

## 4. 즉시 적용 가능한 개선 (무료)

### 1) 로깅 레벨 조정
```python
# app/main.py
import logging
logging.basicConfig(level=logging.WARNING)  # INFO -> WARNING
```

### 2) 불필요한 데이터 쿼리 제거
```python
# 대시보드에서 사용하지 않는 데이터는 로드하지 않기
# 예: recent_posts가 필요 없으면 제외
```

### 3) 캐싱 추가
```python
from functools import lru_cache
from datetime import datetime, timedelta

_cache = {}
_cache_time = {}

def cached_snapshot(account_id):
    now = datetime.now()
    if account_id in _cache:
        if now - _cache_time[account_id] < timedelta(minutes=5):
            return _cache[account_id]

    # 새로 가져오기
    snapshot = get_snapshot(account_id)
    _cache[account_id] = snapshot
    _cache_time[account_id] = now
    return snapshot
```

## 5. 실시간 모니터링 설정

```bash
# Cloud Run 메트릭을 실시간으로 확인
gcloud run services describe marketing-analytics \
  --region=asia-northeast3 \
  --format="yaml(status.conditions)" \
  | watch -n 5

# 로그 실시간 스트리밍
gcloud run services logs tail marketing-analytics \
  --region=asia-northeast3
```

## 6. 권장 순서

1. **즉시**: 로그 확인하여 병목 지점 파악
2. **5분**: 미들웨어 추가하여 각 요청 시간 측정
3. **10분**: 데이터베이스 쿼리 최적화 (selectinload)
4. **30분**: 캐싱 추가
5. **비용 허용 시**: 최소 인스턴스 1개 설정

## 7. 체크리스트

- [ ] 로그에서 slow query 확인
- [ ] Cold start 빈도 확인
- [ ] 각 페이지별 로딩 시간 측정
- [ ] 데이터베이스 쿼리 수 확인
- [ ] 외부 API 호출 시간 확인
- [ ] 정적 파일 크기 확인
- [ ] 메모리 사용량 확인
