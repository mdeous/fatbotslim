#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   This file is part of fatbotslim.
#
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

from multiprocessing import Process

from twisted.internet import reactor, ssl

from core.config import getConfigs
from core.ircbot import IrcBotFactory

__app__ = 'fatbotslim'
__version__ = '0.1'
__author__ = 'MatToufoutu'


class BotLauncher(object):
    """
    Launch multiple clients in separated processes.
    """
    def __init__(self):
        self.factories = list()
        self.processes = list()

    def addBot(self, cfg):
        """add a client to the list of bots to start.
        @param cfg (object): client's configuration"""
        factory = IrcBotFactory(cfg)
        self.factories.append(factory)

    def startBot(self, factory):
        """start a client.
        @param factory (object): factory to use to create the client"""
        if factory.config.ssl:
            try:
                import OpenSSL
                reactor.connectSSL(factory.config.host, factory.config.port, factory, ssl.ClientContextFactory())
            except ImportError:
                print("[%s] Can not connect using SSL, pyopenssl not found")
                return
        else:
            reactor.connectTCP(factory.config.host, factory.config.port, factory)
        reactor.run()

    def startAll(self):
        """start all registered clients."""
        for factory in self.factories:
            p = Process(target=self.startBot, args=(factory,))
            p.start()
            self.processes.append(p)


def main():
    """main function"""
    launcher = BotLauncher()
    for config in getConfigs('fatbotslim.conf'):
        launcher.addBot(config)
    launcher.startAll()

if __name__ == '__main__':
    main()
