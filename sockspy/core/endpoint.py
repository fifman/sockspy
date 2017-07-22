#! /usr/bin/env python
# -*- coding: utf-8 -*-

from selectors import EVENT_WRITE, EVENT_READ
from sockspy.core import context


class Endpoint:
    def __init__(self, sock, local=True, address=None):
        self.sock = sock
        self.peer = None
        self.events = None
        self.local = local
        self.stream = b''
        self.address = address
        self.try_turn = 0

    def destroy(self):
        context.POOL.unregister(self)
        self.sock.close()

    def fileno(self):
        return self.sock.fileno()

    def _read_data(self):
        data = self.sock.recv(context.POOL.msg_size)
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
        self.peer.stream = self._write_data(self.peer.stream)

    def switch_events(self):
        context.POOL.modify(self, EVENT_WRITE if EVENT_READ & self.events else EVENT_READ)


class ReadOrWriteNoDataError(Exception):
    pass
