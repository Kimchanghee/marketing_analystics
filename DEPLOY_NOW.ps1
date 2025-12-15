# PowerShell 배포 스크립트

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "🚀 Marketing Analytics 배포 시작" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# 1. 프로젝트 ID 설정
$PROJECT_ID = "your-project-id"  # 실제 프로젝트 ID로 변경 필요
$SERVICE_NAME = "marketing-analystics"
$REGION = "europe-west1"

Write-Host "📋 배포 정보:" -ForegroundColor Yellow
Write-Host "  - 프로젝트: $PROJECT_ID"
Write-Host "  - 서비스: $SERVICE_NAME"
Write-Host "  - 리전: $REGION"
Write-Host ""

# 2. Google Cloud 프로젝트 확인
Write-Host "🔍 Google Cloud 프로젝트 확인 중..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

# 3. Cloud Build로 이미지 빌드
Write-Host ""
Write-Host "🏗️  이미지 빌드 중... (약 3-5분 소요)" -ForegroundColor Yellow
gcloud builds submit --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 빌드 실패!" -ForegroundColor Red
    exit 1
}

# 4. Cloud Run에 배포
Write-Host ""
Write-Host "☁️  Cloud Run에 배포 중..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
  --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --memory 1Gi `
  --cpu 1 `
  --max-instances 10 `
  --timeout 300

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 배포 실패!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "===================================" -ForegroundColor Green
Write-Host "✅ 배포 완료!" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 서비스 URL:" -ForegroundColor Cyan
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
Write-Host ""
Write-Host "📊 배포 후 체크리스트:" -ForegroundColor Yellow
Write-Host "  1. [ ] 홈 페이지 접속 확인"
Write-Host "  2. [ ] 로그인 테스트 (슈퍼 관리자)"
Write-Host "  3. [ ] /dashboard 접속 확인"
Write-Host "  4. [ ] AI PD 기능 테스트"
Write-Host "  5. [ ] 기업 대시보드 확인"
Write-Host ""
Write-Host "📝 로그 확인:" -ForegroundColor Yellow
Write-Host "  gcloud logging read `"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME`" --limit 50"
Write-Host ""
