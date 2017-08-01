#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `sockspy` package."""
import multiprocessing, os, signal, pytest, requests, time
from click.testing import CliRunner
from sockspy import cli


SERVER_HOST = "localhost"
SERVER_PORT = 3333


def _try_socks5_proxy(url):
    proxy = {
        'http':'socks5://'+SERVER_HOST+':'+str(SERVER_PORT),
        'https':'socks5://'+SERVER_HOST+':'+str(SERVER_PORT)
    }
    return requests.get(url, proxies=proxy, timeout=3)


def _try_socks5(test_server):

    def run_sockspy():
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0

    _wrap_test(2, run_sockspy, test_server)


def test_valid_address():

    def test_server():
        response = _try_socks5_proxy("https://www.bing.com")
        assert response.status_code == requests.codes.ok

    _try_socks5(test_server)


def test_invalid_address():

    def test_server():
        with pytest.raises(Exception) as ex:
            response = _try_socks5_proxy("https://www.baidu.co")
            assert response.status_code != requests.codes.ok
        assert ex is not None

    _try_socks5(test_server)


def _wrap_test(sec, cb_test, cb_com=None):
    pid = os.getpid()

    def cb_kill():
        time.sleep(sec)
        if cb_com:
            cb_com()
        os.kill(pid, signal.SIGINT)

    process = multiprocessing.Process(target=cb_kill)
    process.start()
    try:
        cb_test()
    finally:
        process.terminate()
        process.join()


# host, port, timeout, itimeout, qsize, backlog, maxtry, bsize, verbose, logfile=None, logcfgfile = None, cfgfile=None
def test_command_line_interface():

    def cli_test():
        runner = CliRunner()
        result = runner.invoke(cli.main, [
            "--timeout", 10,
            "--itimeout", 60,
            "--host", "localhost",
            "--port", 3333,
            "--qsize", 100,
            "--backlog", 1024,
            "--maxtry", 3,
            "--bsize", 4096,
            "--verbose", 2,
            "--logfile", "/var/log/sockspy",
            "--logcfgfile", "tests/log.yaml"
        ])
        assert result.exit_code == 0
        assert 'started' in result.output               # server successfully started
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert 'Simple python implementation of a socks5 proxy server.' in help_result.output

    _wrap_test(3, cli_test)

