#!/usr/bin/env python
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
This is a sample script to demonstrate how to create an IRC bot
using FatBotSlim.
"""

from fatbotslim.cli import make_bot, main
from fatbotslim.handlers import CommandHandler, EVT_PUBLIC


class HelloCommand(CommandHandler):
    """
    A sample command handler that makes the bot answer "Hello <user>!"
    when someone uses the "!hello" command (only in public messages).
    """
    triggers = {
        'hello': [EVT_PUBLIC],
    }

    def hello(self, msg):
        self.irc.msg(msg.dst, "Hello {0}!".format(msg.src.name))


bot = make_bot()  # create a bot instance
bot.add_handler(HelloCommand)  # register as many handlers as needed
main(bot)  # start the bot
