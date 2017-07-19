#! /usr/bin/env python
# -*- coding: utf-8 -*-

import socket
from selectors import EVENT_WRITE
from sockspy.core.context import process_endpoint, POOL
from sockspy.socket.raw import client_socket


class Endpoint:
    def __init__(self, sock, local=True, address=None):
        self.sock = sock
        self.peer = None
        self.events = None
        self.local = local
        self.stream = b''
        self.address = address

    def create_remote_endpoint(self):
        sock = client_socket(self.address)
        endpoint = Endpoint(sock, False, self.address)
        self.peer = endpoint
        endpoint.peer = self
        POOL.register(endpoint, EVENT_WRITE)

    def destroy(self):
        POOL.unregister(self)
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()

    def fileno(self):
        return self.sock.fileno()

    def ready(self):
        process_endpoint(self)

    def _read_data(self):
        data = self.sock.recv(POOL.msg_size)
        if not data:
            raise ReadOrWriteNoDataError()
        return data

    def _write_data(self, stream):
        len = self.sock.send(stream)
        if len == 0:
            raise ReadOrWriteNoDataError()
        return stream[len:]

    def read(self):
        self.stream = self.stream + self._read_data()

    def write(self):
        self.stream = self._write_data(self.peer.stream)

    def switch_events(self):
        POOL.modify(self, ~ self.events)


class ReadOrWriteNoDataError(Exception):
    pass
