#! /usr/bin/env python
# -*- coding: utf-8 -*-
import click
from sockspy import sockspy_main
from sockspy.core import app_config


@click.command()
@click.option("--host", help="The host that sockspy server will listen to, default is 'localhost'.")
@click.option("--port", help="The port that sockspy server will listen to, default is 3333.")
@click.option("--itimeout", help="Maximum seconds sockspy waits for inactive sockets before put them into  the recycle queue.")
@click.option("--timeout", help="Timeout of polling. Default is 10.")
@click.option("--qsize", help="Maximum size of the recycle queue before trigger recycling. Default is 100.")
@click.option("--backlog", help="Backlog parameter of server socket accept function. Default is 1024.")
@click.option("--maxtry", help="Maximum times to try to connect to remote addresss. Default is 3.")
@click.option("--bsize", help="Buffer size for socket read and write. Default is 4096.")
@click.option("--verbose", help="Log message level,\n    0: only print error message;\n   1: print info message;\n   2: print debug message. Default is 0.")
@click.option("--logfile", help="Log message level,\n    0: only print error message;\n   1: print info message;\n   2: print debug message.")
@click.option("--logcfgfile", help="yaml file to config logger.")
@click.option("--cfgfile", help="yaml file to read config from.")
def main(host, port, timeout, itimeout, qsize, backlog, maxtry, bsize, verbose, logfile=None, logcfgfile = None, cfgfile=None):
    """Simple python implementation of a socks5 proxy server. """

    dict_cfg = {}
    if cfgfile:
        dict_cfg = app_config.get_config_by_file(cfgfile)

    def get_param(key, param, default):
        return param or dict_cfg.get(key, None) or default

    cfg = app_config.Config(
        address=(get_param("host", host, "localhost"), get_param("port", port, 3333)),
        timeout= get_param("timeout", timeout, 10),
        msg_size = get_param("bsize", bsize, 4096),
        max_try_turn = get_param("maxtry", maxtry, 3),
        backlog = get_param("backlog", backlog, 1024),
        max_queue_size = get_param("qsize", qsize, 100),
        endpoint_timeout = get_param("itimeout", itimeout, 60),
        verbose = get_param("verbose", verbose, 0),
        logfile = get_param("logfile", logfile, None),
        logcfgfile = get_param("logcfgfile", logcfgfile, None)
    )
    click.echo("Starting sockspy...")
    sockspy_main.run(cfg)


if __name__ == "__main__":
    main()
