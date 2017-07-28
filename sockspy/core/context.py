#! /usr/bin/env python
# -*- coding: utf-8 -*-
import signal
import sys

from sockspy.core import pool
from sockspy.socket import raw
import logging


class AppContext(object):
    """
    IOC/DI implementation. Use this class as the application context to configure components.
    """

    def __init__(self, engine_constructor, config):
        self.pool = pool.EndpointPool()
        self.engine = engine_constructor(config, self.pool)
        self.config = config
        self.logger = logging.getLogger(__name__)

    def run(self):

        def handle_signal(sig, _):
            self.logger.debug("destroy engine with signal: " + str(sig))
            self.engine.destroy()
            sys.exit(0)
            # Refer to PEP 475, user case 2, should raise an exception to stop the process
            # raise KeyboardInterrupt("interrupt by signal!")

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        try:
            self.pool.set_listener(raw.server_socket(self.config.address, self.config.backlog))
            self.pool.poll(self.engine, self.config.timeout)
        except Exception as ex:
            self.logger.error("<<< context error!\n" + repr(ex))
            sys.exit(1)
