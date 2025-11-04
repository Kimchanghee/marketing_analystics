# SendGrid 이메일 설정 가이드 - creatorscontrol.com

## 📧 설정 정보

- **도메인**: `creatorscontrol.com`
- **슈퍼관리자 이메일**: `admin@creatorscontrol.com`
- **테스트 수신 이메일**: `k931103@gmail.com`
- **SMTP 서버**: `smtp.sendgrid.net:587`

---

## 🚀 1단계: SendGrid Domain Authentication

### SendGrid 대시보드에서:

1. **Settings > Sender Authentication** 클릭
2. **"Authenticate Your Domain"** 섹션 선택
3. **"Get Started"** 버튼 클릭
4. 다음 정보 입력:
   - **Domain**: `creatorscontrol.com`
   - **Would you like to brand the link for this domain?**: **No** 선택
5. **"Next"** 버튼 클릭

---

## 🌐 2단계: DNS 레코드 추가

SendGrid가 3개의 CNAME 레코드를 생성합니다. 예시:

```
Type   Host/Name                              Value/Points to
────────────────────────────────────────────────────────────────────────────
CNAME  em1234                                 u12345.wl.sendgrid.net
CNAME  s1._domainkey                          s1.domainkey.u12345.wl.sendgrid.net
CNAME  s2._domainkey                          s2.domainkey.u12345.wl.sendgrid.net
```

### 도메인 등록업체에 DNS 레코드 추가

**creatorscontrol.com을 구매한 곳에 따라:**

#### GoDaddy:
1. My Products > Domains > `creatorscontrol.com` > Manage DNS
2. "Add" 버튼 클릭
3. Type: **CNAME** 선택
4. Host, Points to, TTL 입력
5. 3개의 레코드 모두 추가
6. Save

#### Cloudflare:
1. Dashboard > `creatorscontrol.com` > DNS
2. "Add record" 버튼 클릭
3. Type: **CNAME**, Name, Target 입력
4. **Proxy status: DNS only** (회색 구름) ⚠️ 중요!
5. 3개의 레코드 모두 추가
6. Save

#### Namecheap:
1. Domain List > `creatorscontrol.com` > Manage > Advanced DNS
2. "Add New Record" 버튼 클릭
3. Type: **CNAME Record**
4. Host, Value, TTL 입력
5. 3개의 레코드 모두 추가
6. Save

#### AWS Route 53:
1. Hosted zones > `creatorscontrol.com`
2. "Create record" 버튼 클릭
3. Record type: **CNAME**
4. Record name, Value 입력
5. 3개의 레코드 모두 추가
6. Create records

#### Google Domains:
1. My domains > `creatorscontrol.com` > DNS
2. Custom records > "Manage custom records"
3. "Create new record"
4. Type: **CNAME**, Host name, Data 입력
5. 3개의 레코드 모두 추가
6. Save

---

## ✅ 3단계: SendGrid 인증 확인

DNS 레코드 추가 후:

1. **SendGrid 화면으로 돌아가기**
2. **"Verify" 버튼 클릭**
3. DNS 전파 대기 (보통 10-30분, 최대 48시간)
4. ✅ **"Verified" 상태 확인**

⚠️ **즉시 인증 안 되면:**
- 10-30분 후 다시 "Verify" 클릭
- DNS 레코드가 정확한지 확인
- DNS 전파 확인: https://dnschecker.org/

---

## 🔑 4단계: SendGrid API 키 생성

1. **Settings > API Keys** 클릭
2. **"Create API Key"** 버튼 클릭
3. 입력:
   - **API Key Name**: `CreatorsControl SMTP`
   - **API Key Permissions**: **Restricted Access** 선택
   - 스크롤해서 **"Mail Send"** 찾기
   - **"Mail Send"**를 **"Full Access"**로 변경 (다른 권한은 No Access)
4. **"Create & View"** 버튼 클릭
5. ⚠️ **API 키 복사** (한 번만 표시됨!):
   ```
   SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

---

## ⚙️ 5단계: 로컬 환경 설정 (.env)

`.env` 파일을 다음과 같이 수정:

```env
# 슈퍼관리자 이메일 설정 (SendGrid)
SUPER_ADMIN_EMAIL=admin@creatorscontrol.com
SUPER_ADMIN_EMAIL_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USE_TLS=true

