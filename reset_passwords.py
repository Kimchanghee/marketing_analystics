"""계정 비밀번호 재설정 스크립트"""
import asyncio
from app.database import engine, init_db
from app.models import User
from app.auth import auth_manager
from sqlmodel import Session, select


async def reset_passwords():
    """모든 테스트 계정의 비밀번호 재설정"""
    init_db()

    with Session(engine) as session:
        accounts = [
            ("creator@test.com", "password123"),
            ("manager@test.com", "password123"),
            ("admin@test.com", "password123"),
            ("admin@creatorscontrol.com", "Ckdgml9788@"),
        ]

        for email, password in accounts:
            user = session.exec(select(User).where(User.email == email)).first()
            if user:
                # 비밀번호 재해싱
                user.hashed_password = auth_manager.hash_password(password)
                user.is_active = True
                user.is_email_verified = True
                user.password_login_enabled = True
                session.add(user)
                print(f"✅ {email} 비밀번호 재설정 완료")
            else:
                print(f"❌ {email} 계정을 찾을 수 없음")

        session.commit()
        print("\n" + "="*60)
        print("✅✅✅ 모든 계정 비밀번호가 재설정되었습니다!")
        print("="*60)
        print("\n이제 다음 계정으로 로그인하세요:")
        print("\n🔐 마스터 관리자:")
        print("   이메일: admin@creatorscontrol.com")
        print("   비밀번호: Ckdgml9788@")
        print("\n🔐 일반 슈퍼관리자:")
        print("   이메일: admin@test.com")
        print("   비밀번호: password123")
        print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(reset_passwords())
