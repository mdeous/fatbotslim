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

import re
from collections import defaultdict
from os import linesep
from random import choice
from traceback import format_exc
from gevent import spawn
from gevent.pool import Group
from fatbotslim.irc.codes import *
from fatbotslim.irc.tcp import TCP, SSL
from fatbotslim.log import create_logger

ctcp_re = re.compile(r'\x01(.*?)\x01')


class NullMessage(Exception):
    pass


class Message(object):
    def __init__(self, data):
        self._raw = data
        self.src, self.dst, self.command, self.args = Message.parse(data)

    def __str__(self):
        return "<Message(src='{0}', command='{1}', args={2})>".format(
            self.src.name, self.command, self.args
        )

    @classmethod
    def parse(cls, data):
        src = ''
        dst = None
        if not data:
            raise NullMessage('Received an empty line from the server')
        if data[0] == ':':
            src, data = data[1:].split(' ', 1)
        if ' :' in data:
            data, trailing = data.split(' :', 1)
            args = data.split()
            args.append(trailing)
        else:
            args = data.split()
        command = args.pop(0)
        if command == PRIVMSG:
            dst = args.pop(0)
            if ctcp_re.match(args[0]):
                args = args[0].strip('\x01').split()
                command = 'CTCP_'+args.pop(0)
        return Source(src), dst, command, args


class Source(object):
    def __init__(self, data):
        self._raw = data
        self.name, self.mode, self.user, self.host = Source.parse(data)

    def __str__(self):
        return "<Source(nick='{0}', mode='{1}', user='{2}', host='{3}')>".format(
            self.name, self.mode, self.user, self.host
        )

    @classmethod
    def parse(cls, name):
        try:
            nick, rest = name.split('!')
        except ValueError:
            return name, None, None, None
        try:
            mode, rest = rest.split('=')
        except ValueError:
            mode, rest = None, rest
        try:
            user, host = rest.split('@')
        except ValueError:
            return nick, mode, rest, None
        return nick, mode, user, host


class IRC(object):
    """
    Provides a basic interface to an IRC server.
    """
    quit_msg = "I'll be back!"

    def __init__(self, settings):
        self.server = settings['server']
        self.port = settings['port']
        self.ssl = settings['ssl']
        self.channels = settings['channels']
        self.nick = settings['nick']
        self.realname = settings['realname']
        self._pool = Group()
        self._handlers = defaultdict(set)
        self.log = create_logger(__name__, level=settings.get('loglevel', 'INFO'))

    def _create_connection(self):
        transport = SSL if self.ssl else TCP
        return transport(self.server, self.port)

    def _connect(self):
        self.conn = self._create_connection()
        spawn(self.conn.connect)
        self._set_nick(self.nick)
        self.cmd('USER', (self.nick, ' 3 ', '* ', self.realname))

    def _send(self, command):
        self.log.debug('-> '+command)
        self.conn.oqueue.put(command)

    def _event_loop(self):
        """
        The main event loop.
        Data from the server is parsed here using `_parse_msg`. Parsed events are
        put in the object's event queue (`self.events`).
        """
        while True:
            line = self.conn.iqueue.get()
            self.log.debug('<- '+line)
            try:
                message = Message(line)
            except ValueError:
                self.log.error("Received a line that can't be parsed:%(linesep)s" \
                               "%(line)s%(linesep)s%(exception)s" % dict(
                    linesep=linesep, line=line, exception=format_exc()
                ))
                continue
            if message.command == ERR_NICKNAMEINUSE:
                self._set_nick(IRC.randomize_nick(self.nick))
            elif message.command == PING:
                self.cmd('PONG', message.args)
            elif message.command == RPL_CONNECTED:
                self._join_chans(self.channels)
            if message.command not in ALL_CODES:
                self.log.info("Unknown code received: {0}".format(message.command))
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

    def ctcp_reply(self, command, dst, message=None):
        if message is None:
            raw_cmd = '\x01{0}\x01'.format(command)
        else:
            raw_cmd = '\x01{0} {1}\x01'.format(command, message)
        self.notice(dst, raw_cmd)

    def msg(self, target, msg):
        self.cmd('PRIVMSG', ['{0} :{1}'.format(target, msg)])

    def notice(self, target, msg):
        self.cmd('NOTICE', ['{0} :{1}'.format(target, msg)])

    def disconnect(self):
        self.cmd('QUIT', [':{0}'.format(self.quit_msg)])

    def run(self):
        self._connect()
        self._event_loop()
