from __future__ import absolute_import

import logging
import threading


logger = logging.getLogger(__name__)


class FutureSet(object):
    """
    Coordinates a set of ``Future`` objects (either from
    ``concurrent.futures``, or otherwise API compatible), and allows for
    attaching a callback when all futures have completed execution.
    """

    def __init__(self, futures):
        self.__pending = set(futures)
        self.__completed = set()
        self.__callbacks = []
        self.__lock = threading.Lock()

        for future in futures:
            future.add_done_callback(self.__mark_completed)

    def __iter__(self):
        with self.__lock:
            futures = self.__pending | self.__completed
        return iter(futures)

    def __execute_callback(self, callback):
        try:
            callback(self)
        except Exception as error:
            logger.warning(
                'Error when calling callback %r: %s',
                callback, error, exc_info=True)

    def __mark_completed(self, future):
        with self.__lock:
            self.__pending.remove(future)
            self.__completed.add(future)
            remaining = len(self.__pending)

        if remaining == 0:
            for callback in self.__callbacks:
                self.__execute_callback(callback)

    def add_done_callback(self, callback):
        with self.__lock:
            remaining = len(self.__pending)
            if remaining > 0:
                self.__callbacks.append(callback)

        if remaining == 0:
            self.__execute_callback(callback)
