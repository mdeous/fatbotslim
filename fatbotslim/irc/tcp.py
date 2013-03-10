# -*- coding: utf-8 -*-
#
# This file is part of FatBotSlim.
#
# FatBotSlim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FatBotSlim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FatBotSlim. If not, see <http://www.gnu.org/licenses/>.
#
"""
.. module:: fatbotslim.irc.tcp

.. moduleauthor:: Mathieu D. (MatToufoutu)

This module contains the low-level networking stuff.
"""

from gevent import spawn, joinall, killall
from gevent.queue import Queue
from gevent.socket import socket
from gevent.ssl import wrap_socket

from fatbotslim.log import create_logger

log = create_logger(__name__)


class TCP(object):
    """
    A TCP connection.
    """
    def __init__(self, host, port, timeout=300):
        """
        :param host: server's hostname
        :type host: str
        :param port: server's port
        :type port: int
        :param timeout: maximum time a request/response should last.
        :type timeout: int
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self._ibuffer = ''
        self._obuffer = ''
        self.iqueue = Queue()
        self.oqueue = Queue()
        self._socket = self._create_socket()

    def _create_socket(self):
        """
        Creates a new socket and sets its timeout.

        :return: new socket.
        :rtype: :class:`gevent.socket.socket`
        """
        s = socket()
        s.settimeout(self.timeout)
        return s

    def _recv_loop(self):
        """
        Waits for data forever and feeds the input queue.
        """
        while True:
            try:
                data = self._socket.recv(4096)
                self._ibuffer += data
                while '\r\n' in self._ibuffer:
                    line, self._ibuffer = self._ibuffer.split('\r\n', 1)
                    self.iqueue.put(line)
            except Exception:
                break

    def _send_loop(self):
        """
        Waits for data in the output queue to send.
        """
        while True:
            try:
                line = self.oqueue.get().splitlines()[0][:500]
                self._obuffer += line + '\r\n'
                while self._obuffer:
                    sent = self._socket.send(self._obuffer)
                    self._obuffer = self._obuffer[sent:]
            except Exception:
                break

    def connect(self):
        """
        Connects the socket and spawns the send/receive loops.
        """
        jobs = []
        self._socket.connect((self.host, self.port))
        try:
            jobs = [spawn(self._recv_loop), spawn(self._send_loop)]
            joinall(jobs)
        finally:
            killall(jobs)

    def disconnect(self):
        """
        Closes the socket.
        """
        self._socket.close()


class SSL(TCP):
    """
    SSL wrapper for a :class:`fatbotslim.irc.tcp.TCP` connection.
    """
    def _create_socket(self):
        """
        Creates a new SSL enabled socket and sets its timeout.
        """
        log.warning('No certificate check is performed for SSL connections')
        s = super(SSL, self)._create_socket()
        return wrap_socket(s)
