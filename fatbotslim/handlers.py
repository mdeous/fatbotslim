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

import platform
from datetime import datetime
from fatbotslim import NAME, VERSION
from fatbotslim.irc.codes import *


class CTCPHandler(object):
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
    def __init__(self):
        self.commands = {
            PING: self.ping,
        }

    def ping(self, msg, irc):
        irc.cmd('PONG', msg.args)


class UnknownCodeHandler(object):
    def __init__(self):
        self.commands = {
            UNKNOWN_CODE: self.unknown_code,
        }

    def unknown_code(self, msg, irc):
        irc.log.info("Received an unknown command: {0}".format(msg.command))
