import json
import logging
import os
import socket
import threading
import time
import unittest
import urllib.request
import warnings
from unittest.mock import MagicMock, patch

import waitress
from bs4 import BeautifulSoup
from flask import Flask

from csctracker_py_core.repository.http_repository import HttpRepository
from csctracker_py_core.repository.remote_repository import RemoteRepository
from csctracker_py_core.starter import Starter
from csctracker_py_core.utils.configs import CustomJsonFormatter
from csctracker_py_core.utils.graceful_shutdown import GracefulShutdown
from csctracker_py_core.utils.interceptor import Interceptor


class TestStarterWsgi(unittest.TestCase):
    def setUp(self):
        GracefulShutdown.reset_instance()
        self._env_backup = os.environ.copy()
        for key in ("DEBUG", "PORT", "WSGI_THREADS", "WSGI_CHANNEL_TIMEOUT"):
            os.environ.pop(key, None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env_backup)
        GracefulShutdown.reset_instance()

    @patch("csctracker_py_core.starter.SwaggerView.init")
    @patch("csctracker_py_core.starter.waitress.create_server")
    def test_start_uses_waitress_by_default(self, mock_create_server, mock_swagger_init):
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        starter = Starter(save_request=False)
        with patch.object(starter.app, "run") as mock_flask_run:
            starter.start()

        mock_swagger_init.assert_called_once()
        mock_flask_run.assert_not_called()
        mock_create_server.assert_called_once_with(
            starter.app,
            host="0.0.0.0",
            port=5000,
            threads=32,
            channel_timeout=600,
        )
        mock_server.run.assert_called_once()
        shutdown = starter.get_graceful_shutdown()
        self.assertTrue(callable(shutdown._server_close_hook))
        self.assertTrue(callable(shutdown._server_post_drain_hook))

    @patch("csctracker_py_core.starter.SwaggerView.init")
    @patch("csctracker_py_core.starter.waitress.create_server")
    def test_start_respects_wsgi_env_overrides(self, mock_create_server, mock_swagger_init):
        os.environ["PORT"] = "8085"
        os.environ["WSGI_THREADS"] = "64"
        os.environ["WSGI_CHANNEL_TIMEOUT"] = "900"
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        starter = Starter(save_request=False)
        starter.start()

        mock_create_server.assert_called_once_with(
            starter.app,
            host="0.0.0.0",
            port=8085,
            threads=64,
            channel_timeout=900,
        )
        mock_server.run.assert_called_once()

    @patch("csctracker_py_core.starter.SwaggerView.init")
    @patch("csctracker_py_core.starter.waitress.create_server")
    def test_start_falls_back_to_defaults_on_invalid_int_envs(
        self, mock_create_server, mock_swagger_init
    ):
        os.environ["PORT"] = ""
        os.environ["WSGI_THREADS"] = "invalid"
        os.environ["WSGI_CHANNEL_TIMEOUT"] = ""
        mock_server = MagicMock()
        mock_create_server.return_value = mock_server

        starter = Starter(save_request=False)
        starter.start()

        mock_create_server.assert_called_once_with(
            starter.app,
            host="0.0.0.0",
            port=5000,
            threads=32,
            channel_timeout=600,
        )

    @patch("csctracker_py_core.starter.SwaggerView.init")
    @patch("csctracker_py_core.starter.waitress.create_server")
    def test_start_uses_werkzeug_when_debug_is_1(
        self, mock_create_server, mock_swagger_init
    ):
        os.environ["DEBUG"] = "1"
        os.environ["PORT"] = "5050"

        starter = Starter(save_request=False)
        with patch.object(starter.app, "run") as mock_flask_run:
            starter.start()

        mock_swagger_init.assert_called_once()
        mock_create_server.assert_not_called()
        mock_flask_run.assert_called_once_with(host="0.0.0.0", port=5050)

    @patch("csctracker_py_core.starter.SwaggerView.init")
    @patch("csctracker_py_core.starter.waitress.create_server")
    def test_swagger_init_is_idempotent(self, mock_create_server, mock_swagger_init):
        mock_create_server.return_value = MagicMock()

        starter = Starter(save_request=False)
        starter.start()
        starter.start()

        mock_swagger_init.assert_called_once()

    def test_graceful_shutdown_closes_server_before_hooks(self):
        shutdown = GracefulShutdown.get_instance(timeout=5)
        events = []

        shutdown.set_server_close_hook(lambda: events.append("server_close"))
        shutdown.set_server_post_drain_hook(lambda rem: events.append("post_drain"))
        shutdown.register_shutdown_hook(lambda: events.append("shutdown_hook"))

        shutdown.wait_for_drain(timeout=2, exit_process=False)
        self.assertEqual(events, ["server_close", "post_drain", "shutdown_hook"])

        # Subsequent drain must not call server_close or post_drain again
        events.clear()
        shutdown.wait_for_drain(timeout=2, exit_process=False)
        self.assertEqual(events, ["shutdown_hook"])

    def test_graceful_shutdown_continues_if_server_close_raises(self):
        shutdown = GracefulShutdown.get_instance(timeout=5)
        hook_called = []

        def broken_close():
            raise RuntimeError("socket already closed")

        shutdown.set_server_close_hook(broken_close)
        shutdown.register_shutdown_hook(lambda: hook_called.append(True))

        shutdown.wait_for_drain(timeout=2, exit_process=False)
        self.assertEqual(hook_called, [True])

    def test_custom_json_formatter_python_json_logger_v4(self):
        formatter = CustomJsonFormatter(
            "%(levelname)s %(name)s %(requestId)s %(appName)s %(message)s"
        )
        record = logging.LogRecord(
            "test_logger", logging.INFO, __file__, 42, "hello json", (), None
        )
        parsed = json.loads(formatter.format(record))

        self.assertEqual(parsed["message"], "hello json")
        self.assertEqual(parsed["levelname"], "INFO")
        self.assertIn("requestId", parsed)
        self.assertIn("appName", parsed)
        self.assertIn("appVersion", parsed)
        self.assertIn("name", parsed)

    def test_interceptor_returns_503_connection_close_when_shutting_down(self):
        shutdown = GracefulShutdown.get_instance(timeout=5)
        app = Flask(__name__)
        Interceptor(app, HttpRepository(RemoteRepository()), save_request=False)

        @app.route("/ping")
        def ping():
            return {"status": "ok"}

        shutdown.is_shutting_down = True
        resp = app.test_client().get("/ping")

        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.headers.get("Connection"), "close")
        self.assertEqual(resp.get_json(), {"error": "Service shutting down"})
        self.assertEqual(shutdown.active_requests, 0)

    def test_http_repository_find_value_text_with_modern_bs4(self):
        html = "<div><span>Label</span><strong>42,50</strong></div>"
        soup = BeautifulSoup(html, "html.parser")
        repo = HttpRepository(RemoteRepository())

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            value = repo.find_value(soup, "Label", "text", parents=2, children=0)

        self.assertEqual(value, "42,50")
        bs4_deprecations = [
            w for w in caught if issubclass(w.category, DeprecationWarning)
        ]
        self.assertEqual(bs4_deprecations, [])

    def test_waitress_real_drain_flushes_inflight_request_without_trigger_error(self):
        shutdown = GracefulShutdown.get_instance(timeout=5)
        app = Flask(__name__)
        Interceptor(app, HttpRepository(RemoteRepository()), save_request=False)

        started = threading.Event()
        release = threading.Event()

        @app.route("/slow")
        def slow():
            started.set()
            release.wait(timeout=4)
            return {"status": "completed"}

        server = waitress.create_server(app, host="127.0.0.1", port=0, threads=4)
        Starter._register_waitress_shutdown_hooks(shutdown, server)
        port = getattr(server, "effective_port", None) or server.getsockname()[1]

        server_thread = threading.Thread(target=server.run, daemon=True)
        server_thread.start()

        response_result = {}

        def do_request():
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/slow", timeout=5
                ) as resp:
                    response_result["status"] = resp.status
                    response_result["body"] = json.loads(resp.read().decode("utf-8"))
            except Exception as exc:
                response_result["error"] = exc

        req_thread = threading.Thread(target=do_request, daemon=True)
        req_thread.start()
        self.assertTrue(started.wait(timeout=2))

        shutdown.is_shutting_down = True
        drain_thread = threading.Thread(
            target=shutdown.wait_for_drain,
            kwargs={"timeout": 5, "exit_process": False},
            daemon=True,
        )
        drain_thread.start()

        deadline = time.time() + 2
        while (server.accepting or server.socket is not None) and time.time() < deadline:
            time.sleep(0.01)
        self.assertFalse(server.accepting)
        self.assertIsNone(server.socket)

        with self.assertRaises(OSError):
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                pass

        release.set()
        req_thread.join(timeout=5)
        drain_thread.join(timeout=5)
        server_thread.join(timeout=5)

        self.assertNotIn("error", response_result)
        self.assertEqual(response_result.get("status"), 200)
        self.assertEqual(response_result.get("body"), {"status": "completed"})
        self.assertEqual(shutdown.active_requests, 0)
        self.assertFalse(drain_thread.is_alive())
        self.assertFalse(server_thread.is_alive())


if __name__ == "__main__":
    unittest.main()
