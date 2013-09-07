=========
Utilities
=========

Commands Help
=============

If you want to have help messages for your handlers' commands automatically generated,
`fatbotslim` provides a convenience handler.

The :class:`fatbotslim.handlers.HelpHandler` provides two kind of help messages, one that simply
lists available commands when `!help` is called (assuming `!` is your current `trigger_char`),
and one that displays the command's docstring when `help [command]` is called.

To use this feature, simply document your commands' docstrings (try to keep a consistent format
across all your docstrings), and add the handler to your bot. ::

    from fatbotslim.cli import make_bot, main
    from fatbotslim.handlers import CommandHandler, HelpHandler, EVT_PUBLIC

    class HelloCommand(CommandHandler):
        triggers = {
            u'hello': [EVT_PUBLIC],
        }

        def hello(self, msg):
            """hello - says hello"""
            self.irc.msg(msg.dst, u"Hello {0}!".format(msg.src.name))

        def say(self, msg):
            """say <message> - simply repeats the message"""
            self.irc.msg(msg.dst, ' '.join(msg.args[1:]))

    bot = make_bot()
    bot.add_handler(HelpHandler)
    bot.add_handler(HelloCommand)
    main(bot)

Given the previous code, if one called `!help`, the bot would answer::

    Available commands: hello, say

and if one called `!help say`, the bot would answer::

    say <message> - simply repeats the message

Colored Messages
================

To send colored messages, you can use the :class:`fatbotslim.irc.colors.ColorMessage` class. It
mimics strings behaviour, and thus allows to call string methods on it. ::

    from fatbotslim.irc.colors import ColorMessage
    message = ColorMessage('sOmE rAnDoM tExT', color='blue')
    message = ColorMessage('sOmE rAnDoM tExT', color='blue', bold=True)
    message = ColorMessage('sOmE rAnDoM tExT', color='blue', underline=True)
    message = ColorMessage('sOmE rAnDoM tExT', color='blue', highlight=True)
    upper_message = message.upper()
    title_message = message.title()

