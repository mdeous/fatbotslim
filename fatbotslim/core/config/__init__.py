# -*- coding: utf-8 -*-
#
#   Copyright (c) 2011 MatToufoutu
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

import config as settings
from core import NAME, VERSION
from core.config.configobj import ConfigObj


CONFIG_RULES = {
    'server_alias': {
        'mandatory': True,
        'type': basestring,
    },
    'host': {
        'mandatory': True,
        'type': basestring,
    },
    'nickname': {
        'mandatory': False,
        'type': basestring,
        'default': 'fatbotslim',
    },
    'channels': {
        'mandatory': False,
        'type': list,
        'default': list(),
    },
    'srv_pass': {
        'mandatory': False,
        'type': basestring,
        'default': '',
    },
    'port': {
        'mandatory': False,
        'type': int,
        'default': 6667,
    },
    'ssl': {
        'mandatory': False,
        'type': bool,
        'default': False,
    },
    'plugins': {
        'mandatory': False,
        'type': list,
        'default': [],
    },
    'versionName': {
        'mandatory': False,
        'type': basestring,
        'default': NAME,
    },
    'versionNum': {
        'mandatory': False,
        'type': basestring,
        'default': VERSION,
    },
}


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


class ConfigObject(object):
    """
    Object containing options for a given server.
    constructor:
        @param server (str): server name for which the config is
    """
    def __init__(self, config_dict):
        if not 'server_name' in config_dict:
            raise MissingConfigOption('Unknown Server', 'server_name')
        for opt, rule in CONFIG_RULES.iteritems():
            if rule['mandatory']:
                if not opt in config_dict:
                    raise MissingConfigOption(config_dict.get('server_name'), opt)
                setattr(self, opt, config_dict.get(opt))
            else:
                setattr(self, opt, config_dict.get(opt, rule.get('default')))
            if not isinstance(getattr(self, opt), rule.get('type')):
                raise ConfigTypeError(
                    self.server_name,
                    opt,
                    opt.__class__.__name__,
                    rule.get('type').__class__.__name__,
                )
