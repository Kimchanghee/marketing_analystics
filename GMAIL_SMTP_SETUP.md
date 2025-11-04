# Gmail SMTP 이메일 서비스 설정 가이드

## 📋 Comet AI에게 시킬 프롬프트

```
다음 순서대로 Gmail SMTP 이메일 서비스를 설정하고 Cloud Run에 배포해줘:

## 1단계: Gmail 앱 비밀번호 생성
내가 직접 할게. 완료되면 앱 비밀번호를 알려줄게.

## 2단계: Cloud Run 환경 변수 설정
다음 명령어를 실행해서 Cloud Run 서비스에 환경 변수를 추가해줘:

```bash
# 프로젝트 ID 확인
gcloud config get-value project

# Cloud Run 서비스명 확인
gcloud run services list

# 환경 변수 설정 (아래 값들은 내가 제공할게)
gcloud run services update SERVICE_NAME \
  --update-env-vars SMTP_HOST=smtp.gmail.com \
  --update-env-vars SMTP_PORT=587 \
  --update-env-vars SUPER_ADMIN_EMAIL=kckc93@creatorscontrol.com \
  --update-env-vars SUPER_ADMIN_EMAIL_PASSWORD=앱비밀번호여기 \
  --update-env-vars IMAP_HOST=imap.gmail.com \
  --update-env-vars IMAP_PORT=993 \
  --region asia-northeast3

# 설정 확인
gcloud run services describe SERVICE_NAME --region asia-northeast3 --format="value(spec.template.spec.containers[0].env)"
```

## 3단계: 배포 확인
배포가 완료되면 다음을 확인해줘:
1. https://creatorscontrol.com/super-admin 접속
2. 로그인 (kckc93@creatorscontrol.com / Ckdgml9788@)
3. "슈퍼 관리자 메일" 탭에서 테스트 메일 발송
4. 수신 확인

문제가 발생하면 로그를 확인하고 알려줘:
```bash
gcloud run services logs read SERVICE_NAME --region asia-northeast3 --limit 50
```
```

---

## 🔑 사용자가 직접 해야 할 일 (1단계)

### ⚠️ 중요: 이메일 계정 확인

**kckc93@creatorscontrol.com이 어떤 계정인지 확인하세요:**

#### 케이스 A: Google Workspace 도메인 이메일인 경우
- ✅ **그대로 사용 가능**
- creatorscontrol.com 도메인을 Google Workspace로 관리 중이면 OK
- kckc93@creatorscontrol.com으로 Gmail에 로그인 가능하면 이 케이스

**앱 비밀번호 생성 방법:**
1. https://myaccount.google.com/apppasswords 접속
2. kckc93@creatorscontrol.com 계정으로 로그인
3. 앱 비밀번호 생성 → "메일" 선택
4. 생성된 16자리 비밀번호 복사 (예: `abcd efgh ijkl mnop`)

#### 케이스 B: 일반 Gmail 계정을 사용해야 하는 경우
- ⚠️ **kckc93@gmail.com 같은 Gmail 계정 필요**
- creatorscontrol.com이 Google Workspace가 아닌 경우
- 일반 Gmail 계정으로 SMTP 인증 후 발신자명만 변경 가능

**앱 비밀번호 생성 방법:**
1. https://myaccount.google.com/apppasswords 접속
2. Gmail 계정(예: kckc93@gmail.com)으로 로그인
3. **2단계 인증이 꺼져있으면 먼저 활성화:**
   - https://myaccount.google.com/security
   - "2단계 인증" → "사용 설정"
4. 다시 앱 비밀번호로 돌아가서 생성 → "메일" 선택
5. 생성된 16자리 비밀번호 복사

**환경 변수는 다음으로 변경:**
```bash
--update-env-vars SUPER_ADMIN_EMAIL=kckc93@gmail.com \
--update-env-vars SUPER_ADMIN_EMAIL_PASSWORD=앱비밀번호 \
```

---

## 📌 Comet AI에게 전달할 정보

앱 비밀번호를 생성한 후 Comet AI에게 다음 정보를 제공하세요:

```
앱 비밀번호 생성 완료! 다음 정보로 설정해줘:

SERVICE_NAME: [Cloud Run 서비스명]
SUPER_ADMIN_EMAIL: kckc93@creatorscontrol.com (또는 kckc93@gmail.com)
SUPER_ADMIN_EMAIL_PASSWORD: [16자리 앱 비밀번호]
```

---

## 🧪 테스트 방법

배포 후 다음 순서로 테스트:

1. **슈퍼 관리자 페이지 접속**
   - URL: https://creatorscontrol.com/super-admin
   - 로그인: kckc93@creatorscontrol.com / Ckdgml9788@

2. **메일 탭 확인**
   - "슈퍼 관리자 메일" 탭 클릭
   - "연결된 계정" 표시 확인

3. **테스트 메일 발송**
   - "테스트 메일 보내기" 버튼 클릭
   - 본인 이메일로 수신 확인

4. **수신 테스트**
   - "수신함" 탭에서 메일 목록 확인
   - "새로고침" 버튼으로 동기화

---

## ❌ 문제 해결

### 1. "앱 비밀번호" 메뉴가 안 보임
→ **2단계 인증을 먼저 활성화**하세요:
- https://myaccount.google.com/security
- "2단계 인증" → "사용 설정"

### 2. SMTP 인증 실패
→ **앱 비밀번호 공백 제거**:
- `abcd efgh ijkl mnop` → `abcdefghijklmnop` (16자)

### 3. Gmail에서 차단됨
→ **"보안 수준이 낮은 앱" 허용** (구형 Gmail만 해당):
- https://myaccount.google.com/lesssecureapps

### 4. 발신 제한
- Gmail 무료: 하루 500통
- Google Workspace: 하루 2,000통

---

## 🎯 요약

1. **사용자**: Gmail 앱 비밀번호 생성
2. **Comet AI**: Cloud Run 환경 변수 설정 + 배포
3. **사용자**: 슈퍼 관리자 페이지에서 테스트

이제 위 프롬프트를 Comet AI에게 복사해서 전달하세요!
