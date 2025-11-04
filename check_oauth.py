"""OAuth 설정 확인 스크립트

현재 설정된 OAuth 제공자를 확인합니다.
"""
import sys
import os

# Windows 콘솔 UTF-8 인코딩 설정
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from app.config import get_settings


def check_oauth_config():
    """OAuth 설정 상태 확인"""
    settings = get_settings()

    print("=" * 70)
    print("📱 OAuth 소셜 로그인 설정 상태")
    print("=" * 70)
    print()

    providers = [
        ("Google", settings.google_client_id, settings.google_client_secret),
        ("Apple", settings.apple_client_id, settings.apple_team_id and settings.apple_key_id and settings.apple_private_key),
        ("Facebook", settings.facebook_app_id, settings.facebook_app_secret),
        ("Twitter", settings.twitter_client_id, settings.twitter_client_secret),
        ("TikTok", settings.tiktok_client_key, settings.tiktok_client_secret),
    ]

    configured_count = 0
    for name, client_id, secret in providers:
        is_configured = bool(client_id and secret)
        status = "✅ 설정됨" if is_configured else "❌ 미설정"
        print(f"{name:12} {status}")
        if is_configured:
            configured_count += 1
            # 일부만 표시
            if client_id:
                masked_id = client_id[:10] + "..." if len(client_id) > 10 else client_id
                print(f"{'':12} Client ID: {masked_id}")

    print()
    print("-" * 70)
    print(f"총 {configured_count}/{len(providers)}개 제공자 설정됨")
    print("-" * 70)
    print()

    if configured_count == 0:
        print("⚠️  설정된 OAuth 제공자가 없습니다.")
        print()
        print("소셜 로그인을 활성화하려면:")
        print("1. OAUTH_SETUP_GUIDE.md 파일 참조")
        print("2. Google OAuth부터 설정하는 것을 추천 (5-10분 소요)")
        print()
        return False
    else:
        print("✅ 소셜 로그인 사용 가능!")
        print()
        print("회원가입 시 다음 기능을 사용할 수 있습니다:")
        print("- 👤 개인 크리에이터로 소셜 가입")
        print("- 🏢 기업 관리자로 소셜 가입")
        print()
        return True

    print("=" * 70)


if __name__ == "__main__":
    try:
        check_oauth_config()
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
