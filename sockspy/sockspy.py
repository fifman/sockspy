#! /usr/bin/env python
# -*- coding: utf-8 -*-
import logging.config
import yaml
from pkg_resources import resource_string
config = yaml.safe_load(resource_string("sockspy.resources", "log.yaml"))
logging.config.dictConfig(config)

from sockspy.core.context import POOL
from sockspy.socket.raw import server_socket


def run(host="localhost", port=3333, msg_size=4096):
    POOL.msg_size = msg_size
    listener = server_socket((host, port))
    POOL.set_listener(listener)
    POOL.poll()
