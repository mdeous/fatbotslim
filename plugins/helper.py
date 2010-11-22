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

from plugins import BasePlugin, trigger


class Helper(BasePlugin):
    """Generate usage messages for loaded plugins"""
    name = 'Helper'
    description = "Generate help messages for the loaded plugins"
    header = "##### COMMANDS #####\n"

    def showPubHelp(self, user, channel, message):
        print message
        plugins = [p for p in self.client.pman.plugins if (p.pubHelp is not None)]
        if len(plugins) != 0:
            self.client.msg(channel, self.header + '\n'.join(p.pubHelp.strip() for p in plugins))

    def showPrivHelp(self, user, destination, message):
        plugins = [p for p in self.client.pman.plugins if (p.privHelp is not None)]
        if len(plugins) != 0:
            self.client.msg(self.netmaskToNick(user), self.header + '\n'.join(p.privHelp.strip() for p in plugins))

    def showNoticeHelp(self, user, message):
        plugins = [p for p in self.client.pman.plugins if (p.noticeHelp is not None)]
        if len(plugins) != 0:
            self.client.msg(self.netmaskToNick(user), self.header + '\n'.join(p.noticeHelp.strip() for p in plugins))

    @trigger('!help', showPubHelp)
    def on_pubmsg(self, user, channel, message):
        pass

    @trigger('!help', showPrivHelp)
    def on_privmsg(self, user, destination, message):
        pass

    @trigger('!help', showNoticeHelp)
    def on_noticed(self, user, channel, message):
        pass
