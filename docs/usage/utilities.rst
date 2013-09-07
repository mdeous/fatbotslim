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
across all your docstrings), and add the handler to your bot::

    bot.add_handler(HelpHandler)
