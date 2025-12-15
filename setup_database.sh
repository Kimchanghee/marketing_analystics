#!/bin/bash

# Cloud Run 데이터베이스 환경 변수 설정 스크립트

set -e

PROJECT_ID="marketing-analytics-475700"
REGION="europe-west1"
SERVICE_NAME="marketing-analystics"
INSTANCE_NAME="marketing-db"
DB_NAME="marketing_analytics"
DB_USER="dbuser"
DB_PASSWORD="MarketingAnalytics2024!"

echo "================================================"
echo "Cloud Run 데이터베이스 환경 변수 설정"
echo "================================================"
echo ""

# 1. Cloud SQL 인스턴스 확인
echo "1단계: Cloud SQL 인스턴스 확인 중..."
if gcloud sql instances describe $INSTANCE_NAME --project=$PROJECT_ID &>/dev/null; then
    echo "✓ Cloud SQL 인스턴스가 이미 존재합니다: $INSTANCE_NAME"
    INSTANCE_EXISTS=true
else
    echo "✗ Cloud SQL 인스턴스가 없습니다. 생성하시겠습니까? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Cloud SQL 인스턴스 생성 중... (5-10분 소요)"
        gcloud sql instances create $INSTANCE_NAME \
            --database-version=POSTGRES_14 \
            --tier=db-f1-micro \
            --region=$REGION \
            --project=$PROJECT_ID
        echo "✓ Cloud SQL 인스턴스 생성 완료"
        INSTANCE_EXISTS=true
    else
        echo "Cloud SQL 인스턴스가 필요합니다. 종료합니다."
        exit 1
    fi
fi

# 2. 데이터베이스 생성
if [ "$INSTANCE_EXISTS" = true ]; then
    echo ""
    echo "2단계: 데이터베이스 생성 중..."
    if gcloud sql databases describe $DB_NAME --instance=$INSTANCE_NAME --project=$PROJECT_ID &>/dev/null; then
        echo "✓ 데이터베이스가 이미 존재합니다: $DB_NAME"
    else
        gcloud sql databases create $DB_NAME \
            --instance=$INSTANCE_NAME \
            --project=$PROJECT_ID
        echo "✓ 데이터베이스 생성 완료: $DB_NAME"
    fi

    # 3. 사용자 생성
    echo ""
    echo "3단계: 데이터베이스 사용자 생성 중..."
    if gcloud sql users list --instance=$INSTANCE_NAME --project=$PROJECT_ID | grep -q $DB_USER; then
        echo "✓ 사용자가 이미 존재합니다: $DB_USER"
        echo "비밀번호 업데이트 중..."
        gcloud sql users set-password $DB_USER \
            --instance=$INSTANCE_NAME \
            --password=$DB_PASSWORD \
            --project=$PROJECT_ID
    else
        gcloud sql users create $DB_USER \
            --instance=$INSTANCE_NAME \
            --password=$DB_PASSWORD \
            --project=$PROJECT_ID
        echo "✓ 사용자 생성 완료: $DB_USER"
    fi

    # 4. Public IP 가져오기
    echo ""
    echo "4단계: Cloud SQL Public IP 확인 중..."
    PUBLIC_IP=$(gcloud sql instances describe $INSTANCE_NAME \
        --project=$PROJECT_ID \
        --format="value(ipAddresses[0].ipAddress)")
    echo "✓ Public IP: $PUBLIC_IP"

    # 5. DATABASE_URL 생성
    DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$PUBLIC_IP:5432/$DB_NAME"
    echo ""
    echo "5단계: DATABASE_URL 생성 완료"
    echo "DATABASE_URL: postgresql://$DB_USER:****@$PUBLIC_IP:5432/$DB_NAME"

    # 6. SECRET_KEY 생성
    echo ""
    echo "6단계: SECRET_KEY 생성 중..."
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))' 2>/dev/null || openssl rand -base64 32)
    echo "✓ SECRET_KEY 생성 완료"

    # 7. Cloud Run 환경 변수 설정
    echo ""
    echo "7단계: Cloud Run 환경 변수 설정 중..."
    gcloud run services update $SERVICE_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --set-env-vars "DATABASE_URL=$DATABASE_URL" \
        --set-env-vars "SECRET_KEY=$SECRET_KEY" \
        --set-env-vars "ENVIRONMENT=production" \
        --set-env-vars "SUPER_ADMIN_ACCESS_TOKEN=Ckdgml9788@"

    echo ""
    echo "================================================"
    echo "✓ 모든 설정이 완료되었습니다!"
    echo "================================================"
    echo ""
    echo "데이터베이스 정보:"
    echo "  인스턴스: $INSTANCE_NAME"
    echo "  데이터베이스: $DB_NAME"
    echo "  사용자: $DB_USER"
    echo "  비밀번호: $DB_PASSWORD"
    echo "  Public IP: $PUBLIC_IP"
    echo ""
    echo "Cloud Run 서비스가 재배포되고 있습니다..."
    echo "배포 완료까지 2-3분 소요됩니다."
    echo ""
    echo "배포 완료 후 테스트:"
    echo "  https://marketing-analystics-573434207823.europe-west1.run.app/health"
    echo ""
fi
