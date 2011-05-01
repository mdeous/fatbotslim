# -*- coding: utf-8 -*-
#
#    Copyright (c) 2010 MatToufoutu
#
#    This file is part of fatbotslim.
#    fatbotslim is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#TODO: implement commands: oper, mode, topic, names, list, invite
#TODO:     ''        ''  : kick, who, whois, whowas, kill, away
#TODO:     ''        ''  : rehash, restart, wallops,

import logging
import platform
from asynchat import async_chat
from datetime import datetime
from re import compile as re_compile
from socket import AF_INET, SOCK_STREAM

from core.servercodes import *
from core import NAME, VERSION, AUTHOR

LOGFORMAT = '[%(name)s] %(levelname)s - %(message)s'
CTCP_RE = re_compile(r'^\x01(?P<type>[A-Z]+)(?: (?P<data>.+))?\x01$')


class IRCClient(async_chat):
    """
    Asynchronous IRC protocol implementation.
    """
    terminator = '\r\n'
    ctcp_version = None

    def __init__(self, host, port, nickname, username,
                 channels=None,
                 loglevel=logging.INFO,
                 logformat=LOGFORMAT):
        async_chat.__init__(self)
        logging.basicConfig(format=logformat)
        self.host = host
        self.port = port
        self.nickname = nickname
        self.username = username
        self.channels = [] if (channels is None) else channels
        self.received_data = ''
        self.logger = logging.getLogger('%(host)s:%(port)d' % {'host': host, 'port': port})
        self.logger.setLevel(loglevel)
        self.logger.info('connecting to host...')
        self.create_socket(AF_INET, SOCK_STREAM)
        self.connect((host, port))

    @classmethod
    def split_netmask(cls, netmask):
        """extracts the nickname, username and hostname from a netmask.
        @param netmask (str): the netmask to split
        @return tuple"""
        nick = netmask.split('!')[0].lstrip(':')
        user = netmask.split('@')[0].split('!')[1]
        host = netmask.split('@')[1]
        return nick, user, host

    @classmethod
    def netmask_to_nick(cls, netmask):
        return IRCClient.split_netmask(netmask)[0]

    @classmethod
    def netmask_to_user(cls, netmask):
        return IRCClient.split_netmask(netmask)[1]

    @classmethod
    def netmask_to_host(cls, netmask):
        return IRCClient.split_netmask(netmask)[2]

    def _connection_made(self):
        """joins configured channels once connection is complete."""
        self.logger.info('connection successful')
        for channel in self.channels:
            self.send_data('JOIN %(chan)s' % {'chan': channel})
        self.on_connection()

    def send_data(self, data):
        """sends data through the socket.
        @param data (str): the data to send"""
        self.logger.debug('SENT DATA: %(data)s' % {'data': repr(data)})
        data += '\r\n'
        self.push(data)

    def handle_connect(self):
        """authenticates to the server after a successful connection."""
        self.send_data('NICK :%(nick)s' % {'nick': self.nickname})
        self.send_data('USER %(nick)s %(nick)s %(nick)s :%(user)s' % {
            'nick': self.nickname,
            'user': self.username,
        })

    def handle_data(self, data):
        """dispatches received data to the various callbacks.
        @param data (str): received data"""
        self.logger.debug(str(data))
        token = data.split()
        src = token[0]

        if PRIVMSG in token:
            dst = token[2]
            message = ' '.join(token[3:]).lstrip(':')
            ctcp = CTCP_RE.match(message)
            if ctcp is not None:
                ctcp = ctcp.groupdict()
                self.on_ctcp(src, dst, ctcp)
                return
            self.on_privmsg(src, dst, message)

        elif NOTICE in token:
            dst = token[2]
            message = ' '.join(token[3:]).lstrip(':')
            self.on_notice(src, dst, message)

        elif JOIN in token:
            dst = token[2]
            self.on_join(src, dst)

        elif PART in token:
            dst = token[2]
            message = ' '.join(token[3:]).lstrip(':') if (len(token) > 2) else None
            self.on_part(src, dst, message)

        elif PING in token:
            self.on_ping(token[1])

        elif RPL_ENDOFMOTD in token:
            self._connection_made()

        else:
            self.on_unknown_data(data)

    def found_terminator(self):
        """sends buffered data to ``IRCClient.handle_data`` on line terminator."""
        self.handle_data(self.received_data)
        self.received_data = ''

    def collect_incoming_data(self, data):
        """adds received data to the buffer.
        @param data (str): received data"""
        self.received_data += data

    ##########################
    ## IRC COMMANDS METHODS ##
    ##########################

    def set_nick(self, new_nick):
        """change client nickname (NICK).
        @param new_nick (str): the new nickname"""
        self.nickname = new_nick
        self.send_data('NICK %(nick)s' % {'nick': new_nick})

    def privmsg(self, dst, msg, color=None):
        """sends a private/public message (PRIVMSG).
        @param dst (str): message destination
        @param msg (str): message content
        @param color (str): color to use for the message text (default: None)
        """
        self.send_data('PRIVMSG %(dst)s :%(msg)s' % {
            'dst': dst,
            'msg': msg,
        })

    def notice(self, dst, msg):
        """sends a notice message (NOTICE)."""
        self.send_data('NOTICE %(dst)s :%(msg)s' % {
            'dst': dst,
            'msg': msg,
        })

    def join(self, dst):
        """joins a channel (JOIN).
        """
        self.send_data('JOIN %(dst)s' % {'dst': dst})

    def part(self, dst, msg=None):
        data = 'PART %(dst)s' % {'dst': dst}
        if msg is not None:
            data += ' :%(msg)s' % {'msg': msg}
        self.send_data(data)

    def quit(self, msg=None):
        data = 'QUIT'
        if msg is not None:
            data += ' :%(msg)s' % {'msg': msg}
        self.send_data(data)

    def on_ping(self, ping_id):
        self.send_data('PONG %(id)s' % {'id': ping_id})

    def on_ctcp(self, src, dst, ctcp):
        if (ctcp['type'] == 'PING') and (ctcp['data'] is not None):
            self.on_ctcp_ping(src, ctcp)
        elif ctcp['type'] == 'TIME':
            self.on_ctcp_time(src)
        elif ctcp['type'] == 'VERSION':
            self.on_ctcp_version(src)
        elif ctcp['type'] == 'FINGER':
            self.on_ctcp_finger(src)
        elif ctcp['type'] == 'ACTION':
            self.on_action(src, dst, ctcp['data'])

    ############################################
    ## EVENTS HANDLERS TO USE IN A SUBCLASSES ##
    ############################################

    def on_unknown_data(self, data):
        pass

    def on_connection(self):
        pass

    def on_ctcp_ping(self, src, ctcp):
        nick, _, _ = self.split_netmask(src)
        self.notice(nick, '\x01PING %(timestamp)s\x01' % {'timestamp': ctcp['data']})

    def on_ctcp_time(self, src):
        nick, _, _ = self.split_netmask(src)
        message = '%s UTC' % datetime.utcnow()
        self.notice(nick, '\x01TIME :%(time)s\x01' % {'time': message})

    def on_ctcp_version(self, src):
        nick, _, _ = self.split_netmask(src)
        sysinfo = 'Python %(version)s (%(py_imp)s) on %(os)s' % {
            'version': platform.python_version(),
            'py_imp': platform.python_implementation(),
            'os': platform.system(),
            }
        message = '\x01VERSION %(name)s:%(version)s:%(system)s\x01' % {
            'name': NAME,
            'version': VERSION,
            'system': sysinfo,
        }
        self.notice(nick, message)

    def on_ctcp_finger(self, src):
        pass

    def on_action(self, src, dst, msg):
        pass

    def on_privmsg(self, src, dst, msg):
        pass

    def on_notice(self, src, dst, msg):
        pass

    def on_join(self, src, dst):
        pass

    def on_part(self, src, dst, msg):
        pass

    def on_quit(self, src, msg):
        pass

if __name__ == '__main__':
    from asyncore import loop
    host, port = 'rafale.org', 6667
    nick = username = 'fatbotslim'
    channels = ['#testbot']
    loglevel = logging.DEBUG
    client = IRCClient(host, port, nick, username, channels, loglevel)
    loop()
