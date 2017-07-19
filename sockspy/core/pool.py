#! /usr/bin/env python
# -*- coding: utf-8 -*-

from selectors import DefaultSelector, EpollSelector, DevpollSelector, KqueueSelector, PollSelector, SelectSelector, EVENT_READ

from sockspy.core.endpoint import Endpoint

TYPE_DEFAULT = 0
TYPE_SELECT = 1
TYPE_POLL = 2
TYPE_EPOLL = 3
TYPE_DEVPOLL = 4
TYPE_KQUEUE = 5


class EndpointPool:

    def __init__(self, selector_type=TYPE_DEFAULT):
        self.poller = {
            TYPE_DEFAULT: DefaultSelector,
            TYPE_SELECT: SelectSelector,
            TYPE_POLL: PollSelector,
            TYPE_EPOLL: EpollSelector,
            TYPE_DEVPOLL: DevpollSelector,
            TYPE_KQUEUE: KqueueSelector
        }.get(selector_type)()
        self.msg_size = 4096

    def set_listener(self, listener):
        self.listener = listener
        self.poller.register(listener, EVENT_READ)

    def register(self, endpoint, events):
        self.poller.register(endpoint, events)

    def modify(self, endpoint, events):
        self.poller.modify(endpoint, events)

    def unregister(self, endpoint):
        self.poller.unregister(endpoint)

    def poll(self):
        for (key, events) in self.poller.select():
            endpoint = key.fileobj
            if endpoint == self.listener:
                sock, address = self.listener.accept()
                self.create_local_endpoint(sock)
            endpoint.events = events
            endpoint.ready()

    def create_local_endpoint(self, sock):
        endpoint = Endpoint(sock)
        endpoint.peer = endpoint
        self.register(endpoint, EVENT_READ)
