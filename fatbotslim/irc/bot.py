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
.. module:: fatbotslim.irc.bot

.. moduleauthor:: Mathieu D. (MatToufoutu)

This module contains IRC protocol related stuff.
"""

import re
from os import linesep
from random import choice
from traceback import format_exc
from gevent import spawn, joinall, killall
from gevent.pool import Group
from fatbotslim.irc.codes import *
from fatbotslim.irc.tcp import TCP, SSL
from fatbotslim.handlers import CTCPHandler, PingHandler, UnknownCodeHandler
from fatbotslim.log import create_logger

ctcp_re = re.compile(r'\x01(.*?)\x01')


class NullMessage(Exception):
    """
    Raised when an empty line is received from the server.
    """
    pass


class Message(object):
    """
    Holds informations about a line received from the server.
    """
    def __init__(self, data):
        """
        :param data: line received from the server.
        :type data: str
        """
        self._raw = data
        self.src, self.dst, self.command, self.args = Message.parse(data)

    def __str__(self):
        return "<Message(src='{0}', dst='{1}', command='{2}', args={3})>".format(
            self.src.name, self.dst, self.command, self.args
        )

    @classmethod
    def parse(cls, data):
        """
        Extracts message informations from `data`.

        :param data: received line.
        :type data: str
        :return: extracted informations (source, destination, command, args).
        :rtype: tuple(Source, str, str, list)
        :raise: :class:`fatbotslim.irc.NullMessage` if `data` is empty.
        """
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
        if command in (PRIVMSG, NOTICE):
            dst = args.pop(0)
            if ctcp_re.match(args[0]):
                args = args[0].strip('\x01').split()
                command = 'CTCP_'+args.pop(0)
        return Source(src), dst, command, args


class Source(object):
    """
    Holds informations about a message sender.

    """
    def __init__(self, prefix):
        """
        :param prefix: raw prefix with format ``<servername>|<nick>['!'<user>]['@'<host>]``.
        :type prefix: str
        """
        self._raw = prefix
        self.name, self.mode, self.user, self.host = Source.parse(prefix)

    def __str__(self):
        return "<Source(nick='{0}', mode='{1}', user='{2}', host='{3}')>".format(
            self.name, self.mode, self.user, self.host
        )

    @classmethod
    def parse(cls, prefix):
        """
        Extracts informations from `prefix`.

        :param prefix: raw prefix with format ``<servername>|<nick>['!'<user>]['@'<host>]``.
        :type prefix: str
        :return: extracted informations (nickname or host, mode, username, host).
        :rtype: tuple(str, str, str, str)
        """
        try:
            nick, rest = prefix.split('!')
        except ValueError:
            return prefix, None, None, None
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
    The main IRC bot class.
    """
    quit_msg = "I'll be back!"
    default_handlers = {
        CTCPHandler(),
        PingHandler(),
        UnknownCodeHandler(),
    }

    def __init__(self, settings):
        """
        The only expected argument is the bot's configuration,
        it should be a :class:`dict` with at least the following keys defined:

        * server: the ircd's host (:class:`str`)
        * port: the ircd's port (:class:`int`)
        * ssl: connect to the server using SSL (:class:`bool`)
        * channels: the channels to join upon connection (:class:`list`)
        * nick: the bot's nickname (:class:`str`)
        * realname: the bot's real name (:class:`str`)

        :param settings: bot configuration.
        :type settings: dict
        """
        self.server = settings['server']
        self.port = settings['port']
        self.ssl = settings['ssl']
        self.channels = settings['channels']
        self.nick = settings['nick']
        self.realname = settings['realname']
        self._pool = Group()
        self._handlers = set()
        self.log = create_logger(__name__, level=settings.get('loglevel', 'INFO'))
        for handler in self.default_handlers:
            self.add_handler(handler)

    def _create_connection(self):
        """
        Creates a transport channel.

        :return: transport channel instance
        :rtype: :class:`fatbotslim.irc.tcp.TCP` or :class:`fatbotslim.irc.tcp.SSL`
        """
        transport = SSL if self.ssl else TCP
        return transport(self.server, self.port)

    def _connect(self):
        """
        Connects the bot to the server and identifies itself.
        """
        self.conn = self._create_connection()
        spawn(self.conn.connect)
        self.set_nick(self.nick)
        self.cmd('USER', (self.nick, ' 3 ', '* ', self.realname))

    def _send(self, command):
        """
        Sends a raw line to the server.

        :param command: line to send.
        :type command: str
        """
        self.log.debug('-> '+command)
        self.conn.oqueue.put(command)

    def _event_loop(self):
        """
        The main event loop.
        Data from the server is parsed here using :func:`_parse_msg`.
        Parsed events are put in the object's event queue (`self.events`).
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
                self.set_nick(IRC.randomize_nick(self.nick))
            elif message.command == RPL_CONNECTED:
                for channel in self.channels:
                    self.join(channel)
            self._handle(message)

    def _handle(self, msg):
        """
        Pass a received message to the registered handlers.

        :param msg: received message
        :type msg: :class:`fatbotslim.irc.Message`
        """
        for handler in self._handlers:
            for command in handler.commands:
                if command == msg.command:
                    self._pool.spawn(handler.commands[command], msg, self)

    @classmethod
    def randomize_nick(cls, base, suffix_length=3):
        """
        Generates a pseudo-random nickname.

        :param base: prefix to use for the generated nickname.
        :type base: str
        :param suffix_length: amount of digits to append to `base`
        :type suffix_length: int
        :return: generated nickname.
        :rtype: str
        """
        suffix = ''.join(choice('0123456789') for _ in range(suffix_length))
        return '{0}_{1}'.format(base, suffix)

    def add_handler(self, handler):
        """
        Registers a new handler.

        :param handler: handler to register.
        :type handler: object
        """
        self._handlers.add(handler)

    def cmd(self, command, args, prefix=None):
        """
        Sends a command to the server.

        :param command: IRC code to send.
        :type command: str
        :param args: arguments to pass with the command.
        :type args: iterable
        :param prefix: optional prefix to prepend to the command.
        :type prefix: str or None
        """
        if prefix is None:
            prefix = ''
        raw_cmd = '{0} {1} {2}'.format(prefix, command, ''.join(args)).strip()
        self._send(raw_cmd)

    def ctcp_reply(self, command, dst, message=None):
        """
        Sends a reply to a CTCP request.

        :param command: CTCP command to use.
        :type command: str
        :param dst: sender of the initial request.
        :type dst: str
        :param message: data to attach to the reply.
        :type message: str
        """
        if message is None:
            raw_cmd = '\x01{0}\x01'.format(command)
        else:
            raw_cmd = '\x01{0} {1}\x01'.format(command, message)
        self.notice(dst, raw_cmd)

    def msg(self, target, msg):
        """
        Sends a message to an user or channel.

        :param target: user or channel to send to.
        :type target: str
        :param msg: message to send.
        :type msg: str
        """
        self.cmd('PRIVMSG', ['{0} :{1}'.format(target, msg)])

    def notice(self, target, msg):
        """
        Sends a NOTICE to an user or channel.

        :param target: user or channel to send to.
        :type target: str
        :param msg: message to send.
        :type msg: basestring
        """
        self.cmd('NOTICE', ['{0} :{1}'.format(target, msg)])

    def join(self, channel):
        """
        Make the bot join a channel.

        :param channel: new channel to join.
        :type channel: str
        """
        self.cmd('JOIN', channel)

    def set_nick(self, nick):
        """
        Changes the bot's nickname.

        :param nick: new nickname to use
        :type nick: str
        """
        self.cmd('NICK', nick)

    def disconnect(self):
        """
        Disconnects the bot from the server.
        """
        self.cmd('QUIT', [':{0}'.format(self.quit_msg)])

    def run(self):
        """
        Connects the bot and starts the event loop.
        """
        self._connect()
        self._event_loop()


def run_bots(bots):
    """
    Run many bots in parallel.

    :param bots: IRC bots to run.
    :type bots: list
    """
    greenlets = [spawn(bot.run) for bot in bots]
    try:
        joinall(greenlets)
    except KeyboardInterrupt:
        for bot in bots:
            bot.disconnect()
    finally:
        killall(greenlets)
