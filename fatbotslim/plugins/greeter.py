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


class Greeter(BasePlugin):
    """
    Sample plugin that greets people when they join a channel or send '!hi'
    """
    name = "Greeter"
    description = "A test plugin to show how to code plugins for fatbotslim"
    pubHelp = """
    !hi - Make the bot say hello
    """
    privHelp = """
    no help
    """

    def hi(self, user, destination, message): # message is passed to the function with the trigger stripped from it
        nickname = self.netmaskToNick(user)
        destination = nickname if (destination == self.client.nickname) else destination
        self.client.msg(destination, "Hello %s!" % nickname)

    @trigger('!hi', hi) # register a function to call when the 'message' argument starts with '!hi'
    def on_pubmsg(self, user, destination, message): # define callbacks to handle various events
        pass

    @trigger('!hi', hi)
    def on_privmsg(self, user, destination, message):
        pass

    def on_userJoined(self, user, channel):
        # code to execute each time the event happens
        nickname = self.netmaskToNick(user)
        self.client.msg(channel, "Hello %s!" % nickname)
