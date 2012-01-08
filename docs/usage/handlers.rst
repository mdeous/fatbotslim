========================
Creating custom handlers
========================

Basic handlers
==============

Basic handlers react to IRC events by calling the method mapped to it and are
subclasses of :class:`fatbotslim.handlers.BaseHandler`.

Methods are mapped to events in the handler's :attr:`commands` attribute, which
is a :class:`dict` where keys are IRC events as defined in the :mod:`fatbotslim.irc.codes`
module. They should take 2 arguments, the :class:`fatbotslim.irc.bot.Message` object
which triggered the event, and a :class:`fatbotslim.irc.bot.IRC` object which can be
used to send messages back to the server.

A good example of a custom handler is FatBotSlim's integrated :class:`fatbotslim.handlers.CTCPHandler`::

    class CTCPHandler(BaseHandler):
        """
        Reacts to CTCP events (VERSION,SOURCE,TIME,PING). (enabled by default)
        """
        def __init__(self):
            self.commands = {
                CTCP_VERSION: self.version,
                CTCP_SOURCE: self.source,
                CTCP_TIME: self.time,
                CTCP_PING: self.ping,
            }

        def version(self, msg, irc):
            irc.ctcp_reply('VERSION', msg.src.name, '{0}:{1}:{2}'.format(
                NAME, VERSION, platform.system()
            ))

        def source(self, msg, irc):
            irc.ctcp_reply('SOURCE', msg.src.name,
                           'https://github.com/mattoufoutu/fatbotslim')
            irc.ctcp_reply('SOURCE', msg.src.name)

        def time(self, msg, irc):
            now = datetime.now().strftime('%a %b %d %I:%M:%S%p %Y %Z').strip()
            irc.ctcp_reply('TIME', msg.src.name, now)

        def ping(self, msg, irc):
            irc.ctcp_reply('PING', msg.src.name, msg.args[0])

Command handlers
================

The :class:`fatbotslim.handlers.CommandHandler` is a special kind of handler that
reacts only to ``PRIVMSG`` and ``NOTICE`` messages, they are used to implement
``!foo``-like commands to your bot.

The prefix character is defined by the handler's :attr:`trigger_char` attribute,
and defaults to ``!``.

Commands are defined in the handler's :attr:`triggers` attribute, a dict that
maps method names to events to which they should react. Possible events
are ``public``, ``private``, and ``notice``. The methods should take 2 arguments,
the first is a :class:`fatbotslim.irc.bot.Message` object, and the second is a
:class:`fatbotslim.irc.bot.IRC` object used to send messages back to the server.

For example, the message ``!foo bar`` would call the handler's :func:`foo` method.

Here is a command handler that says hello when it receives ``!hello`` in public::

    class HelloCommand(CommandHandler):
        triggers = {
            'hello': ('public',),
        }

        def hello(self, msg, irc):
            irc.msg(msg.dst, "Hello, {0}!".format(msg.src.name))

If you wanted the handler to answer also to private messages, you would simply have
to add 'private' to the "hello" event list and set the answer destination accordingly::

    class HelloCommand(CommandHandler):
        triggers = {
            'hello': ('public', 'private'),
        }

        def hello(self, msg, irc):
            dst = msg.src.name if (msg.dst == irc.nick) else msg.dst
            irc.msg(dst, "Hello {0}!".format(msg.src.name))
