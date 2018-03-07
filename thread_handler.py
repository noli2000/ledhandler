# -*-: coding utf-8 -*-
""" Thread handler. """

import threading
import time

from singleton import Singleton
from usb_utils import USB


class ThreadHandler(Singleton):
    """ Thread handler. """

    def __init__(self):
        """ Initialisation. """
        self.thread_pool = []
        self.run_events = []

    def run(self, target, args=()):
        """ Run a function in a separate thread.

        :param target: the function to run.
        :param args: the parameters to pass to the function.
        """
        run_event = threading.Event()
        run_event.set()
        thread = threading.Thread(target=target, args=args + (run_event, ))
        self.thread_pool.append(thread)
        self.run_events.append(run_event)
        thread.start()

    def start_run_loop(self, logger=None):
        """ Start the thread handler, ensuring that everything stops property
            when sending a keyboard interrup.
        """
        try:
            if logger is not None:
                logger.debug("Starting run loop thread")

                while 1:
                    time.sleep(.1)
        except KeyboardInterrupt:
            if logger is not None:
                logger.debug("Exiting run loop thread on KeyboardInterrupt")
            self.stop()

    def stop(self):
        """ Stop all functions running in the thread handler."""
        for run_event in self.run_events:
            run_event.clear()

        for thread in self.thread_pool:
            thread.join()
