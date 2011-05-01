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

try:
    set()
except NameError:
    from sets import Set as set
from core import NAME, VERSION
from core.configobj import ConfigObj


class ConfigError(Exception):
    """Base class for errors occuring while reading the configuration file."""
    pass


class MissingConfigOption(ConfigError):
    """
    An option is missing in the configuration file.
    constructor:
        @param server (str): server name for which the error occurs
        @param option (str): name of the missing option
    """
    def __init__(self, server, option):
        self.value = '%s: missing option in config file: %s' % (server, option)
    def __str__(self):
        return repr(self.value)


class ConfigTypeError(ConfigError):
    """
    An option has not the expected type.
    contructor:
        @param server (str): server name for which the error occurs
        @param option (str): name of the "mis-typed" option
        @param given (type): given option's type
        @param expected (type): the type the option should be
    """
    def __init__(self, server, option, given, expected):
        self.value = "%s: wrong value type for option '%s': %s (expected: %s)" % (server, option, given, expected)
    def __str__(self):
        return repr(self.value)


class ConfigSlots(type):
    """
    Metaclass used to automagically create a __slots__ attribute to
    a Config object according to the rules and passed attributes.
    """
    def __new__(cls, name, bases, attrs):
        slots = attrs.get('__slots__', set())
        for attr in attrs['rules']:
            slots.add(attr)
        attrs['__slots__'] = tuple(slots)
        return type.__new__(cls, name, bases, attrs)


class Config(object):
    """
    Object containing options for a given server.
    constructor:
        @param server (str): server name for which the config is
    """
    __metaclass__ = ConfigSlots
    rules = {
        'server': {'mandatory': True, 'type': basestring},
        'host': {'mandatory': True, 'type': basestring},
        'nickname': {'mandatory': True, 'type': basestring},
        'channels': {'mandatory': True, 'type': list},
        'srv_pass': {'mandatory': False, 'type': basestring, 'default': ''},
        'port': {'mandatory': False, 'type': int, 'obj_getter': 'as_int', 'default': 6667},
        'ssl': {'mandatory': False, 'type': bool, 'obj_getter': 'as_bool', 'default': False},
        'plugins': {'mandatory': False, 'type': list, 'default': []},
        'versionName': {'mandatory': False, 'type': basestring, 'default': NAME},
        'versionNum': {'mandatory': False, 'type': basestring, 'default': VERSION},
    }
    def __init__(self, server):
        self.server = server

    def check(self):
        """check mandatory attributes, types, and apply default values if needed."""
        for opt, rule in self.rules.items():
            if rule['mandatory']:
                if not hasattr(self, opt):
                    raise MissingConfigOption(self.server, opt)
            else:
                if not hasattr(self, opt):
                    setattr(self, opt, rule['default'])
            if not isinstance(getattr(self, opt), rule['type']):
                raise ConfigTypeError(self.server, opt, str(type(opt)).split("'")[1], str(rule['type']).split("'")[1])


def readConfig(config_file):
    """read a config file and create a Config object for each section.
    @param config_file (str): path to the configuration file to read
    @return configs (list): list containing created Config objects"""
    configs = []
    co = ConfigObj(config_file)
    for section in co.keys():
        srv = co[section]
        cfg = Config(section)
        for opt in cfg.rules:
            if srv.has_key(opt):
                if cfg.rules[opt].has_key('obj_getter'):
                    value = getattr(srv, cfg.rules[opt]['obj_getter'])(opt)
                else:
                    value = srv[opt]
                setattr(cfg, opt, value)
        cfg.check()
        configs.append(cfg)
    return configs
