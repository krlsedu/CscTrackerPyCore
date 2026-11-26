import hashlib
import logging
import os
import threading
import time
import uuid
from typing import Optional

import requests
from flask import g, request

from csctracker_py_core.utils.version import Version

logger = logging.getLogger(__name__)

_HOP_BY_HOP_OR_FRAMING_HEADERS = frozenset(
    {"content-length", "host", "transfer-encoding", "connection"}
)


class CaseInsensitiveHeaderDict(dict):
    """Subclasse de dict com lookup case-insensitive para headers HTTP."""

    def __init__(self, initial=None, **kwargs):
        super().__init__()
        self._lower_to_key: dict[str, str] = {}
        if initial is not None:
            self.update(initial)
        if kwargs:
            self.update(kwargs)

    def _resolve_key(self, key):
        if isinstance(key, str):
            return self._lower_to_key.get(key.lower(), key)
        return key

    def __setitem__(self, key, value):
        if isinstance(key, str):
            lower = key.lower()
            existing = self._lower_to_key.get(lower)
            if existing is not None and existing != key:
                super().__delitem__(existing)
            self._lower_to_key[lower] = key
        super().__setitem__(key, value)

    def __getitem__(self, key):
        return super().__getitem__(self._resolve_key(key))

    def __delitem__(self, key):
        resolved = self._resolve_key(key)
        super().__delitem__(resolved)
        if isinstance(resolved, str):
            self._lower_to_key.pop(resolved.lower(), None)

    def __contains__(self, key):
        if isinstance(key, str):
            return key.lower() in self._lower_to_key
        return super().__contains__(key)

    def get(self, key, default=None):
        return super().get(self._resolve_key(key), default)

    def pop(self, key, *args):
        if len(args) > 1:
            raise TypeError(f"pop expected at most 2 arguments, got {1 + len(args)}")
        resolved = self._resolve_key(key)
        if super().__contains__(resolved):
            val = super().pop(resolved)
            if isinstance(resolved, str):
                self._lower_to_key.pop(resolved.lower(), None)
            return val
        if args:
            return args[0]
        raise KeyError(key)

    def setdefault(self, key, default=None):
        resolved = self._resolve_key(key)
        if super().__contains__(resolved):
            return super().__getitem__(resolved)
        self[key] = default
        return default

    def update(self, other=(), **kwargs):
        if hasattr(other, "items"):
            for k, v in other.items():
                self[k] = v
        else:
            for k, v in other:
                self[k] = v
        for k, v in kwargs.items():
            self[k] = v

    def clear(self):
        self._lower_to_key.clear()
        super().clear()

    def copy(self):
        return CaseInsensitiveHeaderDict(self)

    def popitem(self):
        key, val = super().popitem()
        if isinstance(key, str):
            self._lower_to_key.pop(key.lower(), None)
        return key, val


class RequestInfo:
    _user_email_cache: dict[str, tuple[Optional[str], float]] = {}
    _user_email_cache_lock = threading.Lock()
    _USER_EMAIL_CACHE_MAX_SIZE = 2048

    @staticmethod
    def clear_user_email_cache():
        with RequestInfo._user_email_cache_lock:
            RequestInfo._user_email_cache.clear()

    @staticmethod
    def get_user_email(
        auth_url: Optional[str] = None, cache_ttl_seconds: int = 300
    ) -> Optional[str]:
        try:
            auth_header = RequestInfo.get_header("Authorization")
        except RuntimeError:
            return None

        if not auth_header or not isinstance(auth_header, str):
            return None

        parts = auth_header.strip().split(None, 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        token = parts[1].strip()
        if not token:
            return None

        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        now = time.monotonic()

        if cache_ttl_seconds > 0:
            with RequestInfo._user_email_cache_lock:
                cached = RequestInfo._user_email_cache.get(token_hash)
                if cached is not None:
                    cached_email, expires_at = cached
                    if now < expires_at:
                        return cached_email
                    RequestInfo._user_email_cache.pop(token_hash, None)

        base_url = (
            auth_url
            or os.getenv("AUTH_URL")
            or "https://auth.csctracker.com"
        ).rstrip("/")
        client_id = os.getenv("AUTH_CLIENT_ID") or "OAUTH"
        client_secret = os.getenv("AUTH_CLIENT_SECRET") or "OAUTH"

        try:
            response = requests.post(
                f"{base_url}/oauth/check_token",
                data={"token": token},
                auth=(client_id, client_secret),
                timeout=5,
            )
        except Exception as exc:
            logger.warning(
                "Falha ao consultar /oauth/check_token para resolver e-mail do usuário: %s",
                type(exc).__name__,
            )
            return None

        if response.status_code != 200:
            return None

        try:
            body = response.json()
        except Exception:
            return None

        if not isinstance(body, dict) or body.get("active", True) is False:
            return None

        user_name = body.get("user_name")
        email = user_name.strip().lower() if isinstance(user_name, str) else ""
        if not email:
            return None

        if cache_ttl_seconds > 0:
            expires_at = time.monotonic() + cache_ttl_seconds
            with RequestInfo._user_email_cache_lock:
                if len(RequestInfo._user_email_cache) >= RequestInfo._USER_EMAIL_CACHE_MAX_SIZE:
                    current_time = time.monotonic()
                    expired_keys = [
                        k
                        for k, (_, exp) in RequestInfo._user_email_cache.items()
                        if current_time >= exp
                    ]
                    for k in expired_keys:
                        RequestInfo._user_email_cache.pop(k, None)
                    if len(RequestInfo._user_email_cache) >= RequestInfo._USER_EMAIL_CACHE_MAX_SIZE:
                        RequestInfo._user_email_cache.clear()
                RequestInfo._user_email_cache[token_hash] = (email, expires_at)

        return email

    @staticmethod
    def get_request_id(create_new=True):
        try:
            request_id_ = g.correlation_id
        except Exception:
            try:
                thread = threading.current_thread()
                request_id_ = thread.__getattribute__("correlation_id")
            except Exception:
                if create_new:
                    request_id_ = f"{Version.get_app_name()}-{str(uuid.uuid4())}"
                else:
                    request_id_ = None

        return request_id_

    @staticmethod
    def get_correlation_id():
        return request.headers.get(
            "x-correlation-id", f"{Version.get_app_name()}-{str(uuid.uuid4())}"
        )

    @staticmethod
    def get_header(header_name: str):
        _headers = request.headers
        _header = next((v for k, v in _headers.items() if k.lower() == header_name.lower()), None)
        return _header

    @staticmethod
    def get_json_body():
        return request.json

    @staticmethod
    def get_args():
        return request.args

    @staticmethod
    def get_headers():
        headers = request.headers
        headers_ = CaseInsensitiveHeaderDict()
        has_correlation_id = False
        for key in headers.keys():
            if key.lower() in _HOP_BY_HOP_OR_FRAMING_HEADERS:
                continue
            if key.lower() == "x-correlation-id":
                has_correlation_id = True
            headers_[key] = headers.get(key)
        if not has_correlation_id:
            headers_["x-correlation-id"] = RequestInfo.get_request_id(True)
        return headers_