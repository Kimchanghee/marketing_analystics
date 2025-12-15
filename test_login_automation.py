"""
로그인 자동화 테스트 스크립트

지정된 계정으로 Creator Control Center에 로그인을 시도하고 결과를 확인합니다.
"""
import sys
import os
import json
import asyncio
from pathlib import Path

# Windows 콘솔 UTF-8 인코딩 설정
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# app 모듈을 import하기 위한 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.database import engine, init_db
from app.models import User
from app.auth import auth_manager
from sqlmodel import Session, select


def print_header(title: str):
    """헤더 출력"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title: str):
    """섹션 출력"""
    print(f"\n📌 {title}")
    print("-" * 70)


def test_login(email: str, password: str, session: Session) -> dict:
    """
    로그인 테스트 수행
    
    Args:
        email: 로그인할 이메일
        password: 비밀번호
        session: 데이터베이스 세션
        
    Returns:
        테스트 결과 딕셔너리
    """
    result = {
        "email": email,
        "success": False,
        "user_found": False,
        "password_valid": False,
        "is_active": False,
        "email_verified": False,
        "password_login_enabled": False,
        "user_role": None,
        "user_name": None,
        "organization": None,
        "error_message": None
    }
    
    try:
        # 1. 데이터베이스에서 사용자 검색
        print(f"   🔍 데이터베이스에서 사용자 검색 중...")
        user = session.exec(select(User).where(User.email == email)).first()
        
        if not user:
            result["error_message"] = "이메일 또는 비밀번호가 일치하지 않습니다."
            print(f"   ❌ 사용자를 찾을 수 없습니다: {email}")
            return result
        
        result["user_found"] = True
        result["user_role"] = user.role.value
        result["user_name"] = user.name
        result["organization"] = user.organization
        result["is_active"] = user.is_active
        result["email_verified"] = user.is_email_verified
        result["password_login_enabled"] = user.password_login_enabled
        
        print(f"   ✅ 사용자 발견: {user.name} ({user.email})")
        print(f"      - 역할: {user.role.value}")
        print(f"      - 조직: {user.organization}")
        print(f"      - 활성 상태: {user.is_active}")
        print(f"      - 이메일 인증: {user.is_email_verified}")
        print(f"      - 비밀번호 로그인 활성화: {user.password_login_enabled}")
        
        # 2. 계정 상태 확인
        print(f"\n   🔐 계정 상태 검증 중...")
        if not user.is_active:
            result["error_message"] = "계정이 비활성화되었습니다."
            print(f"   ❌ 계정이 비활성화되어 있습니다.")
            return result
        
        if not user.password_login_enabled:
            result["error_message"] = "비밀번호 로그인이 비활성화되었습니다."
            print(f"   ❌ 비밀번호 로그인이 비활성화되어 있습니다.")
            return result
        
        print(f"   ✅ 계정 상태 정상")
        
        # 3. 비밀번호 검증
        print(f"\n   🔑 비밀번호 검증 중...")
        password_valid = auth_manager.verify_password(password, user.hashed_password)
        result["password_valid"] = password_valid
        
        if not password_valid:
            result["error_message"] = "이메일 또는 비밀번호가 일치하지 않습니다."
            print(f"   ❌ 비밀번호가 일치하지 않습니다.")
            return result
        
        print(f"   ✅ 비밀번호 검증 성공")
        
        # 4. 로그인 성공
        result["success"] = True
        print(f"\n   🎉 로그인 성공!")
        
        # 리다이렉트 경로 결정
        from app.models import UserRole
        if user.role == UserRole.MANAGER:
            redirect_path = "/manager/dashboard"
        else:
            redirect_path = "/dashboard"
        
        print(f"   → 리다이렉트 경로: {redirect_path}")
        
        return result
        
    except Exception as e:
        result["error_message"] = f"예상치 못한 오류: {str(e)}"
        print(f"   ❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return result


def main():
    """메인 함수"""
    print_header("로그인 자동화 테스트")
    
    # 데이터베이스 초기화
    print("\n🔧 데이터베이스 초기화 중...")
    init_db()
    
    # 테스트할 계정 정보
    test_accounts = [
        {
            "name": "마스터 관리자",
            "email": "kckc93@creatorscontrol.com",
            "password": "Ckdgml9788@",
            "description": "모든 페이지 접근 가능한 슈퍼 관리자"
        },
        {
            "name": "슈퍼 관리자",
            "email": "admin@test.com",
            "password": "password123",
            "description": "테스트용 슈퍼 관리자"
        },
        {
            "name": "기업 관리자",
            "email": "manager@test.com",
            "password": "password123",
            "description": "테스트용 기업 관리자"
        },
        {
            "name": "개인 크리에이터",
            "email": "creator@test.com",
            "password": "password123",
            "description": "테스트용 개인 크리에이터"
        }
    ]
    
    # 전체 테스트 결과 저장
    all_results = []
    
    with Session(engine) as session:
        for account in test_accounts:
            print_section(f"{account['name']} 로그인 테스트")
            print(f"   📧 이메일: {account['email']}")
            print(f"   🔑 비밀번호: {'*' * len(account['password'])}")
            print(f"   📝 설명: {account['description']}")
            print()
            
            result = test_login(account['email'], account['password'], session)
            all_results.append({
                "account_name": account['name'],
                "description": account['description'],
                **result
            })
            
            # 결과 요약
            if result['success']:
                print(f"\n   ✅ 테스트 결과: 성공")
            else:
                print(f"\n   ❌ 테스트 결과: 실패")
                print(f"   📝 오류 메시지: {result['error_message']}")
    
    # 최종 결과 요약
    print_header("테스트 결과 요약")
    
    success_count = sum(1 for r in all_results if r['success'])
    total_count = len(all_results)
    
    print(f"\n총 {total_count}개 계정 테스트 완료")
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {total_count - success_count}개")
    print()
    
    # 상세 결과 출력
    for result in all_results:
        status = "✅ 성공" if result['success'] else "❌ 실패"
        print(f"\n{status} - {result['account_name']}")
        print(f"   이메일: {result['email']}")
        print(f"   사용자 발견: {'✓' if result['user_found'] else '✗'}")
        print(f"   비밀번호 유효: {'✓' if result['password_valid'] else '✗'}")
        print(f"   계정 활성: {'✓' if result['is_active'] else '✗'}")
        print(f"   이메일 인증: {'✓' if result['email_verified'] else '✗'}")
        print(f"   비밀번호 로그인 활성화: {'✓' if result['password_login_enabled'] else '✗'}")
        if result['user_name']:
            print(f"   사용자명: {result['user_name']}")
        if result['user_role']:
            print(f"   역할: {result['user_role']}")
        if not result['success']:
            print(f"   오류: {result['error_message']}")
    
    # JSON 결과 저장
    output_file = "login_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 상세 결과가 {output_file}에 저장되었습니다.")
    
    print_header("테스트 완료")
    
    # 종료 코드 반환
    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
