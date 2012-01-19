====================
Writing a simple bot
====================

In this tutorial, we'll take the code from the README.md and explain what happens,
it is a bot that answers `Hello <username>!` when someone says `!hello` in a public
message.

The code
========

.. literalinclude:: ./simple.py
   :language: python
   :linenos:

Explanations
============

Imports:
--------

* Line 1:

    We import 2 functions, :func:`fatbotslim.cli.make_bot` and
    :func:`fatbotslim.cli.main`, both are useful when dealing with a bot
    that will connect to only one server.

    The :func:`fatbotslim.cli.make_bot` function takes care of gathering the
    command line options, which are used to create a :class:`fatbotslim.irc.IRC`
    instance, and then returns it.

    The :func:`fatbotslim.cli.main` function is there to spawn the bot in a
    greenlet (see gevent's `documentation`_ for details about this) and run
    the main loop for you.

* Line 2:

    Here we import the :class:`fatbotslim.handlers.CommandHandler` that will be used
    to make the bot react to the `!hello` command.

The handler:
------------

* Lines 5-7:

    The :attr:`triggers` attribute is a :class:`dict` used to define to which commands
    and on which  type of events the bot should react. It consists of command names mapped
    to a tuple listing events. If we wanted the bot to react to `!hello` both in public
    and private messages, the value would have been `('public', 'private')`.

* Lines 9-10:

    This is the method that will be called when the `!hello` command will be triggered, it
    must have the same name as defined in :attr:`triggers` and takes two arguments,
    the first is the instance of the :class:`fatbotslim.irc.bot.Message` that triggered the
    command, and the second is an instance of :class:`fatbotslim.irc.bot.IRC` which is used
    to communicate back with the server.

Starting the bot:
-----------------

* Line 12:

    Nothing to explain here, the :func:`fatbotslim.cli.make_bot` function is already
    described in the imports part.

* Line 13:

    The previously created handler is instanciated and added to the bot's handlers.

* Line 14:

    The bot is launched in a greenlet, and the main loop is started.

.. _documentation: http://www.gevent.org/gevent.html#greenlet-objects
