from fatbotslim.cli import make_bot, main
from fatbotslim.handlers import CommandHandler

class HelloCommand(CommandHandler):
    triggers = {
        'hello': ('public',),
    }

    def hello(self, msg, irc):
        irc.msg(msg.dst, "Hello {0}!".format(msg.src.name))

bot = make_bot()
bot.add_handler(HelloCommand())
main(lambda: bot)
