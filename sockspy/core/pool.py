#! /usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import selectors
except ImportError:
    import sockspy.core.selectors2 as selectors
import logging
import click


class EndpointPool(object):
    def __init__(self, selector_type=selectors.DefaultSelector):
        self.listener = None
        self.poller = selector_type()
        self.logger = logging.getLogger(__name__)
        self.endpoint_set = set()

    def set_listener(self, listener):
        self.listener = listener
        self.poller.register(listener, selectors.EVENT_READ)

    def register(self, endpoint, events):
        self.poller.register(endpoint, events)
        self.endpoint_set.add(endpoint)

    def modify(self, endpoint, events):
        self.poller.modify(endpoint, events)

    def unregister(self, endpoint):
        self.poller.unregister(endpoint)
        self.endpoint_set.remove(endpoint)

    def poll(self, engine, timeout):
        click.echo("sockspy started!")
        self.logger.debug("debug started!")
        while True:
            for (key, event) in self.poller.select(timeout):
                endpoint = key.fileobj
                if endpoint == self.listener:
                    sock, address = self.listener.accept()
                    engine.accept(sock)
                else:
                    if endpoint.closed:  # `closed` flag is used to decide whether needs handling.
                        continue
                    endpoint.event = event
                    self.logger.debug("[poll]   fd: %s, event: %s", endpoint.fileno(),
                                      "read" if event & selectors.EVENT_READ else "write")
                    engine.process_event(endpoint)
            engine.process_loop()

    def set_events(self, endpoint):
        self.modify(endpoint, selectors.EVENT_WRITE | selectors.EVENT_READ if len(
            endpoint.peer.stream) > 0 else selectors.EVENT_READ)

    def remove_listener(self):
        self.poller.unregister(self.listener)
        self.listener.close()
