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
from gevent import spawn
from gevent.queue import Queue
from fatbotslim.tcp import TCP, SSL
from fatbotslim.log import create_logger


class NullMessage(Exception):
    pass


class IRC(object):
    """
    Provides a basic interface to an IRC server.
    """
    def __init__(self, settings):
        self.server = settings['server']
        self.port = settings['port']
        self.ssl = settings['ssl']
        self.channels = settings['channels']
        self.nick = settings['nick']
        self.realname = settings['realname']
        self.line = {'prefix': '', 'command': '', 'args': ['', '']}
        self.lines = Queue()
        self.log = create_logger(__name__)
        self._connect()
        self._event_loop()

    def _create_connection(self):
        transport = SSL if self.ssl else TCP
        return transport(self.server, self.port)

    def _connect(self):
        self.conn = self._create_connection()
        spawn(self.conn.connect)
        self._set_nick(self.nick)
        self.cmd('USER', (self.nick, ' 3 ', '* ', self.realname))

    def _disconnect(self):
        self.conn.disconnect()

    def _send(self, command):
        self.log.debug(command)
        self.conn.oqueue.put(command)

    def _parse_msg(self, msg):
        """
        Breaks a message from an IRC server into its prefix, command, and arguments.
        """
        prefix = ''
        trailing = []
        if not msg:
            raise NullMessage('Received an empty line from the server')
        if msg[0] == ':':
            prefix, msg = msg[1:].split(' ', 1)
        if msg.find(' :'):
            msg, trailing = msg.split(' :', 1)
            args = msg.split()
            args.append(trailing)
        else:
            args = msg.split()
        command = args.pop(0)
        return prefix, command, args

    def _event_loop(self):
        """
        The main event loop.
        Data from the server is parsed here using `_parse_msg`. Parsed events are
        put in the object's event queue (`self.events`).
        """
        while True:
            line = self.conn.iqueue.get()
            self.log.debug(line)
            try:
                prefix, command, args = self._parse_msg(line)
            except ValueError:
                self.log.error("Received a line that can't be parsed:%(linesep)s%(line)s%(linesep)s%(exception)s" % dict(
                    linesep=linesep, line=line, exception=format_exc()
                ))
                continue
            self.line = {'prefix': prefix, 'command': command, 'args': args}
            self.lines.put(self.line)
            if command == '433': # nick in use
                self.nick += '_' #TODO: generate random suffix
                self._set_nick(self.nick)
            elif command == 'PING':
                self.cmd('PONG', args)
            elif command == '001':
                self._join_chans(self.channels)

    def _set_nick(self, nick):
        self.cmd('NICK', nick)

    def _join_chans(self, channels):
        for c in channels:
            self.cmd('JOIN', c)

    def cmd(self, command, args, prefix=None):
        if prefix is None:
            prefix = ''
        raw_cmd = '{0} {1} {2}'.format(prefix, command, ''.join(args)).strip()
        self._send(raw_cmd)

    def msg(self, target, msg):
        self.cmd('PRIVMSG', ('{0} :{1}'.format(target, msg)))
