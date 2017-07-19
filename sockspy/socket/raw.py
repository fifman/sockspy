#! /usr/bin/env python
# -*- coding: utf-8 -*-

import socket


def server_socket(address, backlog=5):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setblocking(False)
    server.bind(address)
    server.listen(backlog)
    return server


def client_socket(address):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(0)
    sock.connect(address)
    return sock
