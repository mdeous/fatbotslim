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

Handlers should at least have a `commands` attribute of type `dict` which
maps IRC codes (as defined in :module:`fatbotslim.irc.codes`) to methods.
Mapped methods take 2 arguments, the :class:`fatbotslim.irc.Message` object
that triggered the event, and a :class:`fatbotslim.irc.IRC` instance, which
should be used to send messages back to the server/user.
"""

import platform
from datetime import datetime
from fatbotslim import NAME, VERSION
from fatbotslim.irc.codes import *


class CTCPHandler(object):
    """
    Reacts to CTCP events (VERSION,SOURCE,TIME,PING).
    """
    def __init__(self):
        self.commands = {
            CTCP_VERSION: self.version,
            CTCP_SOURCE: self.source,
            CTCP_TIME: self.time,
            CTCP_PING: self.ping,
        }

    def version(self, msg, irc):
        irc.ctcp_reply('VERSION', msg.src.name, '{0}:{1}:{2}'.format(
            NAME, VERSION, platform.system()
        ))

    def source(self, msg, irc):
        irc.ctcp_reply('SOURCE', msg.src.name,
                       'https://github.com/mattoufoutu/fatbotslim')
        irc.ctcp_reply('SOURCE', msg.src.name)

    def time(self, msg, irc):
        now = datetime.now().strftime('%a %b %d %I:%M:%S%p %Y %Z').strip()
        irc.ctcp_reply('TIME', msg.src.name, now)

    def ping(self, msg, irc):
        irc.ctcp_reply('PING', msg.src.name, msg.args[0])


class PingHandler(object):
    """
    Answers to PINGs sent by the server.
    """
    def __init__(self):
        self.commands = {
            PING: self.ping,
        }

    def ping(self, msg, irc):
        irc.cmd('PONG', msg.args)


class UnknownCodeHandler(object):
    """
    Logs messages for which the IRC code is unknown.
    """
    def __init__(self):
        self.commands = {
            UNKNOWN_CODE: self.unknown_code,
        }

    def unknown_code(self, msg, irc):
        irc.log.info("Received an unknown command: {0}".format(msg.command))


class CommandHandler(object):
    """
    The base for handlers that reacts on PRIVMSG and NOTICE commands
    if the message starts with a pre-defined character (default: '!')
    and dispatches the message to a method with the same name as the command.

    Triggers and event types for which the method should be called must be
    defined in the subclasse's `triggers` attribute. `triggers` is a dict
    mapping method names to a tuple containing one or more event types.
    An event type can be 'private', 'public', or 'notice'.

    For example, the message "!foo bar" would call the `foo` method.
    This class does nothing by itself and is meant to be overriden.

    A command handler that says hello when it receives "!hello" in public:

        class HelloCommand(CommandHandler):
            triggers = {
                'hello': ('public',),
            }
            def hello(self, msg, irc):
                irc.msg(msg.dst, "Hello, {0}!".format(msg.src.name))

    """
    trigger_char = '!'
    triggers = {}

    def __init__(self):
        self.commands = {
            PRIVMSG: self._dispatch,
            NOTICE: self._dispatch
        }

    def _dispatch(self, msg, irc):
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
                    if msg.dst == irc.nick:
                        if 'private' in self.triggers[trigger]:
                            method(msg, irc)
                    else:
                        if 'public' in self.triggers[trigger]:
                            method(msg, irc)
                        pass
                elif (msg.command == NOTICE) and ('notice' in self.triggers[trigger]):
                    if 'notice' in self.triggers[trigger]:
                        method(msg, irc)
