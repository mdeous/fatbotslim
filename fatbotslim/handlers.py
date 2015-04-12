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
from collections import defaultdict

from fatbotslim import NAME, VERSION, URL
from fatbotslim.irc.codes import *
from fatbotslim.log import create_logger

EVT_PUBLIC = 'public'
EVT_PRIVATE = 'private'
EVT_NOTICE = 'notice'

log = create_logger(__name__)


class HandlerError(Exception):
    pass


class BaseHandler(object):
    """
    The base of every handler.

    A handler should at least have a :attr:`commands` attribute of type :class:`dict`
    which maps IRC codes (as defined in :mod:`fatbotslim.irc.codes`) to methods.

    Mapped methods take 1 argument, the :class:`fatbotslim.irc.bot.Message` object
    that triggered the event.
    """
    commands = {}

    def __init__(self, irc):
        self.irc = irc
        for _, method_name in self.commands.iteritems():
            method = getattr(self, method_name)
            if not callable(method):
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
            u'VERSION', msg.src.name,
            u'{0}:{1}:{2}'.format(NAME, VERSION, platform.system())
        )

    def source(self, msg):
        self.irc.ctcp_reply(
            u'SOURCE', msg.src.name,
            URL
        )
        self.irc.ctcp_reply(u'SOURCE', msg.src.name)

    def time(self, msg):
        now = datetime.now().strftime(u'%a %b %d %I:%M:%S%p %Y %Z').strip()
        self.irc.ctcp_reply(u'TIME', msg.src.name, now)

    def ping(self, msg):
        self.irc.ctcp_reply(u'PING', msg.src.name, ' '.join(msg.args))


class PingHandler(BaseHandler):
    """
    Answers to PINGs sent by the server. (enabled by default)
    """
    commands = {
        PING: 'ping'
    }

    def ping(self, msg):
        self.irc.cmd(u'PONG', u' '.join(msg.args))


class UnknownCodeHandler(BaseHandler):
    """
    Logs messages for which the IRC code is unknown. (enabled by default)
    """
    commands = {
        UNKNOWN_CODE: 'unknown_code'
    }

    def unknown_code(self, msg):
        log.info("Received an unknown command: {0}".format(msg.command))


