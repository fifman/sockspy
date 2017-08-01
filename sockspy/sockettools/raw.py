#! /usr/bin/env python
# -*- coding: utf-8 -*-

import socket


def server_socket(address, backlog=5):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(address)
    server.listen(backlog)
    server.setblocking(False)
    return server


def client_socket(address):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(0)
    in_blocking = False
    try:
        sock.connect(address)
    except BlockingIOError:
        in_blocking = True
    return (sock, in_blocking)
