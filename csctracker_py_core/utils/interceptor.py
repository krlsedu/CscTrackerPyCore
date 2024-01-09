import logging
import threading
import time
import uuid

from flask import Flask, request, g

from csctracker_py_core.models.emuns.config import Config
from csctracker_py_core.utils.configs import Configs
from csctracker_py_core.utils.version import Version


class Interceptor:
    def __init__(self, app: Flask):
        self.logger = logging.getLogger()
        self.app = app
        self.__init()

    def __init(self):
        @self.app.before_request
        def start_timer():
            g.start = time.time()
            correlation_id = request.headers.get('X-Correlation-Id', str(uuid.uuid4()))
            g.correlation_id = correlation_id
            threading.local().correlation_id = correlation_id

        @self.app.after_request
        def log_request(response):
            now = time.time()
            duration = round(now - g.start, 2)
            log_entry = {
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'args': dict(request.args),
                'duration': f'{duration}s',
                'date': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now)),
                'requestId': g.correlation_id,
                'appName': Version.get_app_name(),
            }
            if Configs.get_env_variable(Config.LOG_RESPONSE_BODY) == 'True':
                log_entry['response'] = response.get_json()

            if Configs.get_env_variable(Config.LOG_REQUEST_BODY) == 'True':
                try:
                    log_entry['request'] = request.get_json()
                except Exception:
                    pass
            if request.path in ['/metrics', '/health']:
                self.logger.debug(log_entry)
            else:
                self.logger.info(log_entry)
            return response
