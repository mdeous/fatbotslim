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
from random import choice

from gevent import spawn, joinall, killall
from gevent.pool import Group

from fatbotslim.irc import u
from fatbotslim.irc.codes import *
from fatbotslim.irc.tcp import TCP, SSL
from fatbotslim.handlers import CTCPHandler, PingHandler, UnknownCodeHandler
from fatbotslim.log import create_logger

ctcp_re = re.compile(ur'\x01(.*?)\x01')


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
        :type data: unicode
        """
        self._raw = data
        self.erroneous = False
        try:
            self.src, self.dst, self.command, self.args = Message.parse(data)
        except IndexError:
            self.src, self.dst, self.command, self.args = [None] * 4
            self.erroneous = True

    def __str__(self):
        return u"<Message(src='{0}', dst='{1}', command='{2}', args={3})>".format(
            self.src.name, self.dst, self.command, self.args
        )

    @classmethod
    def parse(cls, data):
        """
        Extracts message informations from `data`.

        :param data: received line.
        :type data: unicode
        :return: extracted informations (source, destination, command, args).
        :rtype: tuple(Source, str, str, list)
        :raise: :class:`fatbotslim.irc.NullMessage` if `data` is empty.
        """
        src = u''
        dst = None
        if data[0] == u':':
            src, data = data[1:].split(u' ', 1)
        if u' :' in data:
            data, trailing = data.split(u' :', 1)
            args = data.split()
            args.extend(trailing.split())
        else:
            args = data.split()
        command = args.pop(0)
        if command in (PRIVMSG, NOTICE):
            dst = args.pop(0)
            if ctcp_re.match(args[0]):
                args = args[0].strip(u'\x01').split()
                command = u'CTCP_' + args.pop(0)
        return Source(src), dst, command, args


class Source(object):
    """
    Holds informations about a message sender.

    """

    def __init__(self, prefix):
        """
        :param prefix: prefix with format ``<servername>|<nick>['!'<user>]['@'<host>]``.
        :type prefix: unicode
        """
        self._raw = prefix
        self.name, self.mode, self.user, self.host = Source.parse(prefix)

    def __str__(self):
        return u"<Source(nick='{0}', mode='{1}', user='{2}', host='{3}')>".format(
            self.name, self.mode, self.user, self.host
        )

    @classmethod
    def parse(cls, prefix):
        """
        Extracts informations from `prefix`.

        :param prefix: prefix with format ``<servername>|<nick>['!'<user>]['@'<host>]``.
        :type prefix: unicode
        :return: extracted informations (nickname or host, mode, username, host).
        :rtype: tuple(str, str, str, str)
        """
        try:
            nick, rest = prefix.split(u'!')
        except ValueError:
            return prefix, None, None, None
        try:
            mode, rest = rest.split(u'=')
        except ValueError:
            mode, rest = None, rest
        try:
            user, host = rest.split(u'@')
        except ValueError:
            return nick, mode, rest, None
        return nick, mode, user, host


class IRC(object):
    """
    The main IRC bot class.
    """
    quit_msg = u"I'll be back!"
    default_handlers = {
        CTCPHandler,
        PingHandler,
        UnknownCodeHandler,
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
        self.channels = map(u, settings['channels'])
        self.nick = u(settings['nick'])
        self.realname = u(settings['realname'])
        self.handlers = set()
        self.log = create_logger(__name__, level=settings.get('loglevel', 'INFO'))
        self._pool = Group()
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
        self.cmd(u'USER', u'{0} 3 * {1}'.format(self.nick, self.realname))

    def _send(self, command):
        """
        Sends a raw line to the server.

        :param command: line to send.
        :type command: unicode
        """
        command = command.encode('utf-8')
        self.log.debug('>> ' + command)
        self.conn.oqueue.put(command)

    def _event_loop(self):
        """
        The main event loop.
        Data from the server is parsed here using :func:`_parse_msg`.
        Parsed events are put in the object's event queue (`self.events`).
        """
        while True:
            orig_line = self.conn.iqueue.get()
            self.log.debug('<< ' + orig_line)
            line = u(orig_line, errors='replace').strip()
            err_msg = False
            try:
                message = Message(line)
            except ValueError:
                err_msg = True
            if err_msg or message.erroneous:
                self.log.error("Received a line that can't be parsed: \"%s\"" % orig_line)
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
        for handler in self.handlers:
            for command in handler.commands:
                if command == msg.command:
                    method = getattr(handler, handler.commands[command])
                    self._pool.spawn(method, msg)

    @classmethod
    def randomize_nick(cls, base, suffix_length=3):
        """
        Generates a pseudo-random nickname.

        :param base: prefix to use for the generated nickname.
        :type base: unicode
        :param suffix_length: amount of digits to append to `base`
        :type suffix_length: int
        :return: generated nickname.
        :rtype: unicode
        """
        suffix = u''.join(choice(u'0123456789') for _ in range(suffix_length))
        return u'{0}{1}'.format(base, suffix)

    def add_handler(self, handler, args=None, kwargs=None):
        """
        Registers a new handler.

        :param handler: handler to register.
        :type handler: :class:``fatbotslim.handlers.BaseHandler`
        :param args: positional arguments to pass to the handler's constructor.
        :type args: list
        :param kwargs: keyword arguments to pass to the handler's constructor.
        :type kwargs: dict
        """
        args = [] if args is None else args
        kwargs = {} if kwargs is None else kwargs
        self.handlers.add(handler(self, *args, **kwargs))

    def cmd(self, command, args, prefix=None):
        """
        Sends a command to the server.

        :param command: IRC code to send.
        :type command: unicode
        :param args: arguments to pass with the command.
        :type args: basestring
        :param prefix: optional prefix to prepend to the command.
        :type prefix: str or None
        """
        if prefix is None:
            prefix = u''
        raw_cmd = u'{0} {1} {2}'.format(prefix, command, args).strip()
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
            raw_cmd = u'\x01{0}\x01'.format(command)
        else:
            raw_cmd = u'\x01{0} {1}\x01'.format(command, message)
        self.notice(dst, raw_cmd)

    def msg(self, target, msg):
        """
        Sends a message to an user or channel.

        :param target: user or channel to send to.
        :type target: str
        :param msg: message to send.
        :type msg: str
        """
        self.cmd(u'PRIVMSG', u'{0} :{1}'.format(target, msg))

    def notice(self, target, msg):
        """
        Sends a NOTICE to an user or channel.

        :param target: user or channel to send to.
        :type target: str
        :param msg: message to send.
        :type msg: basestring
        """
        self.cmd(u'NOTICE', u'{0} :{1}'.format(target, msg))

    def join(self, channel):
        """
        Make the bot join a channel.

        :param channel: new channel to join.
        :type channel: str
        """
        self.cmd(u'JOIN', channel)

    def set_nick(self, nick):
        """
        Changes the bot's nickname.

        :param nick: new nickname to use
        :type nick: unicode
        """
        self.cmd(u'NICK', nick)

    def disconnect(self):
        """
        Disconnects the bot from the server.
        """
        self.cmd(u'QUIT', u':{0}'.format(self.quit_msg))

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
