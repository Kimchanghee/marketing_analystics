import imaplib
import smtplib
from contextlib import contextmanager
from dataclasses import dataclass
from email import message_from_bytes
from email.header import decode_header, make_header
from email.message import EmailMessage
from typing import List, Optional

from ..config import Settings


class EmailServiceError(Exception):
    """Base error for the super admin email service."""


class EmailConfigurationError(EmailServiceError):
    """Raised when the email service is not properly configured."""


class EmailSendError(EmailServiceError):
    """Raised when sending fails."""


class EmailReceiveError(EmailServiceError):
    """Raised when fetching mailbox contents fails."""


@dataclass
class EmailSummary:
    """Lightweight representation of an email for list views."""

    uid: str
    subject: str
    sender: str
    recipient: str
    date: str
    snippet: str


def _decode_header(value: Optional[str]) -> str:
    if not value:
        return ""
    try:
        decoded = make_header(decode_header(value))
        return str(decoded)
    except Exception:
        return value


def _extract_text_snippet(message) -> str:
    """Best-effort extraction of the first text snippet from the email body."""
    text_content: Optional[str] = None

    for part in message.walk():
        is_attachment = part.get_content_disposition() == "attachment"
        if is_attachment:
            continue

        if part.get_content_type() == "text/plain":
            payload = part.get_payload(decode=True)
            if payload:
                encoding = part.get_content_charset() or "utf-8"
                try:
                    text_content = payload.decode(encoding, errors="ignore")
                except Exception:
                    text_content = payload.decode("utf-8", errors="ignore")
                break

    if not text_content:
        # Fall back to the raw payload if no text/plain was found.
        payload = message.get_payload(decode=True)
        if payload:
            try:
                text_content = payload.decode("utf-8", errors="ignore")
            except Exception:
                text_content = payload.decode("latin-1", errors="ignore")

    text_content = (text_content or "").strip()
    if len(text_content) > 200:
        return text_content[:200] + "…"
    return text_content


def _ensure_configured(settings: Settings) -> None:
    if not settings.super_admin_email or not settings.super_admin_email_password:
        raise EmailConfigurationError(
            "Super admin email credentials are not configured. "
            "Set SUPER_ADMIN_EMAIL and SUPER_ADMIN_EMAIL_PASSWORD."
        )


class SuperAdminEmailService:
    """Provides send/receive capabilities for the super admin email account."""

    def __init__(self, settings: Settings):
        _ensure_configured(settings)
        self.settings = settings

    @staticmethod
    def is_configured(settings: Settings) -> bool:
        return bool(settings.super_admin_email and settings.super_admin_email_password)

    @contextmanager
    def _smtp_connection(self):
        try:
            server = smtplib.SMTP(
                self.settings.smtp_host,
                self.settings.smtp_port,
                timeout=30,
            )
            try:
                if self.settings.smtp_use_tls:
                    server.starttls()
                server.login(
                    self.settings.super_admin_email,
                    self.settings.super_admin_email_password,
                )
                yield server
            finally:
                server.quit()
        except Exception as exc:
            raise EmailSendError(f"Failed to connect to SMTP server: {exc}") from exc

    @contextmanager
    def _imap_connection(self):
        try:
            if self.settings.imap_use_ssl:
                client = imaplib.IMAP4_SSL(
                    self.settings.imap_host,
                    self.settings.imap_port,
                )
            else:
                client = imaplib.IMAP4(
                    self.settings.imap_host,
                    self.settings.imap_port,
                )

            try:
                client.login(
                    self.settings.super_admin_email,
                    self.settings.super_admin_email_password,
                )
                yield client
            finally:
                client.logout()
        except Exception as exc:
            raise EmailReceiveError(f"Failed to connect to IMAP server: {exc}") from exc

    def send_email(self, to_address: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["From"] = self.settings.super_admin_email
        msg["To"] = to_address
        msg["Subject"] = subject.strip()
        msg.set_content(body)

        with self._smtp_connection() as smtp:
            try:
                smtp.send_message(msg)
            except Exception as exc:
                raise EmailSendError(f"Email delivery failed: {exc}") from exc

    def fetch_inbox(self, limit: int = 20) -> List[EmailSummary]:
        return self._fetch_folder("INBOX", limit)

    def fetch_sent(self, limit: int = 20) -> List[EmailSummary]:
        folder = self.settings.imap_sent_folder or "INBOX"
        return self._fetch_folder(folder, limit)

    def _fetch_folder(self, folder: str, limit: int) -> List[EmailSummary]:
        with self._imap_connection() as imap:
            status, _ = imap.select(folder, readonly=True)
            if status != "OK":
                raise EmailReceiveError(f"Unable to access folder '{folder}'.")

            status, data = imap.search(None, "ALL")
            if status != "OK":
                raise EmailReceiveError("Failed to search mailbox.")

            message_ids = data[0].split()
            if not message_ids:
                return []

            latest_ids = list(reversed(message_ids))[:limit]
            summaries: List[EmailSummary] = []

            for uid in latest_ids:
                status, msg_data = imap.fetch(uid, "(RFC822)")
                if status != "OK" or not msg_data:
                    continue

                raw_email = msg_data[0][1]
                email_message = message_from_bytes(raw_email)
                summaries.append(
                    EmailSummary(
                        uid=uid.decode("utf-8", errors="ignore"),
                        subject=_decode_header(email_message.get("Subject")),
                        sender=_decode_header(email_message.get("From")),
                        recipient=_decode_header(email_message.get("To")),
                        date=_decode_header(email_message.get("Date")),
                        snippet=_extract_text_snippet(email_message),
                    )
                )

            return summaries
