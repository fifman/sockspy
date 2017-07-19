#! /usr/bin/env python
# -*- coding: utf-8 -*-
import socket
from enum import unique, Enum
from sockspy.core.context import POOL
from sockspy.core.engine import SocksEngine, ProtocolStatus
from selectors import EVENT_WRITE, EVENT_READ
import logging


@unique
class Socks5Status(Enum):
    Version = 1
    Method = 2
    Validated = 3
    ValidationResponded = 4
    # Failed = 5
    Confirmed = 6


class Socks5Engine(SocksEngine):
    def __init__(self):
        SocksEngine.__init__(self)

    def get_handlers_in_protocol_validation(self, status, endpoint):
        handler = {
            (Socks5Status.Init, EVENT_READ): (self.validate_method, self.handle_stop, self.handle_error),
            (None, EVENT_READ): (self.validate_version, self.handle_stop, self.handle_error),
            (Socks5Status.Version, EVENT_READ): (self.validate_method, self.handle_stop, self.handle_error),
            (Socks5Status.Validated, EVENT_WRITE): (self.respond_validation, self.handle_stop, self.handle_error),
            (Socks5Status.ValidationResponded, EVENT_READ): (self.confirm, self.handle_stop, self.handle_error),
            (Socks5Status.Confirmed, EVENT_WRITE): (self.respond_confirm, self.handle_stop, self.handle_remote_error)
        }.get((status, endpoint.events), None)
        return [] if handler == None else [handler]

    def validate_version(self, endpoint):
        endpoint.read()
        if endpoint.stream[0] != b'\x05':
            self._error_validate_method(endpoint, "Only supports socks5 protocol!", b'\x05\xFF')
        else:
            self.set_status(endpoint, Socks5Status.Version)

    def validate_method(self, endpoint):
        endpoint.read()
        if len(endpoint.stream) < 3:
            return
        method_num = int.from_bytes(endpoint.stream[1], 'little')
        if method_num > 255 or method_num < 1:
            self._error_validate_method(endpoint, "Number of methods is not in [1,255]!", b'\x05\xFF')
            return
        if len(endpoint.stream) < 2 + method_num:
            return
        self._validate_method_type(endpoint.stream)

    def _validate_method_type(self, endpoint):
        # noinspection PyTypeChecker
        for octet in endpoint.stream[2: (int.from_bytes(endpoint.stream[1],'little')+1)]:
            if octet == b'\x00':
                endpoint.stream = b'\x05\x00'
                self.set_status(endpoint, Socks5Status.Validated)
                endpoint.switch_events()
                return
        self._error_validate_method(endpoint, "Only support 'No authentication required' method!")

    def _error_validate_method(self, endpoint, msg, stream):
        logging.error(msg)
        endpoint.stream = stream
        self.set_status(endpoint, Socks5Status.Confirmed)
        endpoint.switch_events()

    def respond_validation(self, endpoint):
        endpoint.write()
        self.set_status(endpoint, Socks5Status.ValidationResponded)
        endpoint.switch_events()

    def confirm(self, endpoint):
        endpoint.read()
        data = endpoint.stream
        if len(data) < 5:
            return
        expect_length = 10

        def check_confirm():
            if data[0] != b'\x05':
                return "version wrong!"
            if data[1] not in [b'\x00', b'\x03']:
                return "protocol should be tcp or udp!"
            if data[2] != b'\x00':
                return "rsv wrong!"
            if data[3] not in [b'\x01', b'\x03']:
                return "atyp wrong!"
            if data[3] == b'\x03' and int.from_bytes(data[4], "little") < 1:
                return "length wrong!"
            return None

        msg = check_confirm()
        if msg:
            self._error_validate_method(endpoint, msg, b'\x05\x01\x00\x01\x00\x00\x00\x00\x10\x10')
            return
        if data[3] == b'\x03':
            host_length = int.from_bytes(data[4], "little")
            expect_length = 7 + host_length
        if len(data) < expect_length:
            return

        if data[3] == b'\x01':
            ip = socket.inet_ntoa(data[4:7])
            port = int.from_bytes(data[8:9], 'big')
            endpoint.address = (ip, port)
        else:
            host = bytes.decode(data[5:4 + expect_length])
            port = int.from_bytes(data[5 + expect_length:6 + expect_length], 'big')
            endpoint.address = (host, port)
        self.set_status(endpoint, Socks5Status.Confirmed)
        endpoint.switch_events()
        pass

    def respond_confirm(self, endpoint):
        endpoint.write()
        self.set_status(endpoint, ProtocolStatus.ProtocolValidated)
        endpoint.create_remote_endpoint()
        POOL.modify(endpoint, EVENT_WRITE | EVENT_READ)

    def handle_stop(self, endpoint):
        endpoint.destroy()

    def handle_error(self, endpoint, error):
        self.handle_stop(endpoint)
        logging.error(repr(error))

    def handle_remote_error(self, endpoint, error):
        logging.error(repr(error))
        endpoint.peer.destroy()
        self._error_validate_method(endpoint, "connect to the address wrong!", b'\x05\x01\x00\x01\x00\x00\x00\x00\x10\x10')
