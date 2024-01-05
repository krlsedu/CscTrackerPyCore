import logging
import time

from flask import Flask, request, g

from csctracker_py_core.models.emuns.config import Config
from csctracker_py_core.utils.configs import Configs


class Interceptor:
    def __init__(self, app: Flask):
        self.logger = logging.getLogger()
        self.app = app
        self.__init()

    def __init(self):
        @self.app.before_request
        def start_timer():
            g.start = time.time()

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
            }
            if Configs.get_env_variable(Config.LOG_RESPONSE_BODY) == 'True':
                log_entry['response'] = response.get_json()

            if Configs.get_env_variable(Config.LOG_REQUEST_BODY) == 'True':
                try:
                    log_entry['request'] = request.get_json()
                except Exception:
                    pass

            self.logger.info(log_entry)
            return response
