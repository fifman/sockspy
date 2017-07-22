#! /usr/bin/env python
# -*- coding: utf-8 -*-
import socket
from enum import unique, Enum
from sockspy.core import context
from sockspy.core.endpoint import Endpoint
from sockspy.core.engine import SocksEngine, ProtocolStatus
from selectors import EVENT_WRITE, EVENT_READ
import logging

from sockspy.socket.raw import client_socket


@unique
class Socks5Status(Enum):
    ValidateMethod = 1
    MethodValidated = 3
    ValidateRequest = 4
    Failed = 5
    RequestValidated = 6
    Connecting = 7


class Socks5Engine(SocksEngine):
    def __init__(self):
        SocksEngine.__init__(self)
        self.logger = logging.getLogger(__name__)

    def get_handler_in_protocol_validation(self, status, endpoint):
        return {
            None: self.validate_method,
            Socks5Status.MethodValidated: self.respond_validation,
            Socks5Status.ValidateRequest: self.validate_request,
            Socks5Status.Failed: self.error_response,
            Socks5Status.Connecting: self.handle_connecting
        }.get(status)

    def validate_method(self, endpoint):
        self.logger.debug("enter validate_method!")
        endpoint.read()
        if bytearray(endpoint.stream)[0] != 5:
            self._error_validate_method(endpoint, "Only supports socks5 protocol!", b'\x05\xFF')
            return
        if len(endpoint.stream) < 3:
            return
        method_num = bytearray(endpoint.stream)[1]
        if method_num > 255 or method_num < 1:
            self._error_validate_method(endpoint, "Number of methods is not in [1,255]!", b'\x05\xFF')
            return
        if len(endpoint.stream) < 2 + method_num:
            return
        self._validate_method_type(endpoint)

    def _validate_method_type(self, endpoint):
        int_stream = bytearray(endpoint.stream)
        # noinspection PyTypeChecker
        for octet in int_stream[2: int_stream[1] + 2]:
            if octet == 0:
                endpoint.peer.stream = b'\x05\x00'
                self.set_status(endpoint, Socks5Status.MethodValidated)
                endpoint.switch_events()
                return
        self._error_validate_method(endpoint, "Only support 'No authentication required' method!", b'\x05\xFF')

    def _error_validate_method(self, endpoint, msg, stream):
        self.logger.error(msg)
        endpoint.peer.stream = stream
        self.set_status(endpoint, Socks5Status.Failed)
        endpoint.switch_events()

    def respond_validation(self, endpoint):
        self.logger.debug("enter respond_validation")
        endpoint.write()
        self.set_status(endpoint, Socks5Status.ValidateRequest)
        endpoint.switch_events()

    def validate_request(self, endpoint):
        self.logger.debug("enter validate_request!")
        endpoint.read()
        data = bytearray(endpoint.stream)
        if len(data) < 5:
            return
        expect_length = 10

        def check_confirm():
            if data[0] != 5:
                return "version wrong!"
            if data[1] not in [1, 3]:
                return "CMD should be connect or udp associate!"
            if data[2] != 0:
                return "rsv wrong!"
            if data[3] not in [1, 3]:
                return "atyp wrong!"
            if data[3] == 3 and data[4] < 1:
                return "length wrong!"
            return None

        msg = check_confirm()
        if msg:
            self._error_validate_method(endpoint, msg, b'\x05\x01\x00\x01\x00\x00\x00\x00\x10\x10')
            return
        if data[3] == 3:
            expect_length = 7 + data[4]
        if len(data) < expect_length:
            return

        if data[3] == 1:
            ip = socket.inet_ntoa(endpoint.stream[4:8])
            port = data[8] * 256 + data[9]
            endpoint.address = (ip, port)
        else:
            host = bytes.decode(endpoint.stream[5:5 + data[4]])
            port = data[5 + data[4]] * 256 + data[6 + data[4]]
            endpoint.address = (host, port)
        self.set_status(endpoint, ProtocolStatus.ProtocolValidated)
        self.create_remote_endpoint(endpoint)
        endpoint.peer.stream = b'\x05\x00\x00\x01\x00\x00\x00\x00\x10\x10'
        endpoint.stream = endpoint.stream[expect_length:]

    def error_response(self, endpoint):
        self.logger.debug("enter error_response!")
        endpoint.write()
        self.set_status(endpoint, ProtocolStatus.ProtocolValidated)
        context.POOL.modify(endpoint, EVENT_READ)

    def handle_stop(self, endpoint):
        self.logger.debug("enter handle_stop!")
        endpoint.destroy()

    def handle_error(self, endpoint, error):
        self.logger.debug("enter handle_error!")
        self.handle_stop(endpoint)
        self.logger.error(repr(error))

    def handle_remote_error(self, endpoint, error):
        self.logger.debug("enter handle_remote_error!")
        self.logger.error(repr(error))
        endpoint.peer.destroy()
        self._error_validate_method(endpoint, "connect to the address wrong!",
                                    b'\x05\x01\x00\x01\x00\x00\x00\x00\x10\x10')

    def create_remote_endpoint(self, endpoint):
        (sock, connecting) = client_socket(endpoint.address)
        peer = Endpoint(sock, False, endpoint.address)
        endpoint.peer = peer
        peer.peer = endpoint
        peer.connecting = connecting
        if connecting:
            self.set_status(peer, Socks5Status.Connecting)
            context.POOL.register(peer, EVENT_WRITE)
        else:
            self.set_status(peer, ProtocolStatus.ProtocolValidated)

    def handle_connecting(self, endpoint):
        endpoint.peer.try_turn = endpoint.peer.try_turn + 1
        self.logger.debug("enter handle_connecting!")
        errno = endpoint.sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if errno != 0:
            if endpoint.peer.try_turn < context.MAX_CONNECT_TURN:
                self.create_remote_endpoint(endpoint.peer)
                endpoint.destroy()
            else:
                raise Exception("socket connecting error! errno is " + str(errno))
        self.set_status(endpoint, ProtocolStatus.ProtocolValidated)
        context.POOL.set_events(endpoint)
        context.POOL.set_events(endpoint.peer)

    def handle_remote_error_peer(self, endpoint, error):
        self.logger.debug("enter handle_remote_error_peer!")
        self.handle_remote_error(endpoint.peer, error)
