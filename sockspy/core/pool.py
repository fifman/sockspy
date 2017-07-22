#! /usr/bin/env python
# -*- coding: utf-8 -*-

from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE

from sockspy.core import context
from sockspy.core.endpoint import Endpoint
import logging


class EndpointPool:

    def __init__(self, selector_type=DefaultSelector):
        self.poller = selector_type()
        self.msg_size = 4096
        self.logger = logging.getLogger(__name__)

    def set_listener(self, listener):
        self.listener = listener
        self.poller.register(listener, EVENT_READ)

    def register(self, endpoint, events):
        self.poller.register(endpoint, events)

    def modify(self, endpoint, events):
        self.poller.modify(endpoint, events)

    def unregister(self, endpoint):
        self.poller.unregister(endpoint)

    def poll(self):
        while True:
            for (key, events) in self.poller.select():
                endpoint = key.fileobj
                if endpoint == self.listener:
                    sock, address = self.listener.accept()
                    self.create_local_endpoint(sock)
                    continue
                endpoint.events = events
                self.logger.debug("[poll]   fd: %s, event: %s", endpoint.fileno(), "event_read" if events & EVENT_READ else "event_write")
                context.process_endpoint(endpoint)

    def create_local_endpoint(self, sock):
        endpoint = Endpoint(sock)
        endpoint.peer = endpoint
        self.register(endpoint, EVENT_READ)

    def set_events(self, endpoint):
        self.modify(endpoint, EVENT_WRITE | EVENT_READ if len(endpoint.peer.stream)>0 else EVENT_READ)
