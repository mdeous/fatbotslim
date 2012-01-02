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

from collections import defaultdict
from os import linesep
from random import choice
from traceback import format_exc
from gevent import spawn
from gevent.pool import Group
from gevent.queue import Queue
from fatbotslim.irc.codes import *
from fatbotslim.irc.tcp import TCP, SSL
from fatbotslim.log import create_logger

log = create_logger(__name__)


class NullMessage(Exception):
    pass


class Message(object):
    def __init__(self, data):
        self._raw = data
        self.prefix, self.command, self.args = Message.parse(data)

    @classmethod
    def parse(cls, data):
        prefix = ''
        if not data:
            raise NullMessage('Received an empty line from the server')
        if data[0] == ':':
            prefix, msg = data[1:].split(' ', 1)
        if data.find(' :'):
            msg, trailing = data.split(' :', 1)
            args = msg.split()
            args.append(trailing)
        else:
            args = data.split()
        command = args.pop(0)
        return prefix, command, args


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
        self._pool = Group()
        self._handlers = defaultdict(set)

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
        log.debug(command)
        self.conn.oqueue.put(command)

    def _parse_msg(self, msg):
        """
        Breaks a message from an IRC server into its prefix, command, and arguments.
        """
        #TODO: use a Message object to store received data
        prefix = ''
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
            log.debug(line)
            try:
                message = Message(line)
#                prefix, command, args = self._parse_msg(line)
            except ValueError:
                log.error("Received a line that can't be parsed:%(linesep)s%(line)s%(linesep)s%(exception)s" % dict(
                    linesep=linesep, line=line, exception=format_exc()
                ))
                continue
            self.line = {
                'prefix': message.prefix,
                'command': message.command,
                'args': message.args
            }
            self.lines.put(self.line)
            if message.command == ERR_NICKNAMEINUSE:
                self._set_nick(IRC.randomize_nick(self.nick))
            elif message.command == PING:
                self.cmd('PONG', message.args)
            elif message.command == CONNECTED:
                self._join_chans(self.channels)
            self._handle(message)

    def _set_nick(self, nick):
        self.cmd('NICK', nick)

    def _join_chans(self, channels):
        for c in channels:
            self.cmd('JOIN', c)

    def _handle(self, msg):
        for handler in self._handlers[msg.command]:
            self._pool.spawn(handler, msg, self)

    @classmethod
    def randomize_nick(cls, base, suffix_length=3):
        suffix = ''.join(choice('0123456789') for _ in range(suffix_length))
        return '{0}_{1}'.format(base, suffix)

    def add_handler(self, handler):
        for command in handler.commands:
            self._handlers[command].add(handler.commands[command])

    def cmd(self, command, args, prefix=None):
        if prefix is None:
            prefix = ''
        raw_cmd = '{0} {1} {2}'.format(prefix, command, ''.join(args)).strip()
        self._send(raw_cmd)

    def msg(self, target, msg):
        self.cmd('PRIVMSG', ('{0} :{1}'.format(target, msg)))

    def run(self):
        self._connect()
        self._event_loop()


def spawn_client(settings):
    client = IRC(settings)
    return spawn(client.run), client
