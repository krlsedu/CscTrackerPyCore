import os
import unittest
from unittest.mock import MagicMock, patch

from csctracker_py_core.starter import Starter
from csctracker_py_core.utils.graceful_shutdown import GracefulShutdown


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
        self.assertIs(starter.get_graceful_shutdown()._server_close_hook, mock_server.close)

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
        shutdown.register_shutdown_hook(lambda: events.append("shutdown_hook"))

        shutdown.wait_for_drain(timeout=2, exit_process=False)
        self.assertEqual(events, ["server_close", "shutdown_hook"])

        # Subsequent drain must not call server_close again
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


if __name__ == "__main__":
    unittest.main()
