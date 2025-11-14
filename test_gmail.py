"""Gmail API 연동 테스트 스크립트

이 스크립트는 Gmail API 설정이 올바르게 되었는지 테스트합니다.
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.services.gmail_service import GmailService, send_notification_email
    from app.config import get_settings
except ImportError as e:
    print(f"❌ 필요한 모듈을 가져올 수 없습니다: {e}")
    print("\n다음을 확인하세요:")
    print("1. 현재 디렉토리가 프로젝트 루트인지 확인")
    print("2. pip install -r requirements.txt 실행 여부 확인")
    sys.exit(1)


def test_configuration():
    """Gmail API 설정 확인"""
    print("=" * 70)
    print("1. Gmail API 설정 확인")
    print("=" * 70)

    settings = get_settings()

    # 환경 변수 확인
    if settings.gmail_sender_email:
        print(f"✅ GMAIL_SENDER_EMAIL: {settings.gmail_sender_email}")
    else:
        print("❌ GMAIL_SENDER_EMAIL이 설정되지 않았습니다.")

    # Service Account 방식 확인
    if settings.google_service_account_file:
        print(f"✅ GOOGLE_SERVICE_ACCOUNT_FILE: {settings.google_service_account_file}")
        service_account_path = Path(settings.google_service_account_file)
        if service_account_path.exists():
            print(f"   ✅ Service Account 파일 존재 확인")
        else:
            print(f"   ❌ Service Account 파일을 찾을 수 없음: {service_account_path}")

    # OAuth2 방식 확인
    if settings.gmail_credentials_json:
        print("✅ GMAIL_CREDENTIALS_JSON: 설정됨 (OAuth2 방식)")

    # 설정 완료 여부
    if GmailService.is_configured():
        print("\n✅ Gmail API가 올바르게 설정되었습니다!")
        return True
    else:
        print("\n❌ Gmail API 설정이 완료되지 않았습니다.")
        print("\n다음 중 하나를 설정하세요:")
        print("1. Service Account 방식:")
        print("   - GMAIL_SENDER_EMAIL")
        print("   - GOOGLE_SERVICE_ACCOUNT_FILE")
        print("\n2. OAuth2 방식:")
        print("   - GMAIL_SENDER_EMAIL")
        print("   - GMAIL_CREDENTIALS_JSON")
        print("\n자세한 내용은 GMAIL_API_SETUP.md를 참조하세요.")
        return False


def test_service_initialization():
    """Gmail 서비스 초기화 테스트"""
    print("\n" + "=" * 70)
    print("2. Gmail 서비스 초기화 테스트")
    print("=" * 70)

    try:
        service = GmailService()
        print("✅ GmailService 인스턴스 생성 성공")
        print(f"   발신자 이메일: {service.sender_email}")
        return True
    except Exception as e:
        print(f"❌ GmailService 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_send_email():
    """이메일 전송 테스트"""
    print("\n" + "=" * 70)
    print("3. 테스트 이메일 전송")
    print("=" * 70)

    settings = get_settings()
    recipient = settings.gmail_sender_email  # 자기 자신에게 전송

    if not recipient:
        print("❌ GMAIL_SENDER_EMAIL이 설정되지 않아 테스트를 건너뜁니다.")
        return False

    print(f"\n테스트 이메일을 {recipient}로 전송합니다...")
    print("(자기 자신에게 전송하여 스팸 방지)")

    try:
        # 간단한 텍스트 이메일 전송
        result = send_notification_email(
            to_email=recipient,
            subject="[테스트] Gmail API 연동 테스트",
            message="""안녕하세요!

이 이메일은 Creator Control Center의 Gmail API 연동 테스트입니다.

이 이메일을 받으셨다면 Gmail API가 정상적으로 작동하고 있습니다!

✅ 텍스트 이메일 전송 성공
🔗 Gmail API를 통해 전송됨

