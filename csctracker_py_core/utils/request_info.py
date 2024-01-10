import threading
import uuid

from flask import g, request


class RequestInfo:

    @staticmethod
    def get_request_id(create_new=True):
        try:
            request_id_ = g.correlation_id
        except Exception:
            try:
                thread = threading.current_thread()
                request_id_ = thread.__getattribute__('correlation_id')
            except Exception:
                if create_new:
                    request_id_ = str(uuid.uuid4())
                else:
                    request_id_ = None

        return request_id_

    @staticmethod
    def get_correlation_id(self):
        return request.headers.get('x-correlation-id', str(uuid.uuid4()))
