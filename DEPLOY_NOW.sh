#!/bin/bash
# 배포 스크립트

echo "==================================="
echo "🚀 Marketing Analytics 배포 시작"
echo "==================================="
echo ""

# 1. 프로젝트 ID 설정
PROJECT_ID="your-project-id"  # 실제 프로젝트 ID로 변경 필요
SERVICE_NAME="marketing-analystics"
REGION="europe-west1"

echo "📋 배포 정보:"
echo "  - 프로젝트: $PROJECT_ID"
echo "  - 서비스: $SERVICE_NAME"
echo "  - 리전: $REGION"
echo ""

# 2. Google Cloud 프로젝트 확인
echo "🔍 Google Cloud 프로젝트 확인 중..."
gcloud config set project $PROJECT_ID

# 3. Cloud Build로 이미지 빌드
echo ""
echo "🏗️  이미지 빌드 중... (약 3-5분 소요)"
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

if [ $? -ne 0 ]; then
    echo "❌ 빌드 실패!"
    exit 1
fi

# 4. Cloud Run에 배포
echo ""
echo "☁️  Cloud Run에 배포 중..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --timeout 300

if [ $? -ne 0 ]; then
    echo "❌ 배포 실패!"
    exit 1
fi

echo ""
echo "==================================="
echo "✅ 배포 완료!"
echo "==================================="
echo ""
echo "🌐 서비스 URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
echo ""
echo "📊 배포 후 체크리스트:"
echo "  1. [ ] 홈 페이지 접속 확인"
echo "  2. [ ] 로그인 테스트 (슈퍼 관리자)"
echo "  3. [ ] /dashboard 접속 확인"
echo "  4. [ ] AI PD 기능 테스트"
echo "  5. [ ] 기업 대시보드 확인"
echo ""
echo "📝 로그 확인:"
echo "  gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" --limit 50"
echo ""