class CommandHandler(BaseHandler):
    """
    The CommandHandler is a special kind of handler that eases the creation of
    bots that react to prefixed commands (like ``!command``). It only reacts to
    PRIVMSG and NOTICE messages.

    The prefix character is defined by the handler's :attr:`trigger_char` attribute,
    and defaults to ``!``.

    Commands are defined in the handler's :attr:`triggers` attribute, a dict that
    maps method names to events to which they should react. Possible events
    are :obj:`EVT_PUBLIC`, :obj:`EVT_PRIVATE`, and :obj:`EVT_NOTICE`.
    The methods should take 1 argument, which is the :class:`fatbotslim.irc.bot.Message`
    object  that triggered the event.

    For example, the message ``!foo bar`` would call the handler's :func:`foo` method.

    Here is a command handler that says hello when it receives ``!hello`` in public::

        class HelloCommand(CommandHandler):
            triggers = {
                'hello': [EVT_PUBLIC],
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

    def __init__(self, irc):
        super(CommandHandler, self).__init__(irc)
        for trigger, events in self.triggers.iteritems():
            method = getattr(self, trigger)
            if not callable(method):
                raise HandlerError(
                    '%s has no method named %s' % (
                        self.__class__.__name__, trigger
                    )
                )
            for event in events:
                if event not in (EVT_PUBLIC, EVT_PRIVATE, EVT_NOTICE):
                    raise HandlerError('Unknown event type: %s' % event)

    def _dispatch_trigger(self, msg):
        """
        Dispatches the message to the corresponding method.
        """
        if not msg.args[0].startswith(self.trigger_char):
            return
        split_args = msg.args[0].split()
        trigger = split_args[0].lstrip(self.trigger_char)
        if trigger in self.triggers:
            method = getattr(self, trigger)
            if msg.command == PRIVMSG:
                if msg.dst == self.irc.nick:
                    if EVT_PRIVATE in self.triggers[trigger]:
                        msg.event = EVT_PRIVATE
                        method(msg)
                else:
                    if EVT_PUBLIC in self.triggers[trigger]:
                        msg.event = EVT_PUBLIC
                        method(msg)
            elif (msg.command == NOTICE) and (EVT_NOTICE in self.triggers[trigger]):
                msg.event = EVT_NOTICE
                method(msg)


class HelpHandler(CommandHandler):
    """
    Provides automatic help messages for :class:`fatbotslim.handlers.CommandHandler` commands.
    """
    triggers = {
        'help': [EVT_PUBLIC, EVT_PRIVATE, EVT_NOTICE]
    }

    def help(self, msg):
        """
        help [command] - displays available commands, or help message for given command
        """
        commands = {}
        for handler in self.irc.handlers:
            if isinstance(handler, CommandHandler):
                for command in handler.triggers:
                    method = getattr(handler, command)
                    if hasattr(method, '__doc__') and method.__doc__:
                        commands[command] = method.__doc__.strip()
                    else:
                        commands[command] = 'No help available for command: %s' % command

        if len(msg.args) == 2:
            if msg.args[1] not in commands:
                message = 'Unknown command: %s' % msg.args[1]
            else:
                message = commands[msg.args[1]]
        else:
            message = 'Available commands: %s' % ', '.join(commands.keys())

        if msg.event == EVT_PUBLIC:
            self.irc.msg(msg.dst, message)
        elif msg.event == EVT_PRIVATE:
            self.irc.msg(msg.src, message)
        elif msg.event == EVT_NOTICE:
            self.irc.notice(msg.src, message)


class RightsHandler(CommandHandler):
    """
    Provides rights management for :class:`fatbotslim.handlers.CommandHandler` commands.
    """
    notify = True
    commands_rights = defaultdict(dict)

    def set_restriction(self, command, user, event_types):
        """
        Adds restriction for given `command`.

        :param command: command on which the restriction should be set.
        :type command: str
        :param user: username for which the restriction applies.
        :type user: str
        :param event_types: types of events for which the command is allowed.
        :type event_types: list
        """
        self.commands_rights[command][user.lower()] = event_types
        if command not in self.triggers:
            self.triggers[command] = [EVT_PUBLIC, EVT_PRIVATE, EVT_NOTICE]
        if not hasattr(self, command):
            setattr(self, command, lambda msg: self.handle_rights(msg))

    def del_restriction(self, command, user, event_types):
        """
        Removes restriction for given `command`.

        :param command: command on which the restriction should be removed.
        :type command: str
        :param user: username for which restriction should be removed.
        :type user: str
        :param event_types: types of events that should be removed from restriction.
        :type event_types: list
        """
        if user.lower() in self.commands_rights[command]:
            for event_type in event_types:
                try:
                    self.commands_rights[command][user.lower()].remove(event_type)
                except ValueError:
                    pass
            if not self.commands_rights[command][user.lower()]:
                self.commands_rights[command].pop(user.lower())

    def handle_rights(self, msg):
        """
        Catch-all command that is called whenever a restricted command is triggered.

        :param msg: message that triggered the command.
        :type msg: :class:`fatbotslim.irc.Message`
        """
        command = msg.args[0][1:]
        if command in self.commands_rights:
            if msg.src.name.lower() in self.commands_rights[command]:
                if msg.event not in self.commands_rights[command][msg.src.name.lower()]:
                    msg.propagate = False
            elif '*' in self.commands_rights[command]:
                if msg.event not in self.commands_rights[command]['*']:
                    msg.propagate = False
            if (not msg.propagate) and self.notify:
                message = "You're not allowed to use the '%s' command" % command
                if msg.event == EVT_PUBLIC:
                    self.irc.msg(msg.dst, message)
                elif msg.event == EVT_PRIVATE:
                    self.irc.msg(msg.src.name, message)
                elif msg.event == EVT_NOTICE:
                    self.irc.notice(msg.src.name, message)
