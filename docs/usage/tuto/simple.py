from fatbotslim.cli import make_bot, main
from fatbotslim.handlers import CommandHandler, EVT_PUBLIC

class HelloCommand(CommandHandler):
    triggers = {
        'hello': [EVT_PUBLIC],
    }

    def hello(self, msg):
        self.irc.msg(msg.dst, "Hello {0}!".format(msg.src.name))

bot = make_bot()
bot.add_handler(HelloCommand)
main(bot)
