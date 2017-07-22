#! /usr/bin/env python
# -*- coding: utf-8 -*-
from sockspy.core.pool import EndpointPool
from sockspy.socks_impl.socks5 import Socks5Engine


def get_socks5_engine():
    return Socks5Engine()


ENGINES = [get_socks5_engine()]


def process_endpoint(endpoint):
    for engine in ENGINES:
        engine.process(endpoint)


MAX_CONNECT_TURN = 3


POOL = EndpointPool()
