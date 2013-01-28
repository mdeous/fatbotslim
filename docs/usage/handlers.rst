========================
Creating custom handlers
========================

Basic handlers
==============

Basic handlers simply react to IRC events by calling methods mapped to them, they are
subclasses of :class:`fatbotslim.handlers.BaseHandler`.

Events are mapped to methods names in the handler's :attr:`commands` attribute, which
is a :class:`dict` where the key is an IRC event as defined in the :mod:`fatbotslim.irc.codes`
module and the value is the name of the method to call. The mapped methods take just one
attribute, the :class:`fatbotslim.irc.bot.Message` object which triggered the event.
To communicate back to the server,  use the handler's :attr:`irc` (which is a
:class:`fatbotslim.bot.IRC` instance).

A good example of a custom handler is FatBotSlim's integrated :class:`fatbotslim.handlers.CTCPHandler`::

    class CTCPHandler(BaseHandler):
        """
        Reacts to CTCP events (VERSION,SOURCE,TIME,PING). (enabled by default)
        """
        commands = {
            CTCP_VERSION: 'version',
            CTCP_SOURCE: 'source',
            CTCP_TIME: 'time',
            CTCP_PING: 'ping'
        }

        def version(self, msg):
            self.irc.ctcp_reply(
                'VERSION', msg.src.name,
                '{0}:{1}:{2}'.format(NAME, VERSION, platform.system())
            )

        def source(self, msg):
            self.irc.ctcp_reply(
                'SOURCE', msg.src.name,
                'https://github.com/mattoufoutu/fatbotslim'
            )
            self.irc.ctcp_reply('SOURCE', msg.src.name)

        def time(self, msg):
            now = datetime.now().strftime('%a %b %d %I:%M:%S%p %Y %Z').strip()
            self.irc.ctcp_reply('TIME', msg.src.name, now)

        def ping(self, msg):
            self.irc.ctcp_reply('PING', msg.src.name, msg.args[0])

Another, simpler, basic handler is the integrated :class:`fatbotslim.handlers.PingHandler`,
this one simply answers to server's PINGs::

    class PingHandler(BaseHandler):
        """
        Answers to PINGs sent by the server. (enabled by default)
        """
        commands = {
            PING: 'ping'
        }

        def ping(self, msg):
            self.irc.cmd('PONG', msg.args[0])

Command handlers
================

The :class:`fatbotslim.handlers.CommandHandler` is a special kind of handler that
reacts only to ``PRIVMSG`` and ``NOTICE`` messages, they are used to implement
``!foo``-like commands to your bot.

The prefix character is defined by the handler's :attr:`trigger_char` attribute,
and defaults to ``!``.

Commands are defined in the handler's :attr:`triggers` attribute, a dict that
maps method names to events they should react to. Possible events are :attr:`EVT_PUBLIC`,
:attr:`EVT_PRIVATE`, and :attr:`EVT_NOTICE`. The methods take just 1 argument,
the first is a :class:`fatbotslim.irc.bot.Message` object, and the second is a
:class:`fatbotslim.irc.bot.IRC` object used to send messages back to the server.

For example, the message ``!foo bar`` would call the handler's :func:`foo` method.

Here is a command handler that says hello when it receives ``!hello`` in public::

    from fatbotslim.handlers import CommandHandler, EVT_PUBLIC

    class HelloCommand(CommandHandler):
        triggers = {
            'hello': [EVT_PUBLIC],
        }

        def hello(self, msg):
            self.irc.msg(msg.dst, "Hello, {0}!".format(msg.src.name))

If you wanted the handler to answer also to private messages, you would simply have
to add 'private' to the "hello" event list and set the answer destination accordingly::

    from fatbotslim.handlers import CommandHandler, EVT_PUBLIC, EVT_PRIVATE

    class HelloCommand(CommandHandler):
        triggers = {
            'hello': [EVT_PUBLIC, EVT_PRIVATE],
        }

        def hello(self, msg):
            dst = msg.src.name if (msg.dst == irc.nick) else msg.dst
            self.irc.msg(dst, "Hello {0}!".format(msg.src.name))
