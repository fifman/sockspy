#! /usr/bin/env python
# -*- coding: utf-8 -*-
from sockspy.core import context, config
from sockspy.socks_impl import socks5


def run():
    cfg = config.get_default_config()
    config.set_default_log_config()
    ctx = context.AppContext(socks5.Socks5Engine, cfg)
    ctx.run()
