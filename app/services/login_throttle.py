"""Login attempt throttling service to prevent brute force attacks."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class LoginAttempt:
    """Track login attempts for a specific identifier."""

    count: int = 0
    first_attempt: float = 0.0
    lockout_until: float = 0.0


class LoginThrottleService:
    """Service to throttle login attempts and prevent brute force attacks.

    Configuration:
        - max_attempts: Maximum login attempts before lockout (default: 5)
        - window_seconds: Time window to track attempts (default: 300 = 5 minutes)
        - lockout_seconds: How long to lock out after max attempts (default: 900 = 15 minutes)
    """

    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 300,
        lockout_seconds: int = 900,
    ):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._attempts: dict[str, LoginAttempt] = defaultdict(LoginAttempt)
        self._lock = Lock()

    def _get_key(self, email: str, ip: str) -> str:
        """Generate a key combining email and IP for tracking."""
        return f"{email.lower()}:{ip}"

    def _cleanup_old_attempts(self, now: float) -> None:
        """Remove expired attempt records."""
        keys_to_remove = []
        for key, attempt in self._attempts.items():
            if (
                attempt.lockout_until < now
                and now - attempt.first_attempt > self.window_seconds
            ):
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del self._attempts[key]

    def is_locked_out(self, email: str, ip: str) -> tuple[bool, int]:
        """Check if the email/IP combination is locked out.

        Returns:
            Tuple of (is_locked, remaining_seconds)
        """
        now = time.time()
        key = self._get_key(email, ip)

        with self._lock:
            self._cleanup_old_attempts(now)
            attempt = self._attempts.get(key)

            if attempt and attempt.lockout_until > now:
                remaining = int(attempt.lockout_until - now)
                return True, remaining

        return False, 0

    def record_failed_attempt(self, email: str, ip: str) -> tuple[bool, int, int]:
        """Record a failed login attempt.

        Returns:
            Tuple of (is_now_locked, remaining_attempts, lockout_seconds)
        """
        now = time.time()
        key = self._get_key(email, ip)

        with self._lock:
            self._cleanup_old_attempts(now)
            attempt = self._attempts[key]

            # Reset if window expired
            if now - attempt.first_attempt > self.window_seconds:
                attempt.count = 0
                attempt.first_attempt = now
                attempt.lockout_until = 0.0

            # First attempt in window
            if attempt.count == 0:
                attempt.first_attempt = now

            attempt.count += 1
            remaining = max(0, self.max_attempts - attempt.count)

            # Check if should lock out
            if attempt.count >= self.max_attempts:
                attempt.lockout_until = now + self.lockout_seconds
                return True, 0, self.lockout_seconds

            return False, remaining, 0

    def record_successful_login(self, email: str, ip: str) -> None:
        """Clear attempt records after successful login."""
        key = self._get_key(email, ip)
        with self._lock:
            if key in self._attempts:
                del self._attempts[key]


# Global singleton instance
login_throttle_service = LoginThrottleService()
