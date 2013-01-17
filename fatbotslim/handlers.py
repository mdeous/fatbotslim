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
.. module:: fatbotslim.handlers

.. moduleauthor:: Mathieu D. (MatToufoutu)

This module contains a collection of handlers to react to basic IRC events
and allow creation of custom handlers.
"""

import platform
from datetime import datetime
from fatbotslim import NAME, VERSION
from fatbotslim.irc.codes import *


class HandlerError(Exception):
    pass


class BaseHandler(object):
    """
    The base of every handler.

    A handler should at least have a :attr:`commands` attribute of type :class:`dict`
    which maps IRC codes (as defined in :mod:`fatbotslim.irc.codes`) to methods.

    Mapped methods take 2 arguments, the :class:`fatbotslim.irc.bot.Message` object
    that triggered the event, and a :class:`fatbotslim.irc.bot.IRC` instance, which
    can be used to send messages back to the server.
    """
    commands = {}

    def __init__(self, irc):
        self.irc = irc
        for _, method_name in self.commands:
            if not hasattr(self, method_name):
                raise HandlerError(
                    '%s has no method named %s' % (
                        self.__class__.__name__, method_name
                    )
                )

    def _dispatch_command(self, msg):
        method = getattr(self, self.commands[msg.command])
        method(msg)


class CTCPHandler(BaseHandler):
    """
    Reacts to CTCP events (VERSION,SOURCE,TIME,PING). (enabled by default)
    """
    commands = {
        CTCP_VERSION: 'version',
        CTCP_SOURCE: 'source',
        CTCP_TIME: 'time',
        CTCP_PING: 'ping'
    }

    def version(self, msg):
        self.irc.ctcp_reply(
            'VERSION', msg.src.name,
            '{0}:{1}:{2}'.format(NAME, VERSION, platform.system())
        )

    def source(self, msg):
        self.irc.ctcp_reply(
            'SOURCE', msg.src.name,
            'https://github.com/mattoufoutu/fatbotslim'
        )
        self.irc.ctcp_reply('SOURCE', msg.src.name)

    def time(self, msg):
        now = datetime.now().strftime('%a %b %d %I:%M:%S%p %Y %Z').strip()
        self.irc.ctcp_reply('TIME', msg.src.name, now)

    def ping(self, msg):
        self.irc.ctcp_reply('PING', msg.src.name, msg.args[0])


class PingHandler(BaseHandler):
    """
    Answers to PINGs sent by the server. (enabled by default)
    """
    commands = {
        PING: 'ping'
    }

    def ping(self, msg):
        self.irc.cmd('PONG', msg.args)


class UnknownCodeHandler(BaseHandler):
    """
    Logs messages for which the IRC code is unknown. (enabled by default)
    """
    commands = {
        UNKNOWN_CODE: 'unknown_code'
    }

    def unknown_code(self, msg):
        self.irc.log.info("Received an unknown command: {0}".format(msg.command))


class CommandHandler(BaseHandler):
    """
    The CommandHandler is a special kind of handler that eases the creation of
    bots that react to prefixed commands (like ``!command``). It only reacts to
    PRIVMSG and NOTICE messages.

    The prefix character is defined by the handler's :attr:`trigger_char` attribute,
    and defaults to ``!``.

    Commands are defined in the handler's :attr:`triggers` attribute, a dict that
    maps method names to events to which they should react. Possible events
    are ``public``, ``private``, and ``notice``. The methods should take 2 arguments,
    the first is a :class:`fatbotslim.irc.bot.Message` object, and the second is a
    :class:`fatbotslim.irc.bot.IRC` object used to send messages back to the server.

    For example, the message ``!foo bar`` would call the handler's :func:`foo` method.

    Here is a command handler that says hello when it receives ``!hello`` in public::

        class HelloCommand(CommandHandler):
            triggers = {
                'hello': ('public',),
            }
            def hello(self, msg):
                self.irc.msg(msg.dst, "Hello, {0}!".format(msg.src.name))

    """
    commands = {
        PRIVMSG: '_dispatch_trigger',
        NOTICE: '_dispatch_trigger'
    }
    trigger_char = '!'
    triggers = {}

    def _dispatch_trigger(self, msg):
        """
        Dispatches the message to the corresponding method.
        """
        if not msg.args[0].startswith(self.trigger_char):
            return
        split_args = msg.args[0].split()
        trigger = split_args[0].lstrip(self.trigger_char)
        msg.args = split_args[1:]
        if hasattr(self, trigger):
            method = getattr(self, trigger)
            # check if the method is present and registered in the triggers
            if callable(method) and (trigger in self.triggers):
                if msg.command == PRIVMSG:
                    if msg.dst == self.irc.nick:
                        if 'private' in self.triggers[trigger]:
                            method(msg)
                    else:
                        if 'public' in self.triggers[trigger]:
                            method(msg)
                        pass
                elif (msg.command == NOTICE) and ('notice' in self.triggers[trigger]):
                    if 'notice' in self.triggers[trigger]:
                        method(msg)
