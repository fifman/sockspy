#! /usr/bin/env python
# -*- coding: utf-8 -*-
import socket
import enum
from sockspy.core import engine
import selectors
import logging


@enum.unique
class Socks5Status(enum.Enum):
    MethodValidated = 3
    ValidateRequest = 4
    Failed = 5


class Socks5Engine(engine.SocksEngine):
    def __init__(self, config, pool):
        engine.SocksEngine.__init__(self, config, pool)
        self.logger = logging.getLogger(__name__)

    def get_handler_in_protocol_validation(self, status, endpoint):
        # self.logger.debug("enter protocol method select!")
        return {
            engine.ProtocolStatus.Init: self.validate_method,
            Socks5Status.MethodValidated: self.method_validated,
            Socks5Status.ValidateRequest: self.validate_request,
            Socks5Status.Failed: self.error_response
        }.get(status)

    def validate_method(self, endpoint):
        self.logger.debug("enter validate_method!")
        if bytearray(endpoint.stream)[0] != 5:
            self._error_validate(endpoint, "Only supports socks5 protocol!", b'\x05\xFF')
            return
        if len(endpoint.stream) < 3:
            return
        method_num = bytearray(endpoint.stream)[1]
        if method_num > 255 or method_num < 1:
            self._error_validate(endpoint, "Number of methods is not in [1,255]!", b'\x05\xFF')
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
                self.pool.modify(endpoint, selectors.EVENT_WRITE)
                return
        self._error_validate(endpoint, "Only support 'No authentication required' method!", b'\x05\xFF')

    def _error_validate(self, endpoint, msg, stream):
        self.logger.error(msg)
        endpoint.peer.stream = stream
        self.set_status(endpoint, Socks5Status.Failed)
        self.pool.modify(endpoint, selectors.EVENT_WRITE)

    def method_validated(self, endpoint):
        self.logger.debug("enter method_validated")
        self.set_status(endpoint, Socks5Status.ValidateRequest)
        self.pool.modify(endpoint, selectors.EVENT_READ)

    def validate_request(self, endpoint):
        self.logger.debug("enter validate_request!")
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
            self._error_validate(endpoint, msg, b'\x05\x01\x00\x01\x00\x00\x00\x00\x10\x10')
            return
        if data[3] == 3:
            expect_length = 7 + data[4]
        if len(data) < expect_length:
            return

        if data[3] == 1:
            ip = socket.inet_ntoa(endpoint.stream[4:8])
            port = data[8] * 256 + data[9]
            address = (ip, port)
        else:
            host = bytes.decode(endpoint.stream[5:5 + data[4]])
            port = data[5 + data[4]] * 256 + data[6 + data[4]]
            address = (host, port)
        endpoint.address = address
        self.set_status(endpoint, engine.ProtocolStatus.ProtocolValidated)
        self.create_remote_endpoint(endpoint)
        endpoint.peer.stream = b'\x05\x00\x00\x01\x00\x00\x00\x00\x10\x10'
        endpoint.stream = endpoint.stream[expect_length:]

    def error_response(self, endpoint):
        self.logger.debug("enter error_response!")
        self.set_status(endpoint, engine.ProtocolStatus.ProtocolValidated)
        self.pool.modify(endpoint, selectors.EVENT_READ)
