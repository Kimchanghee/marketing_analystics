"""
로컬 SMTP 서버 - 이메일을 파일로 저장

이메일을 received_emails 폴더에 파일로 저장합니다.
"""
import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path
from aiosmtpd.controller import Controller

# Windows 콘솔 UTF-8 인코딩 설정
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class FileHandler:
    """이메일을 파일로 저장하는 핸들러"""

    def __init__(self, output_dir="received_emails"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    async def handle_DATA(self, server, session, envelope):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 파일명 생성
        from_addr = envelope.mail_from.replace('@', '_at_').replace('.', '_')
        filename = f"{timestamp}_{from_addr}.eml"
        filepath = self.output_dir / filename

        print("\n" + "=" * 70)
        print(f"📧 새 이메일 수신 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print(f"발신자: {envelope.mail_from}")
        print(f"수신자: {', '.join(envelope.rcpt_tos)}")
        print(f"파일 저장: {filepath}")
        print("-" * 70)

        # 이메일 내용 디코딩 및 출력
        try:
            message_content = envelope.content.decode('utf-8', errors='replace')

            # 파일로 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"From: {envelope.mail_from}\n")
                f.write(f"To: {', '.join(envelope.rcpt_tos)}\n")
                f.write(f"Received: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("\n")
                f.write(message_content)

            # 콘솔에도 출력
            print("메시지 내용:")
            print("-" * 70)
            print(message_content)
            print("=" * 70)
            print(f"✅ 이메일이 {filepath}에 저장되었습니다.")
            print()

        except Exception as e:
            print(f"오류 발생: {e}")
            # 원본 바이너리 저장
            with open(filepath, 'wb') as f:
                f.write(envelope.content)

        return '250 Message accepted for delivery'


def run_smtp_server(host='localhost', port=1025):
    """SMTP 서버 실행"""
    handler = FileHandler()
    controller = Controller(handler, hostname=host, port=port)

    print("=" * 70)
    print("🚀 로컬 SMTP 서버 시작 (파일 저장 모드)")
    print("=" * 70)
    print(f"호스트: {host}")
    print(f"포트: {port}")
    print(f"저장 폴더: {handler.output_dir.absolute()}")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("이메일이 received_emails 폴더에 파일로 저장됩니다.")
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
    HOST = "localhost"
    PORT = 1025

    try:
        run_smtp_server(HOST, PORT)
    except Exception as e:
        print(f"❌ 서버 시작 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
