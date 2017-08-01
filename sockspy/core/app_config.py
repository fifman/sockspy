#! /usr/bin/env python
# -*- coding: utf-8 -*-
import yaml
import os.path
import logging.config


def get_config_by_file(log_cfg_path):
    full_path = os.path.abspath(os.path.expanduser(log_cfg_path))
    with open(full_path, 'r') as file_stream:
        return yaml.safe_load(file_stream)


def get_default_log_config():
    return {
        "version": 1,
        "formatters": {
            "simple": {
                "format": '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            "debug": {
                "format": '   <<< %(asctime)s - %(message)s',
                "datefmt": '%H:%M:%S'
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "stream": "ext://sys.stdout"
            },
            "nil": {
                "class": "logging.NullHandler"
            }
        },
        "loggers": {
            "sockspy": {
                "level": "ERROR",
                "handlers": ["console"],
                "propagate": "no"
            }
        },
        "root": {
            "level": "ERROR",
            "handlers": ["console"]
        },
        "disable_existing_loggers": False
    }


def set_log_config(verbose, logfile):
    log_config = get_default_log_config()
    log_level = {
        0: "ERROR",
        1: "INFO",
        2: "DEBUG"
    }.get(verbose, "ERROR")
    if logfile:
        log_config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "debug",
            "filename": os.path.abspath(os.path.expanduser(logfile)),
            "mode": "w"
        }
        log_config["loggers"]["sockspy"]["handlers"].append("file")
    log_config["loggers"]["sockspy"]["level"] = log_level
    log_config["root"]["level"] = log_level
    logging.config.dictConfig(log_config)


class Config(object):

    def __init__(self, address=("localhost", 3333), timeout=10, endpoint_timeout=60, max_queue_size=50, msg_size=4096, max_try_turn=3, backlog=1024, verbose=0, logfile=None, logcfgfile=None):
        self.address = address
        self.msg_size = msg_size
        self.max_try_turn = max_try_turn
        self.backlog = backlog
        self.timeout = timeout
        self.max_queue_size = max_queue_size
        self.endpoint_timeout = endpoint_timeout
        self.verbose = verbose
        self.logfile = logfile
        self.logcfgfile = logcfgfile
        set_log_config(verbose, logfile)
