"""
로컬 SMTP 디버깅 서버

이메일을 실제로 발송하지 않고, 콘솔에 출력하여 테스트할 수 있습니다.
"""
import asyncio
import sys
import os
from datetime import datetime
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP as SMTPProtocol

# Windows 콘솔 UTF-8 인코딩 설정
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class DebugHandler:
    """이메일을 콘솔에 출력하는 핸들러"""

    async def handle_DATA(self, server, session, envelope):
        print("\n" + "=" * 70)
        print(f"📧 새 이메일 수신 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print(f"발신자: {envelope.mail_from}")
        print(f"수신자: {', '.join(envelope.rcpt_tos)}")
        print(f"메시지 크기: {len(envelope.content)} bytes")
        print("-" * 70)
        print("메시지 내용:")
        print("-" * 70)

        # 메시지 디코딩
        try:
            message_content = envelope.content.decode('utf-8', errors='replace')
            print(message_content)
        except Exception as e:
            print(f"디코딩 오류: {e}")
            print(envelope.content)

        print("=" * 70)
        print("✅ 이메일 수신 완료\n")

        return '250 Message accepted for delivery'


def run_smtp_server(host='localhost', port=1025):
    """SMTP 서버 실행"""
    handler = DebugHandler()
    controller = Controller(handler, hostname=host, port=port)

    print("=" * 70)
    print("🚀 로컬 SMTP 디버깅 서버 시작")
    print("=" * 70)
    print(f"호스트: {host}")
    print(f"포트: {port}")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("이 서버는 이메일을 실제로 발송하지 않고 콘솔에 출력합니다.")
    print("테스트 이메일을 발송하려면 다른 터미널에서 send_test_email.py를 실행하세요.")
    print()
    print("종료하려면 Ctrl+C를 누르세요.")
    print("=" * 70)
    print()

    controller.start()

    try:
        # 서버가 계속 실행되도록 유지
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\n\n서버를 종료합니다...")
        controller.stop()
        print("✅ 서버가 종료되었습니다.")


if __name__ == "__main__":
    # 기본 포트는 1025 (권한 불필요)
    HOST = "localhost"
    PORT = 1025

    try:
        run_smtp_server(HOST, PORT)
    except Exception as e:
        print(f"❌ 서버 시작 오류: {e}")
        print("\naiosmtpd 패키지가 설치되지 않았을 수 있습니다.")
        print("다음 명령으로 설치하세요:")
        print("  pip install aiosmtpd")
        sys.exit(1)
