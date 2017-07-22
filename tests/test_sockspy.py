#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `sockspy` package."""

from click.testing import CliRunner
from sockspy import sockspy
from sockspy import cli
import requests
import time
import threading


def try_socks5_proxy(server_host, server_port):
    proxy = {
        'http':'socks5://'+server_host+':'+str(server_port),
        'https':'socks5://'+server_host+':'+str(server_port)
    }
    url = 'https://www.baidu.com'
    return requests.get(url, proxies=proxy)


SERVER_HOST = "localhost"
SERVER_PORT = 3333


def test_socks5():

    def run_sockspy():
        sockspy.run(SERVER_HOST, SERVER_PORT)

    thread = threading.Thread(None, run_sockspy, daemon=True)
    thread.start()
    time.sleep(2)
    response = try_socks5_proxy(SERVER_HOST, SERVER_PORT)
    assert response.status_code == requests.codes.ok


def test_run():
    sockspy.run(SERVER_HOST, SERVER_PORT)


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'sockspy.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output
