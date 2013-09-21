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

Available colors are:

* blue
* brown
* dark_green
* magenta
* purple
* dark_grey
* light_grey
* yellow
* black
* teal
* cyan
* olive
* green
* white
* dark_blue
* red

If no color is specified when instanciating :class:`fatbotslim.irc.colors.ColorMessage`, the value
defaults to "black".

Rights Management
=================

`FatBotSlim` provides a built-in handler (:class:`fatbotslim.handlers.RightsHandler`) to manage
who should be allowed to run specific commands. It allows to define which users can run which
commands, and on which event(s) type(s).

This special handler is automatically enabled, and is accessible through the
:attr:`fatbotslim.irc.bot.IRC.rights` attribute. It can be permanently disabled using the
:meth:`fatbotslim.irc.bot.IRC.enable_rights` method, and can be re-enabled using the
:meth:`fatbotslim.irc.bot.IRC.disable_rights` method.

Settings permissions
--------------------

Adding a new permission is done using the :meth:`fatbotslim.irc.bot.IRC.rights.set_restriction`
method.

For example, to restrict usage of the `hello` command to a user named `LeetUser` in public messages,
the following code should be used (assuming `bot` is the :class:`fatbotslim.irc.bot.IRC` instance::

    bot.rights.set_permission('hello', 'LeetUser', [EVT_PUBLIC])

Once this is done, only `LeetUser` will be allowed to use the `hello` command, and only in public
messages.

Global rights can also be set using `*` as the username. In the following example, `LeetUser` would
be allowed to use the `hello` command in private messages only, and all the other users would be
allowed to use it in public messages and notices only. ::

    bot.rights.set_restriction('hello', 'LeetUser', [EVT_PRIVATE])
    bot.rights.set_restriction('hello', '*', [EVT_PUBLIC, EVT_NOTICE])

Removing permissions
--------------------

Removing a permission is done using the :meth:`fatbotslim.irc.bot.IRC.rights.del_restriction`
method.

The following code snippet would remove the previously set permission for `LeetUser`. ::

    bot.rights.del_restriction('hello', 'LeetUser', [EVT_PRIVATE])

Only given event(s) type(s) are removed from the permission, so, if `LeetUser` was previously
allowed to use the `hello` command in public messages too, it would still have the right to.
