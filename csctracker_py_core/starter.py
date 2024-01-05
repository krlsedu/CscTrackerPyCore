import logging
import os

from flask import Flask
from flask_cors import CORS
from prometheus_flask_exporter import PrometheusMetrics

from csctracker_py_core.models.emuns.config import Config
from csctracker_py_core.repository.http_repository import HttpRepository
from csctracker_py_core.repository.remote_repository import RemoteRepository
from csctracker_py_core.utils.configs import Configs


class Starter:
    def __init__(self):
        self.logger = logging.getLogger()
        self.app = Flask(__name__)
        self.cors = CORS(self.app)
        self.app.config['CORS_HEADERS'] = 'Content-Type'
        self.config = Configs(os.getenv('PROFILE', 'dev'))
        self.remote_repository = RemoteRepository()
        self.http_repository = HttpRepository(remote_repository=self.remote_repository)
        self.metrics = PrometheusMetrics(
            self.app,
            group_by='endpoint',
            default_labels={
                'application': Configs.get_env_variable(Config.APPLICATION_NAME)
            }
        )

    def get_remote_repository(self):
        return self.remote_repository

    def get_http_repository(self):
        return self.http_repository

    def get_app(self):
        return self.app

    def start(self):
        self.app.run(host='0.0.0.0',
                     port=Configs.get_env_variable(Config.PORT, default=5000))
