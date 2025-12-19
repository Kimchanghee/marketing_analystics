# 🚨 즉시 조치 필요 사항 (5분 가이드)

## 배포 전 필수 3단계

### 1️⃣ 보안 키 생성 및 설정 (2분)

```bash
# 터미널에서 실행
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('SUPER_ADMIN_ACCESS_TOKEN=' + secrets.token_urlsafe(32))"
```

출력 예시:
```
SECRET_KEY=xK7n9mP2qR5sT8vY1wZ4aB6cD3eF0gH9iJ2kL5mN8oP1qR4sT7uV0wX3yZ6
SUPER_ADMIN_ACCESS_TOKEN=aB9cD2eF5gH8iJ1kL4mN7oP0qR3sT6uV9wX2yZ5aC8bD1eF4gH7iJ0kL3m
```

**이 키들을 복사해 두세요!**

---

### 2️⃣ .env 파일 생성 (1분)

```bash
# .env.example을 .env로 복사
cp .env.example .env
```

`.env` 파일을 열고 위에서 생성한 키를 입력:
```bash
SECRET_KEY=<1단계에서_생성한_SECRET_KEY>
SUPER_ADMIN_ACCESS_TOKEN=<1단계에서_생성한_토큰>
```

---

### 3️⃣ app/config.py 수정 (2분)

**파일:** `app/config.py`

**변경 전:**
```python
secret_key: str = Field("super-secret-key", env="SECRET_KEY")
super_admin_access_token: str = Field("Ckdgml9788@", env="SUPER_ADMIN_ACCESS_TOKEN")
```

**변경 후:**
```python
secret_key: str = Field(..., env="SECRET_KEY")  # 기본값 제거!
super_admin_access_token: str = Field(..., env="SUPER_ADMIN_ACCESS_TOKEN")  # 기본값 제거!
```

`...`은 "필수 값"을 의미합니다. 이제 .env 파일이 없으면 서버가 시작되지 않습니다.

---

## ✅ 완료 확인

```bash
# 서버 시작 테스트
uvicorn app.main:app --reload
```

**에러가 나면 성공!** (아직 .env에 다른 값들을 설정 안 했으니까)
```
ValidationError: SECRET_KEY field required
```

이 메시지가 나오면 **정상**입니다. 이제 기본값으로 실행될 수 없습니다.

---

## 🎯 다음 단계

이제 두 가지 선택지가 있습니다:

### Option A: 즉시 런칭 (FastAPI + Jinja)
👉 **README_FIXES.md** → "즉시 런칭 원한다면" 섹션 참고

### Option B: Next.js로 개발 계속
👉 **DEPLOYMENT_DECISION.md** → "Option A" 섹션 참고

---

## 📞 문제 발생 시

### "SECRET_KEY not found" 에러
✅ 정상입니다! `.env` 파일에 키를 입력하세요.

### "module not found" 에러
```bash
pip install -r requirements.txt
```

### 서버가 시작 안 됨
```bash
# Python 가상환경 활성화 확인
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 의존성 재설치
pip install fastapi uvicorn sqlmodel pydantic-settings
```

---

## 🔒 절대 하지 말아야 할 것

❌ `.env` 파일을 git에 커밋
❌ 보안 키를 코드에 하드코딩
❌ `app.db` 파일을 git에 커밋
❌ 기본 비밀번호로 프로덕션 배포

---

**예상 소요 시간:** 5분
**난이도:** ⭐☆☆☆☆ (쉬움)
**중요도:** 🔴🔴🔴🔴🔴 (매우 높음)
