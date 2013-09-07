==========================
Writing a multi-server bot
==========================

In this tutorial, we'll take the code from the "simple bot" tutorial, and make it run on multiple
servers.

The code
========

.. literalinclude:: ./multi.py
    :language: python
    :linenos:

Explanations
============

Imports
-------

* Line 1:

    The :class:`fatbotslim.irc.bot.IRC` class will be used to instanciate and configure our bots.
    And the :func:`fatbotslim.irc.bot.run_bots` will allow us to run all our bots in parallel.

Configuration
-------------

* Lines 12-29:

    Instead of having our settings passed via the command line, we create a :obj:`dict` for each server
    our bot will connect to.

Running the bots
----------------

* Lines 31-35:

    Here we create a :obj:`list` to hold our :class:`fatbotslim.irc.bot.IRC` instances. We loop over
    each server configuration, and use them in our bots instanciations.

* Line 37:

    The :func:`fatbotslim.irc.bot.run_bots` function takes a :obj:`list` of bots as argument, and launches
    each one's main loop in a :obj:`greenlet`.