감사합니다.
Creator Control Center
"""
        )

        if result:
            print("✅ 이메일 전송 성공!")
            print(f"\n📬 {recipient}의 받은편지함을 확인하세요.")
            return True
        else:
            print("❌ 이메일 전송 실패")
            return False

    except Exception as e:
        print(f"❌ 이메일 전송 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_html_email():
    """HTML 이메일 전송 테스트"""
    print("\n" + "=" * 70)
    print("4. HTML 이메일 전송 테스트")
    print("=" * 70)

    settings = get_settings()
    recipient = settings.gmail_sender_email

    if not recipient:
        print("❌ GMAIL_SENDER_EMAIL이 설정되지 않아 테스트를 건너뜁니다.")
        return False

    print(f"\nHTML 이메일을 {recipient}로 전송합니다...")

    try:
        service = GmailService()

        html_body = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px 10px 0 0;
            text-align: center;
        }
        .content {
            background: #f9f9f9;
            padding: 30px;
            border-radius: 0 0 10px 10px;
        }
        .success-badge {
            background: #10b981;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            display: inline-block;
            margin: 20px 0;
        }
        .footer {
            text-align: center;
            color: #666;
            margin-top: 30px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎉 Gmail API 연동 성공!</h1>
    </div>
    <div class="content">
        <p>안녕하세요!</p>

        <p>Creator Control Center의 <strong>Gmail API</strong> 연동이 정상적으로 완료되었습니다.</p>

        <div class="success-badge">
            ✅ HTML 이메일 전송 테스트 성공
        </div>

        <h3>설정 완료 항목:</h3>
        <ul>
            <li>✅ Gmail API 활성화</li>
            <li>✅ OAuth2 인증 설정</li>
            <li>✅ 이메일 전송 기능</li>
            <li>✅ HTML 템플릿 렌더링</li>
        </ul>

        <h3>다음 단계:</h3>
        <ol>
            <li>프로덕션 환경에 배포</li>
            <li>이메일 템플릿 커스터마이징</li>
            <li>자동화된 알림 워크플로우 구축</li>
        </ol>

        <p>이 이메일은 Gmail API를 통해 전송되었습니다.</p>
    </div>
    <div class="footer">
        <p>Creator Control Center | Powered by Gmail API</p>
    </div>
</body>
</html>
"""

        text_body = """
안녕하세요!

Creator Control Center의 Gmail API 연동이 정상적으로 완료되었습니다.

✅ HTML 이메일 전송 테스트 성공

설정 완료 항목:
- Gmail API 활성화
- OAuth2 인증 설정
- 이메일 전송 기능
- HTML 템플릿 렌더링

다음 단계:
1. 프로덕션 환경에 배포
2. 이메일 템플릿 커스터마이징
3. 자동화된 알림 워크플로우 구축

이 이메일은 Gmail API를 통해 전송되었습니다.

Creator Control Center | Powered by Gmail API
"""

        result = service.send_html_email(
            to_email=recipient,
            subject="[테스트] Gmail API HTML 이메일 테스트",
            html_body=html_body,
            text_body=text_body
        )

        if result and 'id' in result:
            print("✅ HTML 이메일 전송 성공!")
            print(f"   Message ID: {result['id']}")
            print(f"\n📬 {recipient}의 받은편지함을 확인하세요.")
            return True
        else:
            print("❌ HTML 이메일 전송 실패")
            return False

    except Exception as e:
        print(f"❌ HTML 이메일 전송 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 실행"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "Gmail API 연동 테스트" + " " * 27 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # 테스트 실행
    tests = [
        ("설정 확인", test_configuration),
        ("서비스 초기화", test_service_initialization),
        ("텍스트 이메일 전송", test_send_email),
        ("HTML 이메일 전송", test_html_email),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ '{test_name}' 테스트 중 예외 발생: {e}")
            results.append((test_name, False))

    # 결과 요약
    print("\n" + "=" * 70)
    print("테스트 결과 요약")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{status} - {test_name}")

    print("\n" + "=" * 70)
    print(f"총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.0f}%)")
    print("=" * 70)

    if passed == total:
        print("\n🎉 모든 테스트를 통과했습니다!")
        print("Gmail API가 정상적으로 작동하고 있습니다.")
    else:
        print("\n⚠️  일부 테스트가 실패했습니다.")
        print("GMAIL_API_SETUP.md를 참조하여 설정을 확인하세요.")

    return passed == total


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ 사용자가 테스트를 취소했습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
