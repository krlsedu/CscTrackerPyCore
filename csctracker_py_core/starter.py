import logging
import os
import socket
import threading
import time

import waitress
from waitress import server as waitress_server
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
        self.graceful_shutdown.register_shutdown_hook(self.remote_repository.close)
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
    def _run_on_waitress_loop(triggers, callback, timeout: float = 1.5):
        executed = False
        exec_lock = threading.Lock()

        def _run_once():
            nonlocal executed
            with exec_lock:
                if executed:
                    return
                executed = True
            callback()

        for trigger in triggers:
            if not getattr(trigger, "_closed", False) and hasattr(trigger, "pull_trigger"):
                done = threading.Event()

                def _thunk():
                    try:
                        _run_once()
                    finally:
                        done.set()

                try:
                    trigger.pull_trigger(_thunk)
                    if done.wait(timeout=timeout):
                        return
                except Exception:
                    pass

        _run_once()

    @staticmethod
    def _register_waitress_shutdown_hooks(graceful_shutdown: GracefulShutdown, server):
        server_map = getattr(server, "_map", None)
        if server_map is None:
            server_map = getattr(server, "map", None)

        def _collect_servers_and_triggers():
            servers = []
            triggers = []
            if isinstance(server_map, dict):
                for obj in list(server_map.values()):
                    if isinstance(obj, waitress_server.BaseWSGIServer):
                        servers.append(obj)
                        trig = getattr(obj, "trigger", None)
                        if trig is not None and trig not in triggers:
                            triggers.append(trig)
            if not servers and isinstance(server, wasyncore.dispatcher):
                servers.append(server)
                trig = getattr(server, "trigger", None)
                if trig is not None and trig not in triggers:
                    triggers.append(trig)
            return servers, triggers

        known_servers, known_triggers = _collect_servers_and_triggers()

        def _get_servers_and_triggers():
            servers, triggers = _collect_servers_and_triggers()
            for srv in known_servers:
                if srv not in servers:
                    servers.append(srv)
            for trig in known_triggers:
                if trig not in triggers:
                    triggers.append(trig)
            return servers, triggers

        def close_listener():
            servers, triggers = _get_servers_and_triggers()

            def _close_listeners_sync():
                # Close only accepting sockets on the wasyncore thread so select() releases
                # kernel socket refs immediately on Linux while keeping trigger open for drain.
                for srv in servers:
                    sock = getattr(srv, "socket", None)
                    if sock is not None:
                        try:
                            sock.shutdown(socket.SHUT_RDWR)
                        except OSError:
                            pass
                    wasyncore.dispatcher.close(srv)

            Starter._run_on_waitress_loop(triggers, _close_listeners_sync, timeout=1.5)

        def finalize_server(remaining_timeout: float):
            deadline = time.time() + max(0.0, remaining_timeout)
            task_dispatcher = getattr(server, "task_dispatcher", None)
            if task_dispatcher is not None:
                task_dispatcher.shutdown(
                    cancel_pending=False,
                    timeout=max(0.1, deadline - time.time()),
                )

            if isinstance(server_map, dict):
                while time.time() < deadline:
                    if not any(
                        getattr(ch, "total_outbufs_len", 0) > 0
                        for ch in list(server_map.values())
                    ):
                        break
                    time.sleep(0.01)

            servers, triggers = _get_servers_and_triggers()
            if not triggers:
                trig = getattr(server, "trigger", None)
                if trig is not None:
                    triggers.append(trig)

            def _close_remaining_sync():
                if isinstance(server_map, dict):
                    for ch in list(server_map.values()):
                        if ch in servers or ch in triggers:
                            continue
                        if hasattr(ch, "close"):
                            try:
                                ch.close()
                            except Exception:
                                pass

                for trig in triggers:
                    if hasattr(trig, "close"):
                        try:
                            trig.close()
                        except Exception:
                            pass

            Starter._run_on_waitress_loop(
                triggers,
                _close_remaining_sync,
                timeout=min(1.5, max(0.2, deadline - time.time())),
            )

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
