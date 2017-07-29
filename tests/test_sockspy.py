#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `sockspy` package."""
import multiprocessing
import pytest
from click.testing import CliRunner
from sockspy import sockspy_main
from sockspy import cli
import requests
import time


SERVER_HOST = "localhost"
SERVER_PORT = 3333


def _try_socks5_proxy(url):
    proxy = {
        'http':'socks5://'+SERVER_HOST+':'+str(SERVER_PORT),
        'https':'socks5://'+SERVER_HOST+':'+str(SERVER_PORT)
    }
    return requests.get(url, proxies=proxy)


def _try_socks5(url):

    def run_sockspy():
        sockspy_main.run()

    process = multiprocessing.Process(target=run_sockspy)
    process.start()
    time.sleep(2)
    try:
        return _try_socks5_proxy(url)
    finally:
        process.terminate()
        process.join()


def test_valid_address():
    response = _try_socks5("https://www.baidu.com")
    assert response.status_code == requests.codes.ok


def test_invalid_address():
    with pytest.raises(Exception) as ex:
        response = _try_socks5("https://www.baidu.co")
        assert response.status_code != requests.codes.ok
    print(repr(ex))
    assert ex is not None


def test_run():
    sockspy_main.run()


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.sockspy_main)
    assert result.exit_code == 0
    assert 'sockspy.cli.main' in result.output
    help_result = runner.invoke(cli.sockspy_main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output
