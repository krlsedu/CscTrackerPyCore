import time
import unittest

from flask import Flask

from csctracker_queue_scheduler.services.scheduler_service import SchedulerService
from csctracker_py_core.repository.http_repository import HttpRepository
from csctracker_py_core.repository.remote_repository import RemoteRepository
from csctracker_py_core.starter import Starter
from csctracker_py_core.utils.graceful_shutdown import GracefulShutdown
from csctracker_py_core.utils.interceptor import Interceptor


class TestGracefulShutdown(unittest.TestCase):
    def setUp(self):
        GracefulShutdown.reset_instance()

    def tearDown(self):
        GracefulShutdown.reset_instance()

    def test_active_requests_tracking(self):
        shutdown = GracefulShutdown.get_instance(timeout=10)
        self.assertEqual(shutdown.active_requests, 0)

        shutdown.start_request()
        shutdown.start_request()
        self.assertEqual(shutdown.active_requests, 2)

        shutdown.end_request()
        self.assertEqual(shutdown.active_requests, 1)

        shutdown.end_request()
        self.assertEqual(shutdown.active_requests, 0)

        # Ensure counter does not go below 0
        shutdown.end_request()
        self.assertEqual(shutdown.active_requests, 0)

    def test_interceptor_request_lifecycle(self):
        shutdown = GracefulShutdown.get_instance(timeout=10)
        app = Flask(__name__)
        remote_repo = RemoteRepository()
        http_repo = HttpRepository(remote_repository=remote_repo)
        Interceptor(app, http_repo, save_request=False)

        @app.route("/ok")
        def ok():
            self.assertEqual(shutdown.active_requests, 1)
            return {"status": "ok"}

        @app.route("/error")
        def error():
            self.assertEqual(shutdown.active_requests, 1)
            raise RuntimeError("Test simulated error")

        client = app.test_client()

        # Test normal request
        resp = client.get("/ok")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(shutdown.active_requests, 0)

        # Test error request (teardown_request must still decrement)
        try:
            client.get("/error")
        except RuntimeError:
            pass
        self.assertEqual(shutdown.active_requests, 0)

    def test_shutdown_hooks_execution(self):
        shutdown = GracefulShutdown.get_instance(timeout=5)
        call_order = []

        def hook1():
            call_order.append(1)

        def faulty_hook():
            call_order.append(2)
            raise ValueError("Error in hook")

        def hook3():
            call_order.append(3)

        shutdown.register_shutdown_hook(hook1)
        shutdown.register_shutdown_hook(faulty_hook)
        shutdown.register_shutdown_hook(hook3)

        shutdown.wait_for_drain(timeout=2, exit_process=False)
        self.assertEqual(call_order, [1, 2, 3])

    def test_timeout_safeguard(self):
        shutdown = GracefulShutdown.get_instance(timeout=1)
        shutdown.start_request()  # Stalled request

        start = time.time()
        shutdown.wait_for_drain(timeout=1, exit_process=False)
        duration = time.time() - start

        self.assertGreaterEqual(duration, 0.9)
        self.assertLess(duration, 3.0)

    def test_scheduler_queue_draining(self):
        SchedulerService.init(threads=2)
        shutdown = GracefulShutdown.get_instance(timeout=15)

        processed = []

        def sample_job(val):
            time.sleep(0.1)
            processed.append(val)

        SchedulerService.put_in_queue(sample_job, args={"val": "job1"}, priority=False)
        SchedulerService.put_in_queue(sample_job, args={"val": "job2"}, priority=True)

        shutdown.wait_for_drain(timeout=15, exit_process=False)

        self.assertIn("job1", processed)
        self.assertIn("job2", processed)

    def test_starter_graceful_shutdown_integration(self):
        starter = Starter(save_request=False)
        shutdown = starter.get_graceful_shutdown()
        self.assertIsNotNone(shutdown)

        hook_called = []
        starter.register_shutdown_hook(lambda: hook_called.append(True))
        self.assertEqual(len(shutdown._shutdown_hooks), 1)


if __name__ == "__main__":
    unittest.main()
