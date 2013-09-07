from fatbotslim.irc.bot import IRC, run_bots
from fatbotslim.handlers import CommandHandler, EVT_PUBLIC

class HelloCommand(CommandHandler):
    triggers = {
        u'hello': [EVT_PUBLIC],
    }

    def hello(self, msg):
        self.irc.msg(msg.dst, u"Hello {0}!".format(msg.src.name))

servers = [
    {
        'server': 'irc.rizon.net',
        'port': 6697,
        'ssl': True,
        'nick': 'fatbotslim',
        'realname': 'fatbotslim',
        'channels': ['#testbot']
    },
    {
        'server': 'irc.freenode.net',
        'port': 6697,
        'ssl': True,
        'nick': 'fatbotslim',
        'realname': 'fatbotslim',
        'channels': ['#testbot']
    }
]

bots = []
for server in servers:
    bot = IRC(server)
    bot.add_handler(HelloCommand)
    bots.append(bot)

run_bots(bots)
