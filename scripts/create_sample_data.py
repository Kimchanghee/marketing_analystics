"""샘플 데이터 생성 스크립트
- 개인 크리에이터: 5개 SNS 채널
- 기업 관리자: 35명 크리에이터 및 각각의 SNS 채널
"""
import asyncio
import random
from datetime import datetime, timedelta
from app.database import engine, init_db
from app.models import (
    User, UserRole, ChannelAccount, Subscription, SubscriptionTier,
    ManagerCreatorLink
)
from app.auth import auth_manager
from sqlmodel import Session, select


# 샘플 데이터
PLATFORMS = ["youtube", "instagram", "tiktok", "facebook", "threads"]
CREATOR_NAMES = [
    "김유튜버", "이인스타", "박틱톡", "최크리에이터", "정콘텐츠",
    "강인플루언서", "조소셜", "윤미디어", "임비디오", "한스트리머",
    "서블로거", "황포스터", "안라이버", "오브이로거", "권유투버",
    "민스타그래머", "배틱토커", "백스냅챗", "유인플루언서", "노콘텐츠",
    "도크리에이터", "손소셜", "양미디어", "진비디오", "차라이버",
    "강블로거", "조포스터", "윤브이로거", "장유투버", "임스타그래머",
    "한틱토커", "서인플루언서", "황콘텐츠", "안크리에이터", "오소셜"
]


async def create_sample_data():
    """샘플 데이터 생성"""
    init_db()

    with Session(engine) as session:
        print("="*60)
        print("샘플 데이터 생성 시작")
        print("="*60)

        # 1. 개인 크리에이터 계정 확인/생성
        creator_email = "creator@test.com"
        creator = session.exec(select(User).where(User.email == creator_email)).first()

        if creator:
            print(f"\n✅ 개인 크리에이터 계정 존재: {creator_email}")

            # 기존 채널 삭제
            existing_channels = session.exec(
                select(ChannelAccount).where(ChannelAccount.owner_id == creator.id)
            ).all()
            for ch in existing_channels:
                session.delete(ch)
            session.commit()
            print(f"   기존 채널 {len(existing_channels)}개 삭제")

            # 5개 SNS 채널 생성
            print(f"\n   5개 SNS 채널 생성 중...")
            for platform in PLATFORMS:
                channel = ChannelAccount(
                    owner_id=creator.id,
                    platform=platform,
                    account_name=f"{creator.name}_{platform}"
                )
                session.add(channel)
            session.commit()
            print(f"   ✅ 5개 SNS 채널 생성 완료")

        # 2. 기업 관리자 계정 확인/생성
        manager_email = "manager@test.com"
        manager = session.exec(select(User).where(User.email == manager_email)).first()

        if manager:
            print(f"\n✅ 기업 관리자 계정 존재: {manager_email}")

            # 기존 크리에이터 링크 삭제
            existing_links = session.exec(
                select(ManagerCreatorLink).where(ManagerCreatorLink.manager_id == manager.id)
            ).all()
            for link in existing_links:
                session.delete(link)
            session.commit()
            print(f"   기존 크리에이터 링크 {len(existing_links)}개 삭제")

            # 35명 크리에이터 생성
            print(f"\n   35명 크리에이터 및 SNS 채널 생성 중...")
            created_count = 0

            for i, name in enumerate(CREATOR_NAMES, 1):
                email = f"creator{i}@company.com"

                # 크리에이터 생성
                test_creator = User(
                    email=email,
                    hashed_password=auth_manager.hash_password("password123"),
                    role=UserRole.CREATOR,
                    name=name,
                    organization="샘플 기업",
                    is_active=True,
                    is_email_verified=True,
                    password_login_enabled=True,
                    locale="ko"
                )
                session.add(test_creator)
                session.commit()
                session.refresh(test_creator)

                # 구독 생성
                subscription = Subscription(
                    user_id=test_creator.id,
                    tier=SubscriptionTier.FREE,
                    active=True,
                    max_accounts=5
                )
                session.add(subscription)

                # 랜덤으로 1~5개 SNS 채널 생성
                num_channels = random.randint(1, 5)
                platforms_to_use = random.sample(PLATFORMS, num_channels)

                for platform in platforms_to_use:
                    channel = ChannelAccount(
                        owner_id=test_creator.id,
                        platform=platform,
                        account_name=f"{name.replace('', '')}_{platform}"
                    )
                    session.add(channel)

                # 매니저와 연결 (승인됨)
                link = ManagerCreatorLink(
                    manager_id=manager.id,
                    creator_id=test_creator.id,
                    approved=True,
                    connected_at=datetime.utcnow() - timedelta(days=random.randint(1, 90))
                )
                session.add(link)

                session.commit()
                created_count += 1

                if created_count % 5 == 0:
                    print(f"   진행 중... {created_count}/35")

            print(f"   ✅ 35명 크리에이터 및 SNS 채널 생성 완료")

        print("\n" + "="*60)
        print("✅ 샘플 데이터 생성 완료!")
        print("="*60)
        print("\n📊 생성된 데이터:")
        print(f"   - 개인 크리에이터: {creator_email} (5개 SNS 채널)")
        print(f"   - 기업 관리자: {manager_email} (35명 크리에이터 관리)")
        print("\n로그인 정보:")
        print(f"   개인: {creator_email} / password123")
        print(f"   기업: {manager_email} / password123")
        print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(create_sample_data())
