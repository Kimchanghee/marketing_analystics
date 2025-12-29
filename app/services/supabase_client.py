"""Supabase client for direct API access.

This module provides a Supabase client for operations that require direct API access
beyond SQLAlchemy/SQLModel database operations, such as:
- Storage bucket operations
- Realtime subscriptions
- Edge functions
- Direct table queries with RLS
"""

from __future__ import annotations

import logging
from typing import Optional

from ..config import get_settings

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Client for Supabase API operations."""

    def __init__(self):
        self.settings = get_settings()
        self._client = None

    @property
    def is_configured(self) -> bool:
        """Check if Supabase is properly configured."""
        return bool(self.settings.supabase_url and self.settings.supabase_anon_key)

    @property
    def client(self):
        """Lazy-initialize Supabase client."""
        if self._client is None and self.is_configured:
            try:
                from supabase import create_client
                self._client = create_client(
                    self.settings.supabase_url,
                    self.settings.supabase_anon_key
                )
                logger.info("Supabase client initialized successfully")
            except ImportError:
                logger.warning("supabase-py package not installed. Install with: pip install supabase")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
        return self._client

    @property
    def admin_client(self):
        """Get admin client with service role key for privileged operations."""
        if not self.settings.supabase_service_role_key:
            logger.warning("Supabase service role key not configured")
            return None
        try:
            from supabase import create_client
            return create_client(
                self.settings.supabase_url,
                self.settings.supabase_service_role_key
            )
        except ImportError:
            logger.warning("supabase-py package not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to create admin client: {e}")
            return None

    # ===== Storage Operations =====

    def upload_file(
        self,
        bucket: str,
        path: str,
        file_data: bytes,
        content_type: str = "application/octet-stream",
    ) -> Optional[str]:
        """Upload file to Supabase Storage.

        Args:
            bucket: Storage bucket name
            path: File path within bucket
            file_data: File contents as bytes
            content_type: MIME type

        Returns:
            Public URL if successful, None otherwise
        """
        if not self.client:
            return None

        try:
            self.client.storage.from_(bucket).upload(
                path,
                file_data,
                {"content-type": content_type}
            )
            return self.get_public_url(bucket, path)
        except Exception as e:
            logger.error(f"Failed to upload file to {bucket}/{path}: {e}")
            return None

    def get_public_url(self, bucket: str, path: str) -> Optional[str]:
        """Get public URL for a file.

        Args:
            bucket: Storage bucket name
            path: File path within bucket

        Returns:
            Public URL if available, None otherwise
        """
        if not self.client:
            return None

        try:
            return self.client.storage.from_(bucket).get_public_url(path)
        except Exception as e:
            logger.error(f"Failed to get public URL for {bucket}/{path}: {e}")
            return None

    def delete_file(self, bucket: str, paths: list[str]) -> bool:
        """Delete files from Supabase Storage.

        Args:
            bucket: Storage bucket name
            paths: List of file paths to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False

        try:
            self.client.storage.from_(bucket).remove(paths)
            return True
        except Exception as e:
            logger.error(f"Failed to delete files from {bucket}: {e}")
            return False

    # ===== Database Query Helper =====

    def query(self, table: str):
        """Get a query builder for a table.

        Args:
            table: Table name

        Returns:
            Supabase query builder
        """
        if not self.client:
            return None
        return self.client.table(table)

    def rpc(self, function_name: str, params: dict = None):
        """Call a Supabase database function (RPC).

        Args:
            function_name: Name of the database function
            params: Parameters to pass to the function

        Returns:
            Function result
        """
        if not self.client:
            return None

        try:
            return self.client.rpc(function_name, params or {}).execute()
        except Exception as e:
            logger.error(f"RPC call to {function_name} failed: {e}")
            return None

    # ===== Auth Helper (Optional) =====

    def get_user_by_email(self, email: str):
        """Get user from Supabase Auth by email.

        Note: This uses the admin client and service role key.
        """
        admin = self.admin_client
        if not admin:
            return None

        try:
            response = admin.auth.admin.list_users()
            for user in response:
                if user.email == email:
                    return user
            return None
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}")
            return None


# Global singleton instance
supabase_client = SupabaseClient()
