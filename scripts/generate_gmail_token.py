"""Gmail OAuth2 토큰 생성 스크립트

이 스크립트는 Gmail API 사용을 위한 OAuth2 토큰을 생성합니다.
브라우저를 통해 Google 계정으로 로그인하여 권한을 부여합니다.
"""
import os
import json
import pickle
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
except ImportError:
    print("❌ 필요한 패키지가 설치되지 않았습니다!")
    print("\n다음 명령어를 실행하세요:")
    print("pip install google-auth-oauthlib")
    exit(1)

SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly'
]

def main():
    print("="*70)
    print("Gmail OAuth2 토큰 생성 스크립트")
    print("="*70)

    creds = None
    token_file = Path('credentials/token.pickle')
    client_secrets_file = Path('credentials/client_secrets.json')

    # client_secrets.json 확인
    if not client_secrets_file.exists():
        print(f"\n❌ {client_secrets_file} 파일이 없습니다!")
        print("\n해결 방법:")
        print("1. Google Cloud Console → API 및 서비스 → 사용자 인증 정보")
        print("2. OAuth 2.0 클라이언트 ID에서 JSON 다운로드")
        print("3. 다운로드한 파일을 credentials/client_secrets.json로 저장")
        return

    print(f"\n✅ {client_secrets_file} 파일을 찾았습니다.")

    # credentials 폴더 확인
    token_file.parent.mkdir(exist_ok=True)

    # 기존 토큰 확인
    if token_file.exists():
        print(f"✅ 기존 토큰 파일을 발견했습니다: {token_file}")
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)

    # 유효한 토큰이 없으면 새로 생성
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("\n🔄 토큰이 만료되었습니다. 갱신 중...")
            try:
                creds.refresh(Request())
                print("✅ 토큰이 성공적으로 갱신되었습니다.")
            except Exception as e:
                print(f"❌ 토큰 갱신 실패: {e}")
                print("새 토큰을 생성합니다...")
                creds = None

        if not creds:
            print("\n🌐 브라우저에서 Google 계정으로 로그인하세요...")
            print("(브라우저가 자동으로 열립니다)")

            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(client_secrets_file), SCOPES)
                creds = flow.run_local_server(port=0)
                print("\n✅ Google 계정 인증이 완료되었습니다!")
            except Exception as e:
                print(f"\n❌ 인증 실패: {e}")
                return

        # 토큰 저장
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
        print(f"✅ 토큰이 {token_file}에 저장되었습니다.")

    # .env에 넣을 JSON 생성
    creds_dict = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }

    # JSON 문자열 생성
    json_str = json.dumps(creds_dict)

    print("\n" + "="*70)
    print("✅ Gmail OAuth2 토큰 생성 완료!")
    print("="*70)
    print("\n📋 다음 내용을 .env 파일에 추가하세요:\n")
    print("-"*70)
    print(f"GMAIL_SENDER_EMAIL=ympartners.uk@gmail.com")
    print(f"GMAIL_CREDENTIALS_JSON='{json_str}'")
    print("-"*70)

    # 선택적으로 .env 파일에 자동 추가
    env_file = Path('.env')
    if env_file.exists():
        print("\n❓ .env 파일에 자동으로 추가하시겠습니까? (y/n): ", end='')
        choice = input().lower().strip()

        if choice == 'y':
            with open(env_file, 'r', encoding='utf-8') as f:
                env_content = f.read()

            # 기존 GMAIL 설정 제거
            lines = []
            skip_next = False
            for line in env_content.split('\n'):
                if line.startswith('GMAIL_SENDER_EMAIL=') or line.startswith('GMAIL_CREDENTIALS_JSON='):
                    continue
                lines.append(line)

            # 새 설정 추가
            lines.append('')
            lines.append('# Gmail API - OAuth2 설정 (자동 생성)')
            lines.append(f'GMAIL_SENDER_EMAIL=ympartners.uk@gmail.com')
            lines.append(f"GMAIL_CREDENTIALS_JSON='{json_str}'")

            with open(env_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            print("✅ .env 파일에 자동으로 추가되었습니다!")
    else:
        print("\n⚠️  .env 파일이 없습니다. 수동으로 생성해주세요.")

    print("\n" + "="*70)
    print("🎉 설정이 완료되었습니다!")
    print("="*70)
    print("\n다음 단계:")
    print("1. .env 파일에 위 내용이 추가되었는지 확인")
    print("2. python test_gmail.py 실행하여 테스트")
    print("="*70)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 사용자가 취소했습니다.")
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
