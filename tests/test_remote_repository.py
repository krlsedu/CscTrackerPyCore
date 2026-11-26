import os
import unittest
from unittest.mock import MagicMock, patch

from csctracker_py_core.repository.remote_repository import RemoteRepository
from csctracker_py_core.starter import Starter
from csctracker_py_core.utils.graceful_shutdown import GracefulShutdown


class TestRemoteRepository(unittest.TestCase):
    def setUp(self):
        GracefulShutdown.reset_instance()
        self._env_backup = os.environ.copy()
        for key in (
            "URL_REPOSITORY",
            "REMOTE_REPOSITORY_TIMEOUT",
            "REMOTE_REPOSITORY_POOL_CONNECTIONS",
            "REMOTE_REPOSITORY_POOL_MAXSIZE",
        ):
            os.environ.pop(key, None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env_backup)
        GracefulShutdown.reset_instance()

    @staticmethod
    def _ok_response(payload):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = payload
        return resp

    def test_default_timeout_600_and_session_reused_across_all_methods(self):
        os.environ["URL_REPOSITORY"] = "http://repository:5000"
        repo = RemoteRepository()
        try:
            session_id = id(repo.session)
            self.assertEqual(repo.timeout, 600)

            post_resp = self._ok_response({"ok": True})
            get_resp = self._ok_response([{"id": 1}])

            with patch.object(repo.session, "post", return_value=post_resp) as mock_post, patch.object(
                repo.session, "get", return_value=get_resp
            ) as mock_get:
                repo.insert("orders", {"id": 1}, headers={"x": "1"})
                repo.update("orders", keys=["id"], data={"id": 1}, headers={"x": "1"})
                repo.delete("orders", keys=["id"], data={"id": 1}, headers={"x": "1"})
                repo.get_object("orders", keys=["id"], data={"id": 1}, headers={"x": "1"})
                repo.get_objects("orders", keys=["id"], data={"id": 1}, headers={"x": "1"})
                repo.execute_select("SELECT 1", headers={"x": "1"})

            self.assertEqual(id(repo.session), session_id)
            self.assertEqual(mock_post.call_count, 4)
            self.assertEqual(mock_get.call_count, 2)

            for call in mock_post.call_args_list:
                self.assertEqual(call.kwargs["timeout"], 600)
            for call in mock_get.call_args_list:
                self.assertEqual(call.kwargs["timeout"], 600)
        finally:
            repo.close()

    def test_timeout_env_override_int_and_float(self):
        os.environ["REMOTE_REPOSITORY_TIMEOUT"] = "120"
        repo_int = RemoteRepository()
        try:
            self.assertEqual(repo_int.timeout, 120)
            self.assertIsInstance(repo_int.timeout, int)
        finally:
            repo_int.close()

        os.environ["REMOTE_REPOSITORY_TIMEOUT"] = "45.5"
        repo_float = RemoteRepository()
        try:
            self.assertEqual(repo_float.timeout, 45.5)
            self.assertIsInstance(repo_float.timeout, float)
        finally:
            repo_float.close()

    def test_timeout_env_invalid_values_fallback_to_600(self):
        for invalid in ("", "   ", "abc", "0", "-5", "-0.5", "nan", "inf"):
            with self.subTest(value=invalid):
                os.environ["REMOTE_REPOSITORY_TIMEOUT"] = invalid
                repo = RemoteRepository()
                try:
                    self.assertEqual(repo.timeout, 600)
                finally:
                    repo.close()

    def test_pool_adapter_defaults_and_env_overrides_with_fallback(self):
        repo_default = RemoteRepository()
        try:
            for scheme in ("http://", "https://"):
                adapter = repo_default.session.get_adapter(scheme)
                self.assertEqual(adapter._pool_connections, 10)
                self.assertEqual(adapter._pool_maxsize, 32)
        finally:
            repo_default.close()

        os.environ["REMOTE_REPOSITORY_POOL_CONNECTIONS"] = "16"
        os.environ["REMOTE_REPOSITORY_POOL_MAXSIZE"] = "64"
        repo_custom = RemoteRepository()
        try:
            for scheme in ("http://", "https://"):
                adapter = repo_custom.session.get_adapter(scheme)
                self.assertEqual(adapter._pool_connections, 16)
                self.assertEqual(adapter._pool_maxsize, 64)
        finally:
            repo_custom.close()

        os.environ["REMOTE_REPOSITORY_POOL_CONNECTIONS"] = ""
        os.environ["REMOTE_REPOSITORY_POOL_MAXSIZE"] = "0"
        repo_fallback = RemoteRepository()
        try:
            adapter = repo_fallback.session.get_adapter("http://")
            self.assertEqual(adapter._pool_connections, 10)
            self.assertEqual(adapter._pool_maxsize, 32)
        finally:
            repo_fallback.close()

    def test_close_and_starter_graceful_shutdown_closes_session(self):
        repo = RemoteRepository()
        with patch.object(repo.session, "close") as mock_close:
            repo.close()
        mock_close.assert_called_once()

        starter = Starter(save_request=False)
        with patch.object(starter.remote_repository.session, "close") as mock_starter_close:
            starter.get_graceful_shutdown().wait_for_drain(timeout=2, exit_process=False)
        mock_starter_close.assert_called_once()

    def test_sanitizes_framing_headers_in_requests(self):
        repo = RemoteRepository()
        try:
            raw_headers = {
                "Host": "repository:5000",
                "Content-Length": "450",
                "Transfer-Encoding": "chunked",
                "Connection": "keep-alive",
                "Authorization": "Bearer tok",
                "userName": "u@csc",
                "x-correlation-id": "cid-1",
            }
            ok_resp = self._ok_response({"id": 1})
            with patch.object(repo.session, "get", return_value=ok_resp) as mock_get, patch.object(
                repo.session, "post", return_value=ok_resp
            ) as mock_post:
                repo.get_object("users", data={"email": "u@csc"}, headers=raw_headers)
                repo.insert("orders", {"id": 1}, headers=raw_headers)
                repo.execute_select("SELECT 1", headers=raw_headers)

            expected = {
                "Authorization": "Bearer tok",
                "userName": "u@csc",
                "x-correlation-id": "cid-1",
            }
            self.assertEqual(mock_get.call_args.kwargs["headers"], expected)
            for call in mock_post.call_args_list:
                self.assertEqual(call.kwargs["headers"], expected)
        finally:
            repo.close()


if __name__ == "__main__":
    unittest.main()
