# Comet AI - Gmail SMTP 이메일 서비스 배포 프롬프트

> 이 프롬프트를 Comet AI 웹 인터페이스에 복사해서 붙여넣으세요.

---

## 📋 Comet AI에게 전달할 프롬프트

```
Gmail SMTP 이메일 서비스를 Cloud Run에 배포해줘. 다음 순서대로 진행해:

### 1단계: 프로젝트 및 서비스 확인

먼저 현재 설정을 확인해줘:

```bash
# GCP 프로젝트 ID 확인
gcloud config get-value project

# Cloud Run 서비스 목록 확인
gcloud run services list --region asia-northeast3
```

### 2단계: Cloud Run 환경 변수 설정

메인 서비스에 다음 환경 변수를 추가해줘 (SERVICE_NAME은 1단계에서 확인한 서비스명 사용):

```bash
gcloud run services update SERVICE_NAME \
  --update-env-vars SMTP_HOST=smtp.gmail.com \
  --update-env-vars SMTP_PORT=587 \
  --update-env-vars SUPER_ADMIN_EMAIL=kckc93@creatorscontrol.com \
  --update-env-vars SUPER_ADMIN_EMAIL_PASSWORD=앱비밀번호16자리여기입력 \
  --update-env-vars IMAP_HOST=imap.gmail.com \
  --update-env-vars IMAP_PORT=993 \
  --region asia-northeast3
```

**⚠️ 중요**: `SUPER_ADMIN_EMAIL_PASSWORD` 값은 내가 따로 알려줄게. 일단 이 명령어 준비만 해둬.

### 3단계: 환경 변수 설정 확인

설정이 제대로 적용됐는지 확인해줘:

```bash
gcloud run services describe SERVICE_NAME \
  --region asia-northeast3 \
  --format="value(spec.template.spec.containers[0].env)"
```

### 4단계: 배포 상태 확인

서비스가 정상 배포됐는지 확인해줘:

```bash
# 서비스 상태 확인
gcloud run services describe SERVICE_NAME --region asia-northeast3

# 최근 로그 확인 (에러 있는지 체크)
gcloud run services logs read SERVICE_NAME --region asia-northeast3 --limit 50
```

### 5단계: 테스트 안내

배포가 완료되면 나에게 다음 정보를 알려줘:

1. 배포된 서비스 URL
2. 환경 변수가 제대로 설정됐는지 확인 결과
3. 로그에 에러가 있는지 확인 결과

그러면 내가 직접 슈퍼 관리자 페이지에서 테스트해볼게:
- URL: https://creatorscontrol.com/super-admin
- 로그인: kckc93@creatorscontrol.com / Ckdgml9788@
- "슈퍼 관리자 메일" 탭에서 테스트 메일 발송

혹시 문제가 발생하면 상세 로그를 보여줘.
```

---

## 🔑 사용자가 먼저 준비할 것

### Gmail 앱 비밀번호 생성

1. **https://myaccount.google.com/apppasswords** 접속
2. **kckc93@creatorscontrol.com** 계정으로 로그인
   - Google Workspace 도메인 이메일이라면 그대로 진행
   - 일반 Gmail 계정이라면 kckc93@gmail.com 사용
3. **2단계 인증 활성화** (아직 안 했다면):
   - https://myaccount.google.com/security
   - "2단계 인증" → "사용 설정"
4. **앱 비밀번호 생성**:
   - "앱 선택" → "메일" 선택
   - "기기 선택" → "기타" 선택 → "Creator Control Center" 입력
   - 생성 버튼 클릭
5. **16자리 비밀번호 복사** (예: `abcd efgh ijkl mnop`)
   - ⚠️ 공백 제거: `abcdefghijklmnop` (16자)

### Comet AI에게 전달할 정보

앱 비밀번호를 생성했으면 Comet AI에게 다음과 같이 알려주세요:

```
앱 비밀번호 생성 완료했어. 다음 정보로 설정해줘:

SUPER_ADMIN_EMAIL_PASSWORD: abcdefghijklmnop

위 값으로 2단계 환경 변수 설정 명령어를 실행해줘.
```

---

## 🧪 배포 후 테스트 절차

Comet AI가 배포를 완료하면:

### 1. 슈퍼 관리자 페이지 접속
- URL: https://creatorscontrol.com/super-admin
- 로그인: kckc93@creatorscontrol.com / Ckdgml9788@

### 2. 메일 연결 확인
- "슈퍼 관리자 메일" 탭 클릭
- 화면 상단에 "연결된 계정: kckc93@creatorscontrol.com" 표시되는지 확인

### 3. 테스트 메일 발송
- "테스트 메일 보내기" 버튼 클릭
- 본인 이메일 주소 입력
- 몇 초 내에 메일 수신 확인

### 4. 수신 테스트
- "수신함" 탭 클릭
- "새로고침" 버튼으로 메일 목록 동기화
- 최근 수신 메일 목록 확인

---

## ❌ 문제 발생 시 (Comet AI에게 요청)

### SMTP 인증 실패
```
로그에 SMTP authentication failed 에러가 있어. 다음 확인해줘:

1. 환경 변수 SUPER_ADMIN_EMAIL_PASSWORD 값이 제대로 설정됐는지
2. 공백이 포함되지 않은 16자리인지 확인
3. 재배포가 필요하면 재배포해줘
```

### 메일 발송 실패
```
메일 발송이 안 돼. 최근 로그 100줄 보여줘:

gcloud run services logs read SERVICE_NAME --region asia-northeast3 --limit 100 --format="table(timestamp,severity,textPayload)"
```

### 환경 변수 재설정 필요
```
환경 변수를 다시 설정해야 할 것 같아. 다음 값으로 업데이트해줘:

SUPER_ADMIN_EMAIL_PASSWORD: 새로운16자리비밀번호
```

---

## 📝 참고 정보

### Gmail 발신 제한
- **무료 Gmail**: 하루 500통
- **Google Workspace**: 하루 2,000통

### 보안 체크리스트
- ✅ 2단계 인증 활성화됨
- ✅ 앱 비밀번호 사용 (계정 비밀번호 아님)
- ✅ HTTPS 연결만 허용
- ✅ Cloud Run 환경 변수로 안전하게 저장

### 유용한 명령어

```bash
# 서비스 전체 정보 확인
gcloud run services describe SERVICE_NAME --region asia-northeast3

# 실시간 로그 모니터링
gcloud run services logs tail SERVICE_NAME --region asia-northeast3

# 환경 변수만 조회
gcloud run services describe SERVICE_NAME --region asia-northeast3 --format="value(spec.template.spec.containers[0].env)"

# 서비스 재시작 (환경 변수 변경 후)
gcloud run services update SERVICE_NAME --region asia-northeast3 --platform managed
```

---

## ✅ 완료 체크리스트

- [ ] Gmail 앱 비밀번호 생성 완료 (16자리)
- [ ] Comet AI에게 프롬프트 전달
- [ ] Cloud Run 환경 변수 설정 완료
- [ ] 배포 완료 및 서비스 정상 작동 확인
- [ ] 슈퍼 관리자 페이지 접속 성공
- [ ] 테스트 메일 발송 및 수신 확인

---

**이제 위 프롬프트를 Comet AI 웹 인터페이스에 복사해서 붙여넣으면 됩니다!**
