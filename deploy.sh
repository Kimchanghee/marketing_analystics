#!/bin/bash
# 🚀 Marketing Analytics 자동 배포 스크립트
# Cloud Shell에서 이 파일을 실행하면 자동으로 배포됩니다.

set -e  # 오류 발생 시 중단

echo "🚀 Marketing Analytics 배포 시작..."
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 프로젝트 설정
PROJECT_ID="marketing-analytics-475700"
SERVICE_NAME="marketing-analystics"
REGION="europe-west1"
BRANCH="claude/fix-admin-permissions-011CUXPaXFEH5HyriuJfw1ry"

echo "📋 설정 정보:"
echo "  프로젝트: $PROJECT_ID"
echo "  서비스: $SERVICE_NAME"
echo "  리전: $REGION"
echo "  브랜치: $BRANCH"
echo ""

# Step 1: 프로젝트 디렉토리 준비
echo "📁 Step 1/5: 프로젝트 디렉토리 준비 중..."
cd ~

if [ -d "marketing_analystics" ]; then
    echo "  기존 디렉토리 발견, 업데이트 중..."
    cd marketing_analystics
    git fetch origin
    git checkout $BRANCH
    git pull origin $BRANCH
else
    echo "  프로젝트 클론 중..."
    git clone https://github.com/Kimchanghee/marketing_analystics.git
    cd marketing_analystics
    git checkout $BRANCH
fi

echo -e "${GREEN}✓ 프로젝트 디렉토리 준비 완료${NC}"
echo ""

# Step 2: 현재 위치 및 파일 확인
echo "🔍 Step 2/5: 프로젝트 구조 확인 중..."
CURRENT_DIR=$(pwd)
echo "  현재 위치: $CURRENT_DIR"

if [ ! -d "app" ]; then
    echo -e "${RED}✗ 오류: app 디렉토리를 찾을 수 없습니다.${NC}"
    echo "  현재 위치가 올바른지 확인하세요."
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}✗ 오류: requirements.txt 파일을 찾을 수 없습니다.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 프로젝트 구조 확인 완료${NC}"
echo ""

# Step 3: Google Cloud 프로젝트 설정
echo "☁️  Step 3/5: Google Cloud 설정 중..."
gcloud config set project $PROJECT_ID
echo -e "${GREEN}✓ Google Cloud 설정 완료${NC}"
echo ""

# Step 4: Cloud Run 배포
echo "🚀 Step 4/5: Cloud Run에 배포 중..."
echo "  이 단계는 약 3-4분 소요됩니다. 잠시만 기다려주세요..."
echo ""

gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --quiet

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 배포 성공!${NC}"
else
    echo -e "${RED}✗ 배포 실패${NC}"
    exit 1
fi
echo ""

# Step 5: 배포 정보 출력
echo "📊 Step 5/5: 배포 정보 확인 중..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format="value(status.url)")

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 배포 완료!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 서비스 URL:"
echo "   $SERVICE_URL"
echo ""
echo "🔐 테스트 계정:"
echo "   마스터 관리자:"
echo "     이메일: kckc93@creatorcontrol.center"
echo "     비밀번호: Ckdgml9788@"
echo ""
echo "   크리에이터:"
echo "     이메일: creator@test.com"
echo "     비밀번호: password123"
echo ""
echo "   매니저:"
echo "     이메일: manager@test.com"
echo "     비밀번호: password123"
echo ""
echo "✅ 변경사항:"
echo "   - SUPER_ADMIN 로그인 오류 수정"
echo "   - 로그인 후 /dashboard로 정상 리다이렉트"
echo "   - 모든 관리 페이지 접근 가능"
echo ""
echo "🧪 테스트 방법:"
echo "   1. 위 URL로 접속"
echo "   2. 마스터 관리자 계정으로 로그인"
echo "   3. Internal Server Error 없이 정상 접속 확인"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
