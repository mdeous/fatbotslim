from fatbotslim.cli import make_bot, main
from fatbotslim.handlers import CommandHandler, EVT_PUBLIC

class HelloCommand(CommandHandler):
    triggers = {
        u'hello': [EVT_PUBLIC],
    }

    def hello(self, msg):
        self.irc.msg(msg.dst, u"Hello {0}!".format(msg.src.name))

bot = make_bot()
bot.add_handler(HelloCommand)
main(bot)
