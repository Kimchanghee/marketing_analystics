"""테스트 계정 생성 스크립트"""
import asyncio
from app.database import engine, init_db
from app.models import User, UserRole, Subscription, SubscriptionTier
from app.services.auth import hash_password
from sqlmodel import Session, select


async def create_test_accounts():
    """테스트용 계정 3개 생성"""
    init_db()

    with Session(engine) as session:
        # 1. Creator 계정
        creator_email = "creator@test.com"
        existing_creator = session.exec(select(User).where(User.email == creator_email)).first()
        if not existing_creator:
            creator = User(
                email=creator_email,
                hashed_password=hash_password("password123"),
                role=UserRole.CREATOR,
                name="테스트 크리에이터",
                organization="개인",
                is_active=True,
                is_email_verified=True,
                password_login_enabled=True,
                locale="ko"
            )
            session.add(creator)
            session.commit()
            session.refresh(creator)

            # Creator 구독 생성
            subscription = Subscription(
                user_id=creator.id,
                tier=SubscriptionTier.FREE,
                active=True,
                max_accounts=1
            )
            session.add(subscription)
            session.commit()
            print(f"✅ Creator 계정 생성 완료: {creator_email} / password123")
        else:
            print(f"ℹ️ Creator 계정이 이미 존재합니다: {creator_email}")

        # 2. Manager 계정
        manager_email = "manager@test.com"
        existing_manager = session.exec(select(User).where(User.email == manager_email)).first()
        if not existing_manager:
            manager = User(
                email=manager_email,
                hashed_password=hash_password("password123"),
                role=UserRole.MANAGER,
                name="테스트 매니저",
                organization="테스트 기업",
                is_active=True,
                is_email_verified=True,
                password_login_enabled=True,
                locale="ko"
            )
            session.add(manager)
            session.commit()
            session.refresh(manager)

            # Manager 구독 생성
            subscription = Subscription(
                user_id=manager.id,
                tier=SubscriptionTier.ENTERPRISE,
                active=True,
                max_accounts=20
            )
            session.add(subscription)
            session.commit()
            print(f"✅ Manager 계정 생성 완료: {manager_email} / password123")
        else:
            print(f"ℹ️ Manager 계정이 이미 존재합니다: {manager_email}")

        # 3. Super Admin 계정
        admin_email = "admin@test.com"
        existing_admin = session.exec(select(User).where(User.email == admin_email)).first()
        if not existing_admin:
            admin = User(
                email=admin_email,
                hashed_password=hash_password("password123"),
                role=UserRole.SUPER_ADMIN,
                name="슈퍼 관리자",
                organization="Creator Control Center",
                is_active=True,
                is_email_verified=True,
                password_login_enabled=True,
                locale="ko"
            )
            session.add(admin)
            session.commit()
            print(f"✅ Super Admin 계정 생성 완료: {admin_email} / password123")
        else:
            print(f"ℹ️ Super Admin 계정이 이미 존재합니다: {admin_email}")

    print("\n" + "="*60)
    print("테스트 계정 생성 완료!")
    print("="*60)
    print("\n📋 로그인 정보:")
    print("\n1️⃣ Creator (개인 크리에이터)")
    print(f"   이메일: creator@test.com")
    print(f"   비밀번호: password123")
    print(f"   접속: http://127.0.0.1:8000/login")
    print(f"   → 로그인 후: http://127.0.0.1:8000/dashboard")

    print("\n2️⃣ Manager (기업 관리자)")
    print(f"   이메일: manager@test.com")
    print(f"   비밀번호: password123")
    print(f"   접속: http://127.0.0.1:8000/login")
    print(f"   → 로그인 후: http://127.0.0.1:8000/manager/dashboard")
    print(f"   → AI 문의 관리: http://127.0.0.1:8000/manager/inquiries")

    print("\n3️⃣ Super Admin (슈퍼 관리자)")
    print(f"   이메일: admin@test.com")
    print(f"   비밀번호: password123")
    print(f"   접속: http://127.0.0.1:8000/login")
    print(f"   → 로그인 후: http://127.0.0.1:8000/super-admin?admin_token=YOUR_TOKEN")
    print(f"   (주의: .env 파일의 SUPER_ADMIN_ACCESS_TOKEN 필요)")
    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(create_test_accounts())
