#! /usr/bin/env python
# -*- coding: utf-8 -*-


def get_default_config():
    return Config(('localhost', 3333))


def get_config_by_file(path):
    pass


def get_config_by_cli():
    pass


def set_default_log_config():
    import logging.config
    import yaml
    from pkg_resources import resource_string
    log_config = yaml.safe_load(resource_string("sockspy.resources", "log.yaml"))
    logging.config.dictConfig(log_config)


class Config(object):

    def __init__(self, address, timeout=10, endpoint_timeout=60, max_queue_size=50, msg_size=4096, max_try_turn=3, backlog=1024):
        self.address = address
        self.msg_size = msg_size
        self.max_try_turn = max_try_turn
        self.backlog = backlog
        self.timeout = timeout
        self.max_queue_size = max_queue_size
        self.endpoint_timeout = endpoint_timeout
