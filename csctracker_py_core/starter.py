import logging
import os
import time

import waitress
from waitress import wasyncore
from csctracker_queue_scheduler.services.scheduler_service import SchedulerService
from flask import Flask
from flask_cors import CORS
from flask_swagger_generator.generators.swagger_view import SwaggerView
from prometheus_flask_exporter import PrometheusMetrics

from csctracker_py_core.models.emuns.config import Config
from csctracker_py_core.repository.http_repository import HttpRepository
from csctracker_py_core.repository.remote_repository import RemoteRepository
from csctracker_py_core.utils.configs import Configs
from csctracker_py_core.utils.graceful_shutdown import GracefulShutdown
from csctracker_py_core.utils.interceptor import Interceptor
from csctracker_py_core.utils.version import Version


class Starter:
    def __init__(self, static_folder="static", save_request=False, is_bff=False):
        self.logger = logging.getLogger()
        self.app = Flask(__name__, static_folder=static_folder)
        try:
            os.environ.pop("FLASK_RUN_FROM_CLI")
        except:
            pass
        try:
            os.environ.pop("FLASK_ENV")
        except:
            pass
        SchedulerService.init(10)
        self.cors = CORS(self.app)
        self.app.config["CORS_HEADERS"] = "Content-Type"
        self.config = Configs(os.getenv("PROFILE", "dev"))
        shutdown_timeout = Configs.get_env_variable(Config.SHUTDOWN_TIMEOUT, default=30)
        self.graceful_shutdown = GracefulShutdown.get_instance(timeout=shutdown_timeout)
        self.graceful_shutdown.register_signals()
        self.remote_repository = RemoteRepository()
        self.http_repository = HttpRepository(remote_repository=self.remote_repository)
        self.interceptor = Interceptor(
            self.app, self.http_repository, save_request=save_request, is_bff=is_bff,
        )
        self.metrics = PrometheusMetrics(
            self.app,
            group_by="endpoint",
            default_labels={"application": Version.get_app_name()},
        )
        self._swagger_initialized = False

    @staticmethod
    def _get_int_env(key: Config, default: int) -> int:
        value = Configs.get_env_variable(key, default=default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _register_waitress_shutdown_hooks(graceful_shutdown: GracefulShutdown, server):
        def close_listener():
            # Close only the accepting socket so in-flight responses can still use server.trigger
            wasyncore.dispatcher.close(server)

        def finalize_server(remaining_timeout: float):
            deadline = time.time() + max(0.0, remaining_timeout)
            task_dispatcher = getattr(server, "task_dispatcher", None)
            if task_dispatcher is not None:
                task_dispatcher.shutdown(
                    cancel_pending=False,
                    timeout=max(0.1, deadline - time.time()),
                )

            server_map = getattr(server, "_map", None)
            if server_map is not None:
                while time.time() < deadline:
                    if not any(
                        getattr(ch, "total_outbufs_len", 0) > 0
                        for ch in list(server_map.values())
                    ):
                        break
                    time.sleep(0.01)

                trigger = getattr(server, "trigger", None)
                for ch in list(server_map.values()):
                    if ch is server or ch is trigger:
                        continue
                    if hasattr(ch, "close"):
                        try:
                            ch.close()
                        except Exception:
                            pass

            trigger = getattr(server, "trigger", None)
            if trigger is not None:
                try:
                    trigger.close()
                except Exception:
                    pass

        graceful_shutdown.set_server_close_hook(close_listener)
        graceful_shutdown.set_server_post_drain_hook(finalize_server)

    def register_shutdown_hook(self, callback):
        self.graceful_shutdown.register_shutdown_hook(callback)

    def get_graceful_shutdown(self):
        return self.graceful_shutdown

    def get_remote_repository(self):
        return self.remote_repository

    def get_http_repository(self):
        return self.http_repository

    def get_app(self):
        return self.app

    def start(self):
        if not self._swagger_initialized:
            SwaggerView.init(
                self.app,
                application_name=Version.get_app_name(),
                application_version=Version.get_version(),
                swagger_destination_path="swagger.yaml",
            )
            self._swagger_initialized = True

        port = self._get_int_env(Config.PORT, default=5000)

        if Configs.is_debug():
            self.logger.info(
                f"Starting Flask development server (DEBUG=1) on 0.0.0.0:{port}"
            )
            self.app.run(host="0.0.0.0", port=port)
            return

        threads = self._get_int_env(Config.WSGI_THREADS, default=32)
        channel_timeout = self._get_int_env(Config.WSGI_CHANNEL_TIMEOUT, default=600)
        self.logger.info(
            f"Starting Waitress WSGI server on 0.0.0.0:{port} "
            f"(threads={threads}, channel_timeout={channel_timeout}s)"
        )
        server = waitress.create_server(
            self.app,
            host="0.0.0.0",
            port=port,
            threads=threads,
            channel_timeout=channel_timeout,
        )
        self._register_waitress_shutdown_hooks(self.graceful_shutdown, server)
        server.run()
