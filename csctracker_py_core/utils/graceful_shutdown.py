import logging
import os
import signal
import threading
import time
from typing import Callable, List, Optional

from csctracker_queue_scheduler.services.scheduler_service import SchedulerService


class GracefulShutdown:
    _instance: Optional["GracefulShutdown"] = None
    _lock = threading.Lock()

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.is_shutting_down = False
        self.active_requests = 0
        self._condition = threading.Condition(self._lock)
        self._shutdown_hooks: List[Callable] = []
        self.logger = logging.getLogger()

    @classmethod
    def get_instance(cls, timeout: Optional[int] = None) -> "GracefulShutdown":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(timeout=timeout if timeout is not None else 30)
            elif timeout is not None:
                cls._instance.timeout = timeout
            assert cls._instance is not None
            return cls._instance

    @classmethod
    def reset_instance(cls):
        with cls._lock:
            cls._instance = None

    def register_signals(self):
        try:
            signal.signal(signal.SIGTERM, self._handle_signal)
        except (ValueError, AttributeError) as e:
            self.logger.warning(f"Could not register SIGTERM handler: {e}")

        try:
            signal.signal(signal.SIGINT, self._handle_signal)
        except (ValueError, AttributeError) as e:
            self.logger.warning(f"Could not register SIGINT handler: {e}")

    def start_request(self):
        with self._condition:
            self.active_requests += 1

    def end_request(self):
        with self._condition:
            self.active_requests = max(0, self.active_requests - 1)
            self._condition.notify_all()

    def register_shutdown_hook(self, callback: Callable):
        with self._lock:
            self._shutdown_hooks.append(callback)

    def _handle_signal(self, signum, frame):
        signal_name = "SIGTERM" if signum == signal.SIGTERM else ("SIGINT" if signum == signal.SIGINT else str(signum))
        self.logger.info(f"Signal {signal_name} received. Starting graceful shutdown...")
        with self._lock:
            if self.is_shutting_down:
                return
            self.is_shutting_down = True

        threading.Thread(target=self._wait_and_exit, args=(True,), daemon=False).start()

    def wait_for_drain(self, timeout: Optional[int] = None, exit_process: bool = False):
        self._wait_and_exit(exit_process=exit_process, override_timeout=timeout)

    def _wait_and_exit(self, exit_process: bool = True, override_timeout: Optional[int] = None):
        timeout = override_timeout if override_timeout is not None else self.timeout
        start_time = time.time()

        # 1. Wait for active HTTP requests to reach 0
        with self._condition:
            while self.active_requests > 0:
                elapsed = time.time() - start_time
                remaining = timeout - elapsed
                if remaining <= 0:
                    self.logger.warning(
                        f"Timeout reached ({timeout}s) with {self.active_requests} active HTTP requests."
                    )
                    break
                self._condition.wait(timeout=min(remaining, 0.5))

        # 2. Wait for SchedulerService queue to be empty and pending tasks to finish
        self._wait_for_scheduler_queue(start_time, timeout)

        # 3. Execute custom shutdown hooks
        with self._lock:
            hooks = list(self._shutdown_hooks)

        for hook in hooks:
            try:
                hook()
            except Exception as e:
                self.logger.error(f"Error executing shutdown hook: {e}")

        self.logger.info("Graceful shutdown completed successfully. Exiting process.")
        if exit_process:
            os._exit(0)

    def _wait_for_scheduler_queue(self, start_time: float, timeout: int):
        while True:
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                self.logger.warning(
                    f"Timeout reached ({timeout}s) waiting for SchedulerService queue."
                )
                break

            queue_empty = True
            try:
                queue_service = SchedulerService.get_queue_service()
                if queue_service is not None:
                    normal_unfinished = getattr(
                        getattr(queue_service, "normal_queue", None), "unfinished_tasks", 0
                    )
                    priority_unfinished = getattr(
                        getattr(queue_service, "priority_queue", None), "unfinished_tasks", 0
                    )
                    normal_empty = (
                        queue_service.normal_queue.empty()
                        if hasattr(queue_service, "normal_queue")
                        else True
                    )
                    priority_empty = (
                        queue_service.priority_queue.empty()
                        if hasattr(queue_service, "priority_queue")
                        else True
                    )

                    if not (normal_empty and priority_empty and normal_unfinished == 0 and priority_unfinished == 0):
                        queue_empty = False
            except Exception as e:
                self.logger.debug(f"Error checking SchedulerService: {e}")

            if queue_empty:
                self.logger.info("SchedulerService queue drained successfully.")
                break
            time.sleep(0.5)
