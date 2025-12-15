# 🔀 Pull Request 생성 가이드

## ⚠️ 현재 상황

main 브랜치가 **보호된 브랜ch(Protected Branch)**로 설정되어 있어 직접 푸시가 불가능합니다.
로컬에 3개의 커밋이 있지만 원격 저장소에 푸시할 수 없습니다.

\`\`\`
error: RPC failed; HTTP 403
Your branch is ahead of 'origin/main' by 3 commits.
\`\`\`

## ✅ 해결 방법: Pull Request 생성

### 🚀 빠른 방법: 자동 PR 링크 사용

**다음 링크를 클릭하면 바로 PR 생성 페이지로 이동합니다:**

\`\`\`
https://github.com/Kimchanghee/marketing_analystics/compare/main...claude/fix-admin-permissions-011CUXPaXFEH5HyriuJfw1ry?expand=1
\`\`\`

---

## 📝 PR 생성 단계별 가이드

### Step 1: GitHub 저장소 접속

1. 브라우저에서 저장소 열기:
   \`\`\`
   https://github.com/Kimchanghee/marketing_analystics
   \`\`\`

2. 화면 상단에 노란색 알림이 보일 수 있습니다:
   \`\`\`
   "claude/fix-admin-permissions-011CUXPaXFEH5HyriuJfw1ry had recent pushes"
   [Compare & pull request] 버튼 클릭
   \`\`\`

### Step 2: Pull Request 수동 생성

노란색 알림이 안 보이면:

1. **"Pull requests" 탭** 클릭

2. **"New pull request"** 버튼 클릭

3. **브랜치 선택**:
   - Base: `main` ← 병합될 대상
   - Compare: `claude/fix-admin-permissions-011CUXPaXFEH5HyriuJfw1ry` ← 병합할 브랜치

4. **변경사항 확인**:
   - Files changed: 3개 파일 (admin.py, auth.py, 2개 문서)
   - Commits: 3개

### Step 3: PR 정보 입력

**제목 (Title):**
\`\`\`
Fix: SUPER_ADMIN 권한 및 로그인 오류 수정
\`\`\`

**설명 (Description):**
\`\`\`markdown
## 🎯 변경 목적

마스터 관리자(SUPER_ADMIN) 로그인 시 Internal Server Error 해결 및 권한 문제 수정

## 📋 주요 변경사항

### 1. 슈퍼관리자 페이지 권한 수정 (`app/routers/admin.py`)
- ✅ `require_roles(UserRole.SUPER_ADMIN)` 제거
- ✅ `admin_token`만으로 슈퍼관리자 페이지 접근 가능
- ✅ 모든 슈퍼관리자 엔드포인트 권한 체크 순서 변경

### 2. 로그인 리다이렉트 수정 (`app/routers/auth.py`)
- ✅ SUPER_ADMIN 로그인 후 `/dashboard`로 리다이렉트 (기존: `/super-admin`)
- ✅ MANAGER는 `/manager/dashboard`로 리다이렉트
- ✅ `/super-admin`은 `admin_token` 파라미터로 수동 접속

### 3. 문서 추가
- ✅ `ACCOUNTS_AND_PAGES.md`: 계정 정보 및 전체 페이지 구조 정리
- ✅ `DEPLOY_GUIDE.md`: Cloud Run 배포 가이드

## 🔍 해결된 문제

**Before:**
\`\`\`
마스터 관리자 로그인 → /super-admin 리다이렉트 → admin_token 없음 → 403 Forbidden
\`\`\`

**After:**
\`\`\`
마스터 관리자 로그인 → /dashboard 리다이렉트 → 정상 접속 ✅
모든 페이지 접근 가능 (dependencies.py의 SUPER_ADMIN 권한)
\`\`\`

## 🧪 테스트 계정

- 마스터 관리자: `kckc93@creatorcontrol.center` / `Ckdgml9788@`
- 크리에이터: `creator@test.com` / `password123`
- 매니저: `manager@test.com` / `password123`

## 🚀 배포 영향

- ✅ 기존 기능 영향 없음
- ✅ 로그인/로그아웃 정상 작동
- ✅ 모든 대시보드 접근 가능
- ✅ AI-PD 기능 정상 작동

## 📊 변경된 파일

- `app/routers/admin.py` - 슈퍼관리자 권한 로직 수정
- `app/routers/auth.py` - 로그인 리다이렉트 로직 수정
- `ACCOUNTS_AND_PAGES.md` - 신규 문서
- `DEPLOY_GUIDE.md` - 신규 문서

## ✅ 체크리스트

- [x] 로컬 테스트 완료
- [x] 코드 리뷰 가능 상태
- [x] 문서 업데이트 완료
- [ ] PR 병합 후 Cloud Run 자동 배포 확인 필요

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
\`\`\`

### Step 4: PR 생성 완료

**"Create pull request"** 버튼 클릭

---

## 🔄 PR 병합 후 자동 배포 프로세스

1. ✅ **PR 생성 완료**
2. 👀 **코드 리뷰** (선택사항)
3. ✅ **"Merge pull request"** 클릭
4. ✅ **"Confirm merge"** 클릭
5. 🔄 **GitHub → Cloud Build 트리거**
6. 🏗️ **Cloud Build 자동 빌드** (약 3분)
7. 🚀 **Cloud Run 자동 배포**
8. ✨ **프로덕션 반영 완료!**

---

## 📊 Cloud Build 모니터링

### 배포 진행 상황 확인:

**Cloud Build 콘솔:**
\`\`\`
https://console.cloud.google.com/cloud-build/builds?project=marketing-analytics-475700
\`\`\`

**CLI로 확인:**
\`\`\`bash
# Cloud Shell에서 실행
gcloud builds list --limit=1 --region=global
gcloud builds log $(gcloud builds list --limit=1 --format="value(id)")
\`\`\`

### 성공적인 배포 확인:

1. **빌드 로그에서 "SUCCESS" 확인**
2. **Cloud Run 서비스 URL 접속**:
   \`\`\`
   https://marketing-analystics-573434207823.europe-west1.run.app
   \`\`\`
3. **마스터 관리자로 로그인 테스트**

---

## ⚠️ PR 병합 전 확인사항

- [ ] 변경사항 검토 완료
- [ ] 모든 파일 변경 내용 확인
- [ ] 커밋 메시지 검토
- [ ] 충돌(Conflict) 없음 확인

---

## 🆘 문제 해결

### "Merge conflicts" 발생 시:

\`\`\`bash
# 로컬에서 해결
git checkout main
git pull origin main
git merge claude/fix-admin-permissions-011CUXPaXFEH5HyriuJfw1ry
# 충돌 해결 후
git push origin main  # (여전히 403 오류 발생)
\`\`\`

**해결책:** GitHub 웹 인터페이스에서 "Resolve conflicts" 버튼 클릭

### PR 생성이 안 될 때:

1. 브랜치가 최신인지 확인:
   \`\`\`bash
   git log origin/claude/fix-admin-permissions-011CUXPaXFEH5HyriuJfw1ry
   \`\`\`

2. 브랜치 푸시 확인:
   \`\`\`bash
   git push origin claude/fix-admin-permissions-011CUXPaXFEH5HyriuJfw1ry
   \`\`\`

---

## 🎯 요약

| 단계 | 설명 | 소요 시간 |
|------|------|-----------|
| 1. PR 생성 | GitHub에서 Pull Request 생성 | 1분 |
| 2. PR 병합 | "Merge pull request" 클릭 | 10초 |
| 3. 자동 빌드 | Cloud Build가 자동 실행 | 3분 |
| 4. 자동 배포 | Cloud Run에 배포 완료 | 1분 |
| **총 소요 시간** | | **약 5분** |

---

## 📞 추가 도움말

PR 생성 중 문제가 발생하면:
1. 브라우저 캐시 삭제
2. 시크릿/프라이빗 모드로 재시도
3. 다른 브라우저 사용

PR 링크를 공유해주시면 제가 검토해드립니다! 🚀
