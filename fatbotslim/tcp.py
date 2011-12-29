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

from os import linesep
from traceback import format_exc
from gevent import spawn, joinall, killall
from gevent.queue import Queue
from gevent.socket import socket
from gevent.ssl import wrap_socket
from fatbotslim.log import create_logger

class TCP(object):
    """
    Wraps a TCP connection.
    """
    def __init__(self, host, port, timeout=300):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._ibuffer = ''
        self._obuffer = ''
        self.iqueue = Queue()
        self.oqueue = Queue()
        self._socket = self._create_socket()
        self.log = create_logger(__name__)

    def _create_socket(self):
        return socket()

    def _recv_loop(self):
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
        while True:
            line = self.oqueue.get().splitlines()[0][:500]
            self._obuffer += line.encode('utf-8', 'replace') + '\r\n'
            while self._obuffer:
                sent = self._socket.send(self._obuffer)
                self._obuffer = self._obuffer[sent:]

    def connect(self):
        self._socket.connect((self.host, self.port))
        try:
            jobs = [spawn(self._recv_loop), spawn(self._send_loop)]
            joinall(jobs)
        finally:
            killall(jobs)

    def disconnect(self):
        self._socket.close()


class SSL(TCP):
    """
    SSL wrapper for TCP connections.
    """
    def _create_socket(self):
        s = super(SSL, self)._create_socket()
        return wrap_socket(s)
