"""
테스트 이메일 발송 스크립트

슈퍼관리자 계정으로 k931103@gmail.com에 테스트 이메일을 발송합니다.
"""
import sys
import os
from pathlib import Path

# Windows 콘솔 UTF-8 인코딩 설정
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# app 모듈을 import하기 위한 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.config import get_settings
from app.services.super_admin_email import SuperAdminEmailService, EmailServiceError


def send_test_email():
    """테스트 이메일 발송"""
    # 설정 로드
    settings = get_settings()

    # 이메일 서비스 설정 확인
    if not SuperAdminEmailService.is_configured(settings):
        print("❌ 오류: 슈퍼관리자 이메일이 설정되지 않았습니다.")
        print("다음 환경 변수를 설정해주세요:")
        print("  - SUPER_ADMIN_EMAIL")
        print("  - SUPER_ADMIN_EMAIL_PASSWORD")
        return False

    # 이메일 서비스 초기화
    try:
        email_service = SuperAdminEmailService(settings)

        # 테스트 이메일 정보
        to_address = "k931103@gmail.com"
        subject = "테스트 이메일"
        body = """안녕하세요,

이것은 Creator Control Center 슈퍼관리자 계정에서 발송하는 테스트 이메일입니다.

제목: 테스트 이메일
내용: 테스트 내용입니다.

감사합니다.

---
Creator Control Center
Super Admin Email Service
"""

        print(f"📧 이메일 발송 중...")
        print(f"   보내는 사람: {settings.super_admin_email}")
        print(f"   받는 사람: {to_address}")
        print(f"   제목: {subject}")
        print(f"   SMTP 서버: {settings.smtp_host}:{settings.smtp_port}")
        print()

        # 이메일 발송
        email_service.send_email(
            to_address=to_address,
            subject=subject,
            body=body
        )

        print("✅ 이메일이 성공적으로 발송되었습니다!")
        print(f"   {to_address}로 테스트 이메일이 발송되었습니다.")
        return True

    except EmailServiceError as e:
        print(f"❌ 이메일 발송 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("테스트 이메일 발송 스크립트")
    print("=" * 60)
    print()

    success = send_test_email()

    print()
    print("=" * 60)
    if success:
        print("✅ 완료")
    else:
        print("❌ 실패")
    print("=" * 60)

    sys.exit(0 if success else 1)
