import json
import unittest
from unittest.mock import MagicMock, patch

from flask import Flask

from csctracker_py_core.repository.http_repository import HttpRepository
from csctracker_py_core.repository.remote_repository import RemoteRepository
from csctracker_py_core.utils.request_info import CaseInsensitiveHeaderDict, RequestInfo


class TestRequestInfoGetUserEmail(unittest.TestCase):
    def setUp(self):
        RequestInfo.clear_user_email_cache()
        self.app = Flask(__name__)

    def tearDown(self):
        RequestInfo.clear_user_email_cache()

    def test_outside_flask_context_returns_none(self):
        self.assertIsNone(RequestInfo.get_user_email())

    def test_missing_or_non_bearer_authorization_returns_none(self):
        with self.app.test_request_context("/"):
            self.assertIsNone(RequestInfo.get_user_email())

        with self.app.test_request_context("/", headers={"Authorization": "Basic abc123"}):
            self.assertIsNone(RequestInfo.get_user_email())

        with self.app.test_request_context("/", headers={"Authorization": "Bearer   "}):
            self.assertIsNone(RequestInfo.get_user_email())

    @patch("csctracker_py_core.utils.request_info.requests.post")
    def test_valid_token_and_cache_hit(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "active": True,
            "user_name": "  User@Example.COM ",
        }
        mock_post.return_value = mock_response

        with self.app.test_request_context(
            "/", headers={"Authorization": "Bearer tok-valid-123"}
        ):
            email_1 = RequestInfo.get_user_email(auth_url="https://auth.local")
            email_2 = RequestInfo.get_user_email(auth_url="https://auth.local")

        self.assertEqual(email_1, "user@example.com")
        self.assertEqual(email_2, "user@example.com")
        self.assertEqual(mock_post.call_count, 1)
        mock_post.assert_called_once_with(
            "https://auth.local/oauth/check_token",
            data={"token": "tok-valid-123"},
            auth=("OAUTH", "OAUTH"),
            timeout=5,
        )

    @patch("csctracker_py_core.utils.request_info.time.monotonic")
    @patch("csctracker_py_core.utils.request_info.requests.post")
    def test_cache_expiration_refetches_token(self, mock_post, mock_monotonic):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"active": True, "user_name": "alice@csc.com"}
        mock_post.return_value = mock_response

        # 1st call: check (100.0) + store (100.0 -> exp 160.0)
        # 2nd call: check (161.0 >= 160.0 -> expired) + store (161.0)
        mock_monotonic.side_effect = [100.0, 100.0, 161.0, 161.0]

        with self.app.test_request_context(
            "/", headers={"Authorization": "Bearer tok-ttl"}
        ):
            self.assertEqual(
                RequestInfo.get_user_email(cache_ttl_seconds=60), "alice@csc.com"
            )
            self.assertEqual(
                RequestInfo.get_user_email(cache_ttl_seconds=60), "alice@csc.com"
            )

        self.assertEqual(mock_post.call_count, 2)

    @patch("csctracker_py_core.utils.request_info.requests.post")
    def test_invalid_or_inactive_token_returns_none(self, mock_post):
        mock_401 = MagicMock()
        mock_401.status_code = 401
        mock_post.return_value = mock_401

        with self.app.test_request_context(
            "/", headers={"Authorization": "Bearer tok-invalid"}
        ):
            self.assertIsNone(RequestInfo.get_user_email())

        mock_inactive = MagicMock()
        mock_inactive.status_code = 200
        mock_inactive.json.return_value = {"active": False, "user_name": "bob@csc.com"}
        mock_post.return_value = mock_inactive

        with self.app.test_request_context(
            "/", headers={"Authorization": "Bearer tok-inactive"}
        ):
            self.assertIsNone(RequestInfo.get_user_email())

    @patch("csctracker_py_core.utils.request_info.requests.post")
    def test_network_error_returns_none_without_crashing(self, mock_post):
        mock_post.side_effect = RuntimeError("connection refused")

        with self.app.test_request_context(
            "/", headers={"Authorization": "Bearer tok-err"}
        ):
            self.assertIsNone(RequestInfo.get_user_email())

    def test_get_headers_strips_framing_headers_and_is_case_insensitive_dict(self):
        http_repo = HttpRepository(RemoteRepository())
        try:
            with self.app.test_request_context(
                "/heartbeat",
                method="POST",
                data='{"a": 1}',
                content_type="application/json",
                headers={
                    "Host": "usage-info-ai:5000",
                    "Content-Length": "8",
                    "Transfer-Encoding": "chunked",
                    "Connection": "keep-alive",
                    "Authorization": "Bearer tok-abc",
                    "userName": "u@csc",
                },
            ):
                ri_headers = RequestInfo.get_headers()
                hr_headers = http_repo.get_headers()

            for h in (ri_headers, hr_headers):
                self.assertIsInstance(h, dict)
                self.assertIsInstance(h, CaseInsensitiveHeaderDict)
                lower_keys = {k.lower() for k in h.keys()}
                self.assertNotIn("content-length", lower_keys)
                self.assertNotIn("host", lower_keys)
                self.assertNotIn("transfer-encoding", lower_keys)
                self.assertNotIn("connection", lower_keys)
                self.assertEqual(h.get("userName"), "u@csc")
                self.assertEqual(h.get("USERNAME"), "u@csc")
                self.assertEqual(h["userName"], "u@csc")
                self.assertIn("userName", h)
                self.assertEqual(h.get("authorization"), "Bearer tok-abc")
                self.assertIsNotNone(h.get("X-Correlation-Id"))
                parsed = json.loads(json.dumps(h))
                self.assertEqual(len(parsed), len(h))

                copied = h.copy()
                self.assertIsInstance(copied, CaseInsensitiveHeaderDict)
                copied["USERNAME"] = "other@csc"
                self.assertEqual(copied["userName"], "other@csc")
                self.assertEqual(
                    sum(1 for k in copied.keys() if k.lower() == "username"), 1
                )
                self.assertEqual(copied.pop("userName"), "other@csc")
                self.assertNotIn("USERNAME", copied)
        finally:
            http_repo.remote_repository.close()


if __name__ == "__main__":
    unittest.main()
