import threading
import uuid

from flask import g, request

from csctracker_py_core.utils.version import Version


class RequestInfo:

    @staticmethod
    def get_request_id(create_new=True):
        try:
            request_id_ = g.correlation_id
        except Exception:
            try:
                thread = threading.current_thread()
                request_id_ = thread.__getattribute__("correlation_id")
            except Exception:
                if create_new:
                    request_id_ = f"{Version.get_app_name()}-{str(uuid.uuid4())}"
                else:
                    request_id_ = None

        return request_id_

    @staticmethod
    def get_correlation_id():
        return request.headers.get(
            "x-correlation-id", f"{Version.get_app_name()}-{str(uuid.uuid4())}"
        )

    @staticmethod
    def get_header(header_name: str):
        _headers = request.headers
        _header = next((v for k, v in _headers.items() if k.lower() == header_name.lower()), None)
        return _header

    @staticmethod
    def get_json_body():
        return request.json

    @staticmethod
    def get_args():
        return request.args

    @staticmethod
    def get_headers():
        headers = request.headers
        headers_ = {}
        for key in headers.keys():
            headers_[key] = headers.get(key)
        if "x-correlation-id" not in headers_:
            headers_["x-correlation-id"] = RequestInfo.get_request_id(True)
        return headers