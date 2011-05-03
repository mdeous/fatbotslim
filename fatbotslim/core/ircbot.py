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

from os import path, getcwd
from platform import system

from twisted.internet import defer, reactor
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.words.protocols.irc import IRCClient

from plugins import Manager


class IrcBot(IRCClient):
    """
    IRC bot core class.
    """
    versionEnv = system()

    def initPlugins(self):
        pluginsPath = path.join(getcwd(), 'plugins/')
        self.pman = Manager(self, pluginsPath, self.factory.config.plugins)

    def pingSelf(self):
        """prevents timeouts on some servers."""
        self.ping(self.nickname)
        self.pingSelfId = reactor.callLater(180, self.pingSelf)

    def connectionMade(self):
        """the connection has been successfully initiated."""

        self.nickname = self.factory.config.nickname
        self.password = self.factory.config.srv_pass if self.factory.config.srv_pass else None
        self.versionName = self.factory.config.versionName
        self.versionNum = self.factory.config.versionNum
        self.realname = self.versionName
        self.username = self.versionName
        self.userinfo = "%s v%s" % (self.versionName, self.versionNum)
        self.pingSelfId = None
        self.initPlugins()
        IRCClient.connectionMade(self)

    def msg(self, destination, message, length=400):
        """IRCClient.msg re-implementation to split messages in 400bytes parts by default."""
        IRCClient.msg(self, destination, message, length)

    def say(self, channel, message, length=400):
        """IRCClient.say re-implementation to split messages in 400bytes parts by default"""
        IRCClient.say(self, channel, message, length)

    ### EVENTS CALLBACKS ###

    def signedOn(self):
        """called after a successful connection."""
        print('[%s] Connection successful' % self.factory.config.server_name)
        self.pingSelfId = reactor.callLater(180, self.pingSelf)
        for chan in self.factory.config.channels:
            self.join(chan)
        self.pman.emit('signedOn')

    def privmsg(self, user, destination, message):
        if self.pingSelfId is not None:
            self.pingSelfId.reset(180)
        if destination != self.nickname:
            self.pubmsg(user, destination, message)
        else:
            self.pman.emit('privmsg', user, destination, message)

    def pubmsg(self, user, destination, message):
        self.pman.emit('pubmsg', user, destination, message)

    def joined(self, channel):
        self.pman.emit('joined', channel)

    def left(self, channel):
        self.pman.emit('left', channel)

    def noticed(self, user, channel, message):
        self.pman.emit('noticed', user, channel, message)

    def modeChanged(self, user, channel, set, modes, args):
        self.pman.emit('modeChanged', user, channel, set, modes, args)

    def kickedFrom(self, channel, kicker, message):
        self.pman.emit('kickedFrom', channel, kicker, message)

    def nickChanged(self, nick):
        self.pman.emit('nickChanged', nick)

    def userJoined(self, user, channel):
        self.pman.emit('userJoined', user, channel)

    def userLeft(self, user, channel):
        self.pman.emit('userLeft', user, channel)

    def userQuit(self, user, quitMessage):
        self.pman.emit('userQuit', user, quitMessage)

    def userKicked(self, kickee, channel, kicker, message):
        self.pman.emit('userKicked', kickee, channel, kicker, message)

    def action(self, user, channel, data):
        self.pman.emit('action', user, channel, data)

    def topicUpdated(self, user, channel, newTopic):
        self.pman.emit('topicUpdated', user, channel, newTopic)

    def userRenamed(self, oldname, newname):
        self.pman.emit('userRenamed', oldname, newname)

    def receivedMOTD(self, motd):
        self.pman.emit('receivedMOTD', motd)


class IrcBotFactory(ReconnectingClientFactory):
    """
    Factory class to create auto-reconnecting IRC clients.
    """
    protocol = IrcBot
    def __init__(self, cfg):
        self.config = cfg

    def clientConnectionLost(self, connector, reason):
        print('[%s] Lost connection, reconnecting...' % self.config.server_name)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print('[%s] Could not connect: %s' % (self.config.server_name, reason.value))
