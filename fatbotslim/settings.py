# -*- coding: utf-8 -*-
#
#####################################
#                                   #
#  FATBOTSLIM'S CONFIGURATION FILE  #
#                                   #
#####################################


### Global settings ###

plugin_dirs = []


### Servers settings ###
#
# possible values:
# - server_name: an alias for the server (string) [MANDATORY]
# - host: irc server's hostname or ip (string) [MANDATORY]
# - port: port on which the server is listening (integer) [default: 6667, or 6697 if ssl is True]
# - ssl: connect to the server using ssl (boolean) [default: False]
# - nickname: nickname the bot will use on this server (string) [default: fatbotslim]
# - channels: channels to join upon connection (list of strings) [default: empty list]
# - plugins: plugins to activate for this server (list of strings) [default: empty list]
# - version_name: name to use in CTCP VERSION reply message (string) [default: fatbotslim]
# - version_num: version number to use in CTCP VERSION reply message (string) [default: fatbotslim's version]

freenode = {
    'server_name': 'Freenode',
    'host': 'irc.freenode.net',
    'port': 6667,
    'ssl': False,
    'nickname': 'FatBotSlim',
    'channels': ['#testmybot', '#python'],
    'plugins': [],
    'version_name': 'Name used for CTCP VERSION reply message',
    'version_num': 'Version used for CTCP VERSION reply message',
}

rizon = {
    'server_name': 'Rizon',
    'host': 'irc.rizon.net',
    'port': 6697,
    'ssl': True,
    'nickname': 'FatBotSlim',
    'channels': ['#kalk-test'],
    'plugins': [],
}

active_servers = [rizon,]
