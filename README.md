## FatBotSlim

Just another Python IRC bot library...

### Features:

- asynchronous
- multi-server
- easy to use plugin system
- colored logging
- command line parser to set your custom bot settings from the console

### Dependencies:

- gevent

## Example

This very simple bot answers `Hello <username>!` when someone says `!hello` in a
public message.

Using the `fatbotslim.cli` helpers also gives your bot an integrated command line
arguments parser.

For more detailed informations about writing custom handlers and more complex bots,
please refer to the [documentation](http://fatbotslim.rtfd.org).

```python
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
main(bot)
```

*Just try it!*
