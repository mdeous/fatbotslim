# -*- coding: utf-8 -*-
#
#   Copyright (c) 2010 MatToufoutu
#
#   This file is part of fatbotslim.
#   fatbotslim is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   fatbotslim is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with fatbotslim.  If not, see <http://www.gnu.org/licenses/>.
#

import sys
import re
from collections import defaultdict
from functools import wraps
from inspect import getargspec
from include.utils import cached

try:
    set
except NameError:
    from sets import Set as set


class PluginError(Exception):
    pass

class UnsupportedEventError(PluginError):
    def __init__(self, event):
        self.value = "Can't register trigger: '%s' (supported events: 'privmsg', 'pubmsg', 'noticed')" % event

    def __str__(self):
        return repr(self.value)


class BasePlugin(object):
    """
    Basic plugin class.
    constructor:
        @param client (object): IRC client to which the plugin is linked
    """
    name = None
    description = None
    pubHelp = None
    privHelp = None
    noticeHelp = None

    @property
    @cached
    def callbacks(self):
        """get a list of events supported by the plugin.
        @return list"""
        return [re.sub('^on_', '', method) for method in dir(self) if method.startswith('on_')]

    def netmaskToHost(self, nm):
        """convert a netmask to a host.
        @return str"""
        return nm.split('@')[-1]

    def netmaskToNick(self, nm):
        """convert a netmask to a nickname
        @return str"""
        return nm.split('!')[0]


class Manager(object):
    """
    Plugin manager to load plugins and handle events.
    constructor:
        @param client (object): IRC client to which the manager is linked
        @param path (str): path to the directory where plugins are located
        @param plugins (list): name of the plugins to load
    """
    def __init__(self, client, path, plugins):
        self.callbacks = defaultdict(list)
        self.plugins = []
        if not path in sys.path:
            sys.path.insert(0, path)
        self._loadPlugins(client, plugins)

    def _loadPlugins(self, client, plugins):
        """import and instanciate plugins.
        @param client (object): IRC client to which the plugins will be linked
        @param plugins (list): name of the plugins to load
        """
        for plugin in plugins:
            __import__(plugin, globals(), locals())
        for plugin in BasePlugin.__subclasses__():
            if True in [(getattr(plugin, attr) is None) for attr in ('name', 'description')]:
                print("[%s] %s will not be loaded (plugins must have both a 'name' and a 'description' attribute)" % \
                      (client.factory.config.server, str(plugin).split("'")[1]))
                continue
#            plugin = plugin(client)
            plugin = plugin()
            plugin.client = client
            self.plugins.append(plugin)
            for event in plugin.callbacks:
                callback = getattr(plugin, 'on_%s' % event)
                self.register(plugin, event, callback)

    def register(self, plugin, event, callback):
        """link an event to a callback
        @param plugin (object): plugin for which the event is being registered.
        @param event (str): event name
        @param callback (func): function to call when event is triggered
        """
        #TODO: check if event exists
        if not hasattr(plugin.client, event):
            raise UnsupportedEventError(event)
        if not callback in self.callbacks[event]:
            self.callbacks[event].append(callback)

    def emit(self, event, *args, **kwargs):
        """call all the callbacks linked to emitted event.
        @param event (str): event name
        @param args (list): arguments list to pass to the callback
        @param kwargs (dict): named arguments list to pass to the callback
        """
        #TODO: use twisted defered system for events callbacks
        for callback in self.callbacks[event]:
            callback(*args, **kwargs)


class trigger(object):
    def __init__(self, trigger, callback):
        self.trigger = trigger
        self.callback = callback

    def __call__(self, func):
        event = re.sub('^on_', '', func.func_name)
        if event not in ('privmsg', 'pubmsg', 'noticed'):
            raise UnsupportedEventError(event)
        @wraps(func)
        def wrapped(obj, *args, **kwargs):
            args = list(args)
            argnames = getargspec(func)[0]
            if 'self' in argnames:
                argnames.remove('self')
            msg = args[argnames.index('message')]
            if msg.startswith(self.trigger):
                #TODO: use twisted defered system for triggers callbacks
                args[args.index(msg)] = re.sub('^%s ?' % self.trigger, '', msg)
                self.callback(obj, *args, **kwargs)
            return func(obj, *args, **kwargs)
        return wrapped