# IMAP 설정 (필요 없으면 그대로 둠)
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USE_SSL=true
IMAP_SENT_FOLDER=[Gmail]/Sent Mail
```

**⚠️ 중요:**
- `SUPER_ADMIN_EMAIL_PASSWORD`에 SendGrid API 키 전체를 붙여넣으세요
- `SG.`로 시작하는 전체 문자열

---

## ☁️ 6단계: Cloud Run 환경 변수 설정

### 방법 A: gcloud 명령어

```bash
gcloud run services update marketing-analystics \
  --region asia-northeast3 \
  --set-env-vars "SUPER_ADMIN_EMAIL=admin@creatorscontrol.com" \
  --set-env-vars "SUPER_ADMIN_EMAIL_PASSWORD=SG.xxxxxxxxxxxxxxxxx" \
  --set-env-vars "SMTP_HOST=smtp.sendgrid.net" \
  --set-env-vars "SMTP_PORT=587" \
  --set-env-vars "SMTP_USE_TLS=true"
```

### 방법 B: Cloud Console

1. https://console.cloud.google.com/run 접속
2. `marketing-analystics` 서비스 클릭
3. 상단의 **"새 버전 수정 및 배포"** 클릭
4. **"변수 및 보안 비밀"** 탭 선택
5. 다음 환경 변수 추가:
   - `SUPER_ADMIN_EMAIL`: `admin@creatorscontrol.com`
   - `SUPER_ADMIN_EMAIL_PASSWORD`: `SG.xxxxxxxxxxxxxxxxx`
   - `SMTP_HOST`: `smtp.sendgrid.net`
   - `SMTP_PORT`: `587`
   - `SMTP_USE_TLS`: `true`
6. **"배포"** 클릭

---

## 🧪 7단계: 테스트 이메일 발송

### 로컬 테스트:

```bash
python send_test_email.py
```

이메일이 `k931103@gmail.com`로 발송됩니다!

### Cloud Run에서 테스트:

1. 슈퍼관리자 페이지 접속
2. 이메일 발송 섹션에서 테스트 이메일 발송

---

## 📋 체크리스트

완료 여부를 확인하세요:

- [ ] SendGrid 계정 생성 완료
- [ ] Domain Authentication 설정 시작
- [ ] DNS CNAME 레코드 3개 추가 완료
- [ ] SendGrid에서 도메인 인증 완료 (Verified 상태)
- [ ] API 키 생성 및 복사 완료
- [ ] 로컬 .env 파일 업데이트 완료
- [ ] Cloud Run 환경 변수 설정 완료
- [ ] 로컬에서 테스트 이메일 발송 성공
- [ ] k931103@gmail.com에서 이메일 수신 확인

---

## 🔧 트러블슈팅

### 문제 1: DNS 인증이 안 됨

**확인 사항:**
1. DNS 레코드가 정확한지 확인
2. Cloudflare 사용 시 Proxy 끄기 (DNS only)
3. DNS 전파 확인: https://dnschecker.org/
4. 30분~1시간 후 다시 시도

### 문제 2: 이메일 발송 실패

**확인 사항:**
1. API 키가 정확한지 확인 (`SG.`로 시작)
2. Mail Send 권한이 Full Access인지 확인
3. 도메인 인증이 완료되었는지 확인
4. .env 파일 또는 Cloud Run 환경 변수 확인

### 문제 3: 이메일이 스팸함으로 감

**해결 방법:**
1. SendGrid Domain Authentication 완료 확인
2. SPF, DKIM 레코드 확인 (DNS)
3. 발송량 천천히 늘리기 (처음엔 소량)
4. 수신자가 스팸 해제 표시

---

## 📞 도움 필요 시

1. SendGrid 문서: https://docs.sendgrid.com/
2. DNS 전파 확인: https://dnschecker.org/
3. SendGrid 지원: https://support.sendgrid.com/

---

## 🎉 완료!

모든 설정이 완료되면:
- ✅ `admin@creatorscontrol.com`에서 이메일 발송 가능
- ✅ 스팸 필터 통과율 높음
- ✅ 하루 100통 무료 발송 가능
- ✅ 신뢰할 수 있는 발신자로 표시
