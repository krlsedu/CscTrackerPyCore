import unittest
from unittest.mock import MagicMock, patch

from flask import Flask

from csctracker_py_core.utils.request_info import RequestInfo


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


if __name__ == "__main__":
    unittest.main()
