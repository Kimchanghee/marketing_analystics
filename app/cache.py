"""간단한 인메모리 캐싱 시스템"""
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Optional
import hashlib
import json


class SimpleCache:
    """간단한 TTL 기반 인메모리 캐시"""

    def __init__(self):
        self._cache = {}
        self._timestamps = {}

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        if key in self._cache:
            # TTL 체크
            if key in self._timestamps:
                if datetime.now() < self._timestamps[key]:
                    return self._cache[key]
                else:
                    # 만료된 캐시 삭제
                    del self._cache[key]
                    del self._timestamps[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """캐시에 값 저장 (기본 TTL: 5분)"""
        self._cache[key] = value
        self._timestamps[key] = datetime.now() + timedelta(seconds=ttl_seconds)

    def delete(self, key: str):
        """캐시에서 값 삭제"""
        if key in self._cache:
            del self._cache[key]
        if key in self._timestamps:
            del self._timestamps[key]

    def clear(self):
        """모든 캐시 삭제"""
        self._cache.clear()
        self._timestamps.clear()

    def cleanup_expired(self):
        """만료된 캐시 정리"""
        now = datetime.now()
        expired_keys = [
            key for key, timestamp in self._timestamps.items()
            if now >= timestamp
        ]
        for key in expired_keys:
            self.delete(key)


# 전역 캐시 인스턴스
cache = SimpleCache()


def cached(ttl_seconds: int = 300, key_prefix: str = ""):
    """함수 결과를 캐싱하는 데코레이터

    Args:
        ttl_seconds: 캐시 유효 시간 (초)
        key_prefix: 캐시 키 접두사
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = _generate_cache_key(func.__name__, key_prefix, args, kwargs)

            # 캐시에서 조회
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 캐시 미스 - 함수 실행
            result = func(*args, **kwargs)

            # 결과 캐싱
            cache.set(cache_key, result, ttl_seconds)

            return result
        return wrapper
    return decorator


def _generate_cache_key(func_name: str, prefix: str, args: tuple, kwargs: dict) -> str:
    """캐시 키 생성"""
    # args와 kwargs를 JSON으로 직렬화하여 해시 생성
    try:
        args_str = json.dumps(args, sort_keys=True, default=str)
        kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)
        combined = f"{func_name}:{args_str}:{kwargs_str}"
        hash_value = hashlib.md5(combined.encode()).hexdigest()
        return f"{prefix}:{hash_value}" if prefix else hash_value
    except (TypeError, ValueError):
        # 직렬화 불가능한 경우 간단한 키 사용
        return f"{prefix}:{func_name}:{id(args)}" if prefix else f"{func_name}:{id(args)}"
