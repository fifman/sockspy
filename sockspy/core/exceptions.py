#! /usr/bin/env python
# -*- coding: utf-8 -*-


class ReadOrWriteNoDataError(Exception):
    """
    This exception is thrown when a socket reads or writes 0 byte, which indicates that the remote side is disconnected.
    """
    pass


class StatusRegisterError(Exception):
    pass
