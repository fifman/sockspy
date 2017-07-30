#! /usr/bin/env python
# -*- coding: utf-8 -*-

from sockspy.core import engine
import pytest


def try_instantiate(constructor):
    with pytest.raises(Exception) as ex:
        constructor()
    assert ex.type == TypeError
    assert "Can't instantiate abstract class" in str(ex.value)


def test_instantiate():
    try_instantiate(engine.EndpointEngine)
    try_instantiate(engine.StatusHandlerEngine)
    try_instantiate(engine.EventHandlerEngine)
