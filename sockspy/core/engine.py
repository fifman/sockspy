#! /usr/bin/env python
# -*- coding: utf-8 -*-
from enum import unique, Enum
from selectors import EVENT_READ, EVENT_WRITE
from sockspy.core import context
from sockspy.core.endpoint import ReadOrWriteNoDataError
import logging


@unique
class ProtocolStatus(Enum):
    Init = 0
    ProtocolValidated = 999


class EndpointEngine():
    def process(self, endpoint):
        pass


class EventHandlerEngine(EndpointEngine):
    def get_handler(self, endpoint):
        pass

    def process(self, endpoint):
        try:
            self.get_handler(endpoint)(endpoint)
        except ReadOrWriteNoDataError:
            self.handle_stop(endpoint)
        except Exception as ex:
            self.handle_error(endpoint, ex)

    def handle_stop(self, endpoint):
        pass

    def handle_error(self, endpoint, ex):
        pass


class StatusHandlerEngine(EventHandlerEngine):
    def __init__(self):
        self.status_store = {}

    def get_handler(self, endpoint):
        status = self.get_status(endpoint)
        return self.get_handler_by_status(status, endpoint)

    def get_handler_by_status(self, status, endpoint):
        pass

    def get_status(self, endpoint):
        return self.status_store.get(endpoint)

    def set_status(self, endpoint, status):
        self.status_store[endpoint] = status


class SocksEngine(StatusHandlerEngine):
    def __init__(self):
        StatusHandlerEngine.__init__(self)
        self.logger = logging.getLogger(__name__)

    def get_handler_by_status(self, status, endpoint):
        if status == ProtocolStatus.ProtocolValidated:
            return {
                EVENT_READ: self.handle_read,
                EVENT_WRITE: self.handle_write
            }.get(endpoint.events)
        return self.get_handler_in_protocol_validation(status, endpoint)

    def get_handler_in_protocol_validation(self, status, endpoint):
        pass

    def handle_read(self, endpoint):
        endpoint.read()
        self.logger.debug("[read] fd: %d, stream: %s", endpoint.fileno(), endpoint.stream)
        context.POOL.modify(endpoint.peer, EVENT_READ | EVENT_WRITE)

    def handle_write(self, endpoint):
        self.logger.debug("[write] fd: %d, stream: %s", endpoint.fileno(), endpoint.peer.stream)
        endpoint.write()
        if len(endpoint.peer.stream) == 0:
            context.POOL.modify(endpoint, EVENT_READ)

    def handle_stop(self, endpoint):
        if endpoint.local:
            endpoint.peer.destroy()
            endpoint.destroy()
        else:
            endpoint.peer.create_remote_endpoint()
            endpoint.destroy()

    def handle_error(self, endpoint, error):
        self.handle_stop(endpoint)

    def ceate_remote_endpoint(self, endpoint):
        pass
