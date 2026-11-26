import logging
import math

import requests
from requests.adapters import HTTPAdapter

from csctracker_py_core.models.emuns.config import Config
from csctracker_py_core.utils.configs import Configs


class RemoteRepository:
    DEFAULT_TIMEOUT = 600
    DEFAULT_POOL_CONNECTIONS = 10
    DEFAULT_POOL_MAXSIZE = 32
    _HOP_BY_HOP_OR_FRAMING_HEADERS = frozenset(
        {"content-length", "host", "transfer-encoding", "connection"}
    )

    def __init__(self):
        self.logger = logging.getLogger()
        self.url_repository = Configs.get_env_variable(
            Config.URL_REPOSITORY, default="http://bff:8080/repository/"
        )
        if self.url_repository[-1] != "/":
            self.url_repository += "/"
        self.timeout = self._get_positive_timeout_env(
            Config.REMOTE_REPOSITORY_TIMEOUT, default=self.DEFAULT_TIMEOUT
        )
        pool_connections = self._get_positive_int_env(
            Config.REMOTE_REPOSITORY_POOL_CONNECTIONS,
            default=self.DEFAULT_POOL_CONNECTIONS,
        )
        pool_maxsize = self._get_positive_int_env(
            Config.REMOTE_REPOSITORY_POOL_MAXSIZE,
            default=self.DEFAULT_POOL_MAXSIZE,
        )
        self.session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    @staticmethod
    def _get_positive_timeout_env(key: Config, default: int = DEFAULT_TIMEOUT):
        value = Configs.get_env_variable(key, default=default)
        if value is None or isinstance(value, bool):
            return default
        if isinstance(value, int):
            return value if value > 0 else default
        if isinstance(value, float):
            return value if math.isfinite(value) and value > 0 else default
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return default
            try:
                parsed_int = int(stripped)
                return parsed_int if parsed_int > 0 else default
            except ValueError:
                try:
                    parsed_float = float(stripped)
                    return (
                        parsed_float
                        if math.isfinite(parsed_float) and parsed_float > 0
                        else default
                    )
                except ValueError:
                    return default
        return default

    @staticmethod
    def _get_positive_int_env(key: Config, default: int) -> int:
        value = Configs.get_env_variable(key, default=default)
        if value is None or isinstance(value, bool):
            return default
        if isinstance(value, int):
            return value if value > 0 else default
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return default
            try:
                parsed = int(stripped)
                return parsed if parsed > 0 else default
            except ValueError:
                return default
        return default

    @classmethod
    def _sanitize_headers(cls, headers):
        if headers is None:
            return None
        try:
            items = headers.items()
        except Exception:
            return None
        return {
            k: v
            for k, v in items
            if k and str(k).lower() not in cls._HOP_BY_HOP_OR_FRAMING_HEADERS
        }

    def close(self):
        if self.session is not None:
            try:
                self.session.close()
            except Exception:
                pass

    def insert(self, table, data, headers=None):
        headers = self._sanitize_headers(headers)
        try:
            response = self.session.post(
                self.url_repository + table,
                headers=headers,
                json=data,
                timeout=self.timeout,
            )
            if response.status_code < 200 or response.status_code > 299:
                raise Exception(f"Error inserting data: {response.text}")
            return response.json()
        except Exception as e:
            raise e

    def update(self, table, keys=None, data=None, headers=None):
        params = self.get_params(data, keys)
        headers = self._sanitize_headers(headers)
        try:
            response = self.session.post(
                self.url_repository + table,
                headers=headers,
                json=data,
                params=params,
                timeout=self.timeout,
            )
            if response.status_code < 200 or response.status_code > 299:
                raise Exception(f"Error updating data: {response.text}")
            return response.json()
        except Exception as e:
            raise e

    def delete_all(self, table, headers=None):
        self.delete(table, [], {}, headers=headers)

    def delete(self, table, keys=None, data=None, headers=None):
        params = self.get_params(data, keys)
        headers = self._sanitize_headers(headers)
        try:
            response = self.session.post(
                self.url_repository + "delete/" + table,
                headers=headers,
                json=data,
                params=params,
                timeout=self.timeout,
            )
            if response.status_code < 200 or response.status_code > 299:
                raise Exception(f"Error deleting data: {response.text}")
            return response.json()
        except Exception as e:
            raise e

    def add_user_id(self, data, headers=None):
        user = self.get_user(headers)
        data["user_id"] = user["id"]
        return data

    def get_user(self, headers=None):
        user_name = None
        if headers:
            user_name = next(
                (
                    v
                    for k, v in headers.items()
                    if isinstance(k, str) and k.lower() == "username"
                ),
                None,
            )
        try:
            user = self.get_object("users", data={"email": user_name}, headers=headers)
            return user
        except Exception as e:
            raise e

    def get_object(self, table, keys=None, data=None, headers=None):
        params = self.get_params(data, keys)
        headers = self._sanitize_headers(headers)
        try:
            response = self.session.get(
                self.url_repository + "single/" + table,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )
            if response.status_code < 200 or response.status_code > 299:
                raise Exception(f"Error getting data: {response.text}")
            return response.json()
        except Exception as e:
            raise e

    def get_all_objects(self, table, headers=None):
        return self.get_objects(table, [], {}, headers)

    def get_objects(self, table, keys=None, data=None, headers=None):
        params = self.get_params(data, keys)
        headers = self._sanitize_headers(headers)
        try:
            response = self.session.get(
                self.url_repository + table,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )
            if response.status_code < 200 or response.status_code > 299:
                raise Exception(f"Error getting data: {response.text}")
            return response.json()
        except Exception as e:
            raise e

    def execute_select(self, select, headers=None):
        command = {"command": select}
        headers = self._sanitize_headers(headers)
        try:
            response = self.session.post(
                self.url_repository + "command/select",
                headers=headers,
                json=command,
                timeout=self.timeout,
            )
            if response.status_code < 200 or response.status_code > 299:
                raise Exception(f"Error getting data: {response.text}")
            return response.json()
        except Exception as e:
            raise e

    def exist_by_key(self, table, key=[], data={}, headers=None):
        try:
            objects = self.get_objects(table, key, data, headers)
            return objects.__len__() > 0
        except Exception as e:
            self.logger.exception(e)
            return False

    def get_params(self, data, keys):
        if data is None:
            data = {}
        params = {}
        if keys is None:
            keys = []
        if keys.__len__() > 0:
            for key in keys:
                params[key] = data[key]
            return params
        for key in data.keys():
            params[key] = data[key]
        return params
