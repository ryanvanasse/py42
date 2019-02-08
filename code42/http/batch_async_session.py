import Queue
from session import Session
from code42.util.threadutils import LogThread
from threading import Lock
import time


class BatchAsyncSession(Session):
    def __init__(self, host_address, auth_handler=None, proxies=None, concurrent_threads=4, max_requests_per_second=36):

        super(BatchAsyncSession, self).__init__(host_address, auth_handler=auth_handler, proxies=proxies)
        # Lifo makes it so that callbacks happen sooner after being called instead of being placed all the way
        # to the back of the queue and having to wait again.
        self._request_queue = Queue.LifoQueue()
        self._concurrent_threads = concurrent_threads
        self._max_requests_per_second = max_requests_per_second
        self._exception_handler = None
        self.__started = False
        self.__start_lock = Lock()

    def register_exception_handler(self, func_handler):
        self._exception_handler = func_handler

    def request(self, method, url, *args, **kwargs):
        if not self.__started:
            self.__start_lock.acquire()
            if not self.__started:
                self.__start()
                self.__started = True
            self.__start_lock.release()
        self._request_queue.put({"method": method, "path": url, "args": args, "kwargs": kwargs})

    def _process_queue(self):
        new_request = self._request_queue.get
        send = super(BatchAsyncSession, self).request
        # To avoid having calls dropped because of rate limits, we can tweak the number of concurrent threads and
        # the max requests allowed per second by the rate limit and intentionally throttle dispatching requests if
        # they are completing too quickly.
        min_request_time = float(self._concurrent_threads) / float(self._max_requests_per_second)
        while True:
            try:
                request = new_request()
                start = time.time()
                send(request["method"], request["path"], *request["args"], **request["kwargs"])
                end = time.time()
                elapsed = end - start
                if elapsed < min_request_time:
                    diff = min_request_time - elapsed
                    time.sleep(diff)
            except Exception as e:
                if self._exception_handler is not None:
                    self._exception_handler(e)
                else:
                    print e
            finally:
                self._request_queue.task_done()

    def __start(self):
        for i in range(self._concurrent_threads):
            t = LogThread(target=self._process_queue)
            t.daemon = True
            t.start()

    def wait(self):
        self._request_queue.join()
        self.__started = False
