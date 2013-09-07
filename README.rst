|Flattr this repo|

FatBotSlim
----------

Yet another Python IRC bot library...

Features:
~~~~~~~~~

-  asynchronous
-  multi-server
-  easy to use plugin system
-  automated help messages generation for custom plugins
-  colored logging
-  colored IRC messages
-  command line parser to set your custom bot settings from the console

Dependencies:
~~~~~~~~~~~~~

-  gevent
-  chardet

Documentation:
~~~~~~~~~~~~~~

The documentation is hosted on `readthedocs <http://readthedocs.org>`__
and is available in the following formats:

-  `HTML (online) <http:/fatbotslim.rtfd.org>`__
-  `HTML (downloadable
   .zip) <https://media.readthedocs.org/htmlzip/fatbotslim/latest/fatbotslim.zip>`__
-  `PDF <https://media.readthedocs.org/pdf/fatbotslim/latest/fatbotslim.pdf>`__
-  `Epub <https://media.readthedocs.org/epub/fatbotslim/latest/fatbotslim.epub>`__
-  `Manpage <https://media.readthedocs.org/man/fatbotslim/latest/fatbotslim.1>`__

Example:
~~~~~~~~

This very simple bot answers ``Hello <username>!`` when someone says
``!hello`` in a public message.

Using the ``fatbotslim.cli`` helpers also gives your bot an integrated
command line arguments parser.

For more detailed informations about writing custom handlers and more
complex bots, please refer to the
`documentation <http://fatbotslim.rtfd.org>`__.

.. code:: python

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

*Just try it!*

.. |Flattr this repo| image:: http://api.flattr.com/button/flattr-badge-large.png
   :target: https://flattr.com/submit/auto?user_id=mattoufoutu&url=https://github.com/mattoufoutu/fatbotslim&title=fatbotslim&language=&tags=github&category=software
