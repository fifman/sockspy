#! /usr/bin/env python
# -*- coding: utf-8 -*-

from enum import unique, Enum
from selectors import EVENT_READ, EVENT_WRITE
from sockspy.core.endpoint import ReadOrWriteNoDataError


@unique
class Socks5Status(Enum):
    Validated = 1
    ValidationResponded = 2
    Confirmed = 3


@unique
class ProtocolStatus(Enum):
    Init = 0
    ProtocolValidated = 999


class EndpointEngine():

    def process(self, endpoint):
        pass


class EventHandlerEngine(EndpointEngine):

    def get_handlers(self, endpoint):
        return []

    def process(self, endpoint):
        for (op_handler, stop_handler, error_handler) in self.get_handlers(endpoint):
            try:
                op_handler(endpoint)
            except ReadOrWriteNoDataError:
                stop_handler(endpoint)
            except Exception as ex:
                error_handler(endpoint, ex)


class StatusHandlerEngine(EventHandlerEngine):

    def __init__(self):
        self.status_store = {}

    def get_handlers(self, endpoint):
        status = self.get_status(endpoint)
        return self.get_handlers_by_status(status, endpoint)

    def get_handlers_by_status(self, status, endpoint):
        pass

    def get_status(self, endpoint):
        return self.status_store.get(endpoint)

    def set_status(self, endpoint, status):
        self.status_store[endpoint] = status


class SocksEngine(StatusHandlerEngine):

    def get_handlers_by_status(self, status, endpoint):
        if status == ProtocolStatus.ProtocolValidated:
            return {
                EVENT_READ : (self.handle_read, self.handle_stop, self.handle_error),
                EVENT_WRITE : (self.handle_write, self.handle_stop, self.handle_error)
            }.get(endpoint.events)
        return self.get_handlers_in_protocol_validation(status, endpoint)

    def get_handlers_in_protocol_validation(self, status, endpoint):
        pass

    def handle_read(self, endpoint):

        endpoint.read()

    def handle_write(self, endpoint):
        endpoint.write()

    def handle_stop(self, endpoint):
        if endpoint.local:
            endpoint.peer.destroy()
            endpoint.destroy()
        else:
            endpoint.peer.create_remote_endpoint()
            endpoint.destroy()

    def handle_error(self, endpoint, error):
        self.handle_stop(endpoint)



