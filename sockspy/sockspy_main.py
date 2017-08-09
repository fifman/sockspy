#! /usr/bin/env python
# -*- coding: utf-8 -*-
from sockspy.core import context
from sockspy.socks_impl import socks5


def run(cfg):
    ctx = context.AppContext(socks5.Socks5Engine, cfg)
    ctx.run()
