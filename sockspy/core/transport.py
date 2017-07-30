#! /usr/bin/env python
# -*- coding: utf-8 -*-

from sockspy.core import exceptions


class Endpoint(object):
    """
    This class models the endpoints of tunnels. An endpoint is a wrapper of a socket.
    A tunnel contains two endpoints, a local endpoint and a remote endpoint.
    The local endpoint connects to the client which sends a request.
    The remote endpoint connects to the target address specified by the request.
    """

    def __init__(self, sock, msg_size, local=True):
        """
        Constructor
        :param sock (`socket.socket`): the socket to be wrapped
        :param msg_size (`int`): the maximal size of the data received by sockets.
        :param local (`boolean`): whether the endpoint is local or not
        """
        self.sock = sock
        self.peer = None # the other side of the tunnel
        self.event = None # record the current event (`EVENT_READ` or `EVENT_WRITE`) when the endpoint is polled out.
        self.local = local
        self.stream = b'' # store the bytes read from the sock
        self.msg_size = msg_size
        self.address = None
        self.try_turn = 0
        self.last_active_time = 0
        self.active_queue_index = -1
        self.status = {}

    def destroy(self):
        self.sock.close()

    def fileno(self):
        return self.sock.fileno()

    def _read_data(self):
        data = self.sock.recv(self.msg_size)
        if not data:
            raise exceptions.ReadOrWriteNoDataError()
        return data

    def _write_data(self, stream):
        len = self.sock.send(stream)
        if len == 0:
            raise exceptions.ReadOrWriteNoDataError()
        return stream[len:]

    def read(self):
        self.stream = self.stream + self._read_data()

    def write(self):
        self.peer.stream = self._write_data(self.peer.stream)

    def register_status(self, key, value):
        if key in self.status:
            raise exceptions.StatusRegisterError("Other protocols/engines have already registered a status with this key {}. Choose another key instead!".format(str(key)))
        self.status[key] = value

    def change_status(self, key, value):
        if key not in self.status:
            raise exceptions.StatusRegisterError("You have not registered a status with this key {} yet, need registration first!".format(str(key)))
        self.status[key] = value

    def get_status(self, key):
        return self.status.get(key, None)
