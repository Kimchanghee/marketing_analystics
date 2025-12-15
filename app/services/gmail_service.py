"""Gmail API 통합 서비스

Gmail API를 사용한 이메일 전송 및 수신 서비스
- SMTP/IMAP 방식보다 높은 할당량 (하루 10,000+ 메일)
- OAuth2 인증으로 보안 강화
- 메일 검색, 라벨 관리 등 고급 기능 지원
"""
import base64
import logging
from typing import List, Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass

try:
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GmailServiceError(Exception):
    """Gmail 서비스 기본 예외"""
    pass


class EmailSendError(GmailServiceError):
    """이메일 전송 실패"""
    pass


class EmailReceiveError(GmailServiceError):
    """이메일 수신 실패"""
    pass


@dataclass
class EmailMessage:
    """이메일 메시지 데이터 클래스"""
    id: str
    thread_id: str
    subject: str
    sender: str
    recipient: str
    date: str
    snippet: str
    body: str = ""


class GmailService:
    """Gmail API 서비스"""

    def __init__(self):
        """Gmail API 서비스 초기화"""
        if not GMAIL_API_AVAILABLE:
            raise ImportError(
                "google-api-python-client가 설치되지 않았습니다. "
                "pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
            )

        self.sender_email = settings.gmail_sender_email
        self.service = self._get_gmail_service()

    def _get_gmail_service(self):
        """Gmail API 서비스 객체 생성"""
        # Service Account 방식 (서버 간 통신)
        if hasattr(settings, 'google_service_account_file') and settings.google_service_account_file:
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    settings.google_service_account_file,
                    scopes=['https://www.googleapis.com/auth/gmail.send',
                           'https://www.googleapis.com/auth/gmail.readonly']
                )
                # Domain-wide delegation이 필요한 경우
                if hasattr(settings, 'gmail_delegated_email') and settings.gmail_delegated_email:
                    credentials = credentials.with_subject(settings.gmail_delegated_email)

                return build('gmail', 'v1', credentials=credentials)
            except Exception as e:
                logger.warning(f"Service account initialization failed, falling back to OAuth2: {e}")

        # OAuth2 방식 (사용자 인증)
        if hasattr(settings, 'gmail_credentials_json') and settings.gmail_credentials_json:
            try:
                import json
                creds_dict = json.loads(settings.gmail_credentials_json)
                credentials = Credentials.from_authorized_user_info(creds_dict)
                return build('gmail', 'v1', credentials=credentials)
            except Exception as e:
                logger.error(f"OAuth2 credentials initialization failed: {e}")
                raise GmailServiceError(f"Gmail 인증 실패: {e}") from e

        raise GmailServiceError(
            "Gmail 인증 정보가 설정되지 않았습니다. "
            "GOOGLE_SERVICE_ACCOUNT_FILE 또는 GMAIL_CREDENTIALS_JSON을 설정하세요."
        )

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        이메일 전송

        Args:
            to_email: 수신자 이메일
            subject: 제목
            body: 본문 (텍스트 또는 HTML)
            html: HTML 형식 여부
            cc: 참조 수신자 목록
            bcc: 숨은 참조 수신자 목록

        Returns:
            전송 결과 (메시지 ID 포함)

        Raises:
            EmailSendError: 전송 실패 시
        """
        try:
            # 메시지 생성
            if html:
                message = MIMEMultipart('alternative')
                text_part = MIMEText(body, 'plain')
                html_part = MIMEText(body, 'html')
                message.attach(text_part)
                message.attach(html_part)
            else:
                message = MIMEText(body, 'plain')

            message['To'] = to_email
            message['From'] = self.sender_email
            message['Subject'] = subject

            if cc:
                message['Cc'] = ', '.join(cc)
            if bcc:
                message['Bcc'] = ', '.join(bcc)

            # Base64 인코딩
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Gmail API로 전송
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logger.info(f"Email sent successfully to {to_email}, message ID: {result['id']}")
            return result

        except HttpError as e:
            error_msg = f"Gmail API error: {e.status_code} - {e.reason}"
            logger.error(f"Failed to send email to {to_email}: {error_msg}")
            raise EmailSendError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error sending email: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise EmailSendError(error_msg) from e

    def send_html_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        HTML 이메일 전송 (텍스트 대체 포함)

        Args:
            to_email: 수신자 이메일
            subject: 제목
            html_body: HTML 본문
            text_body: 텍스트 본문 (없으면 HTML에서 추출)

        Returns:
            전송 결과
        """
        if not text_body:
            # HTML에서 간단한 텍스트 추출
            import re
            text_body = re.sub(r'<[^>]+>', '', html_body)

        try:
            message = MIMEMultipart('alternative')
            message['To'] = to_email
            message['From'] = self.sender_email
            message['Subject'] = subject

            # 텍스트 버전 (이메일 클라이언트가 HTML을 지원하지 않을 때)
            text_part = MIMEText(text_body, 'plain', 'utf-8')
            message.attach(text_part)

            # HTML 버전
            html_part = MIMEText(html_body, 'html', 'utf-8')
            message.attach(html_part)

            # Base64 인코딩
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Gmail API로 전송
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logger.info(f"HTML email sent successfully to {to_email}, message ID: {result['id']}")
            return result

        except Exception as e:
            error_msg = f"Failed to send HTML email: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise EmailSendError(error_msg) from e

    def list_messages(
        self,
        max_results: int = 10,
        query: str = "",
        label_ids: Optional[List[str]] = None
    ) -> List[EmailMessage]:
        """
        메일함의 메시지 목록 조회

        Args:
            max_results: 최대 결과 수
            query: Gmail 검색 쿼리 (예: "is:unread", "from:example@gmail.com")
            label_ids: 라벨 ID 목록 (예: ["INBOX", "UNREAD"])

        Returns:
            이메일 메시지 목록

        Raises:
            EmailReceiveError: 조회 실패 시
        """
        try:
            params = {
                'userId': 'me',
                'maxResults': max_results,
            }

            if query:
                params['q'] = query
            if label_ids:
                params['labelIds'] = label_ids

            # 메시지 ID 목록 가져오기
            results = self.service.users().messages().list(**params).execute()
            messages = results.get('messages', [])

            if not messages:
                return []

            # 각 메시지의 상세 정보 가져오기
            email_messages = []
            for msg in messages:
                try:
                    message_detail = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()

                    email_msg = self._parse_message(message_detail)
                    email_messages.append(email_msg)
                except Exception as e:
                    logger.warning(f"Failed to fetch message {msg['id']}: {e}")
                    continue

            return email_messages

        except HttpError as e:
            error_msg = f"Gmail API error: {e.status_code} - {e.reason}"
            logger.error(f"Failed to list messages: {error_msg}")
            raise EmailReceiveError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error listing messages: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise EmailReceiveError(error_msg) from e

    def _parse_message(self, message: Dict[str, Any]) -> EmailMessage:
        """Gmail API 메시지를 EmailMessage 객체로 변환"""
        headers = {h['name'].lower(): h['value'] for h in message['payload']['headers']}

        # 본문 추출
        body = ""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')

        return EmailMessage(
            id=message['id'],
            thread_id=message['threadId'],
            subject=headers.get('subject', '(제목 없음)'),
            sender=headers.get('from', ''),
            recipient=headers.get('to', ''),
            date=headers.get('date', ''),
            snippet=message.get('snippet', ''),
            body=body[:500] if body else message.get('snippet', '')  # 본문 최대 500자
        )

    def get_unread_count(self) -> int:
        """읽지 않은 메일 개수 조회"""
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return profile.get('messagesTotal', 0)
        except Exception as e:
            logger.warning(f"Failed to get unread count: {e}")
            return 0

    def mark_as_read(self, message_id: str) -> bool:
        """메시지를 읽음으로 표시"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            logger.warning(f"Failed to mark message {message_id} as read: {e}")
            return False

    @staticmethod
    def is_configured() -> bool:
        """Gmail 서비스가 설정되어 있는지 확인"""
        has_service_account = (
            hasattr(settings, 'google_service_account_file') and
            settings.google_service_account_file
        )
        has_oauth_creds = (
            hasattr(settings, 'gmail_credentials_json') and
            settings.gmail_credentials_json
        )
        return GMAIL_API_AVAILABLE and (has_service_account or has_oauth_creds)


# 전역 인스턴스 (lazy initialization)
_gmail_service: Optional[GmailService] = None


def get_gmail_service() -> GmailService:
    """Gmail 서비스 싱글톤 인스턴스 반환"""
    global _gmail_service
    if _gmail_service is None:
        _gmail_service = GmailService()
    return _gmail_service


def send_notification_email(
    to_email: str,
    subject: str,
    message: str,
    html: bool = False
) -> bool:
    """
    간편한 알림 이메일 전송 함수

    Args:
        to_email: 수신자 이메일
        subject: 제목
        message: 메시지
        html: HTML 형식 여부

    Returns:
        성공 여부
    """
    try:
        if not GmailService.is_configured():
            logger.warning("Gmail service not configured, skipping email")
            return False

        service = get_gmail_service()
        service.send_email(to_email, subject, message, html=html)
        return True
    except Exception as e:
        logger.error(f"Failed to send notification email: {e}")
        return False
