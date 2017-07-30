#! /usr/bin/env python
# -*- coding: utf-8 -*-
import enum
import selectors
import socket
import time
import abc
import six
from sockspy.core import transport
from sockspy.core import exceptions
import logging
from sockspy.socket import raw


@enum.unique
class ProtocolStatus(enum.Enum):
    Init = 0
    Connecting = 900
    ProtocolValidated = 999


@six.add_metaclass(abc.ABCMeta)
class EndpointEngine():

    @abc.abstractmethod
    def process_event(self, endpoint):
        pass

    @abc.abstractmethod
    def destroy_endpoint(self, endpoint):
        pass

    @abc.abstractmethod
    def accept(self, sock):
        pass

    @abc.abstractmethod
    def destroy(self):
        pass

    @abc.abstractmethod
    def process_loop(self):
        pass


class EventHandlerEngine(EndpointEngine):

    def process_event(self, endpoint):
        try:
            self.handle_event(endpoint)
        except exceptions.ReadOrWriteNoDataError:
            self.handle_stop(endpoint)
        except Exception as ex:
            self.handle_error(endpoint, ex)

    @abc.abstractmethod
    def handle_event(self, endpoint):
        pass

    @abc.abstractmethod
    def handle_stop(self, endpoint):
        pass

    @abc.abstractmethod
    def handle_error(self, endpoint, ex):
        pass


class StatusHandlerEngine(EventHandlerEngine):

    STATUS_KEY = "PROTOCOL_STATUS"

    def handle_event(self, endpoint):
        self.handle_before(endpoint)
        if selectors.EVENT_READ & endpoint.event:
            endpoint.read()
        elif self.get_status(endpoint) == ProtocolStatus.Connecting:
            pass
        else:
            endpoint.write()
        self.handle_after(endpoint)

    @abc.abstractmethod
    def handle_before(self, endpoint):
        pass

    def handle_after(self, endpoint):
        status = self.get_status(endpoint)
        self.get_handler_by_status(status, endpoint)(endpoint)

    @abc.abstractmethod
    def get_handler_by_status(self, status, endpoint):
        pass

    def get_status(self, endpoint):
        return endpoint.status.get(self.STATUS_KEY)

    def set_status(self, endpoint, status):
        endpoint.status[self.STATUS_KEY] = status

    def register_status(self, endpoint, status):
        endpoint.register_status(self.STATUS_KEY, status)


class SocksEngine(StatusHandlerEngine):

    def __init__(self, config, pool):
        self.logger = logging.getLogger(__name__)
        self.pool = pool
        self.config = config
        self.active_queue = []
        self.active_queue_start_pos = 0
        self.last_check_timeout_time = time.time()

    def get_handler_by_status(self, status, endpoint):
        if status == ProtocolStatus.ProtocolValidated:
            return {
                selectors.EVENT_READ: self.handle_read,
                selectors.EVENT_WRITE: self.handle_write
            }.get(endpoint.event)
        if status == ProtocolStatus.Connecting:
            return self.handle_remote_connecting
        return self.get_handler_in_protocol_validation(status, endpoint)

    @abc.abstractmethod
    def get_handler_in_protocol_validation(self, status, endpoint):
        pass

    def handle_read(self, endpoint):
        # self.logger.debug("[read] fd: %d, stream: %s", endpoint.fileno(), endpoint.stream)
        self.pool.modify(endpoint.peer, selectors.EVENT_READ | selectors.EVENT_WRITE)

    def handle_write(self, endpoint):
        if len(endpoint.peer.stream) == 0:
            self.pool.modify(endpoint, selectors.EVENT_READ)

    def handle_stop(self, endpoint):
        self.logger.debug("enter handle_stop!")
        self.close_session(endpoint)

    def handle_error(self, endpoint, error):
        self.logger.debug("enter handle_error!")
        self.close_session(endpoint)
        self.logger.error(repr(error))

    def create_remote_endpoint(self, endpoint):
        (sock, connecting) = raw.client_socket(endpoint.address)
        peer = transport.Endpoint(sock, endpoint.msg_size, False)
        endpoint.peer = peer
        peer.peer = endpoint
        if connecting:
            self.register_status(peer, ProtocolStatus.Connecting)
            self.pool.register(peer, selectors.EVENT_WRITE)
        else:
            self.register_status(peer, ProtocolStatus.ProtocolValidated)

    def accept(self, sock):
        endpoint = transport.Endpoint(sock, self.config.msg_size)
        endpoint.peer = endpoint
        self.register_status(endpoint, ProtocolStatus.Init)
        self.pool.register(endpoint, selectors.EVENT_READ)
        self.update_activity(endpoint)

    def update_activity(self, endpoint):
        endpoint.last_active_time = time.time()
        if endpoint.active_queue_index > -1:
            self.active_queue[endpoint.active_queue_index] = None
        endpoint.active_queue_index = len(self.active_queue)
        self.active_queue.append(endpoint)

    def check_timeout(self):
        pos = self.active_queue_start_pos
        length = len(self.active_queue)
        while pos<length:
            endpoint = self.active_queue[pos]
            if not endpoint:
                pos = pos+1
                continue
            now = time.time()
            if now-endpoint.last_active_time > self.config.endpoint_timeout:
                self.logger.debug("destroy endpoint: " + str(endpoint.fileno()))
                self.close_session(endpoint)
                pos = pos+1
            else:
                if pos > self.config.max_queue_size or pos > (length>>1):
                    self.active_queue = self.active_queue[pos:]
                    for ele in self.pool.endpoint_set:
                        ele.active_queue_index = ele.active_queue_index - pos
                    self.active_queue_start_pos = 0
                else:
                    self.active_queue_start_pos = pos
                return
            if pos == length:
                self.active_queue = []
                self.active_queue_start_pos = 0

    def close_session(self, endpoint):
        if endpoint.peer and endpoint.peer != endpoint:
            self.destroy_endpoint(endpoint.peer)
        self.destroy_endpoint(endpoint)

    def destroy_endpoint(self, endpoint):
        self.pool.unregister(endpoint)
        endpoint.destroy()
        if endpoint.active_queue_index > -1:
            self.active_queue[endpoint.active_queue_index] = None

    def handle_remote_connecting(self, endpoint):
        endpoint.peer.try_turn = endpoint.peer.try_turn + 1
        self.logger.debug("enter handle_remote_connecting!")
        errno = endpoint.sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if errno != 0:
            if endpoint.peer.try_turn < self.config.max_try_turn:
                self.create_remote_endpoint(endpoint.peer)
                endpoint.destroy()
            else:
                raise Exception("socket connecting error! errno is " + str(errno))
        self.set_status(endpoint, ProtocolStatus.ProtocolValidated)
        endpoint.connecting = False
        self.pool.set_events(endpoint)
        self.pool.set_events(endpoint.peer)
        self.update_activity(endpoint)

    def process_loop(self):
        now = time.time()
        if now-self.last_check_timeout_time > self.config.timeout:
            self.check_timeout()
            self.last_check_timeout_time = now

    def destroy(self):
        iter_set = self.pool.endpoint_set.copy()
        for endpoint in iter_set:
            self.destroy_endpoint(endpoint)
        self.pool.remove_listener()
