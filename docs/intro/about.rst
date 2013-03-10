================
About FatBotSlim
================

:Author: Mathieu D. (MatToufoutu)
:Contact: mattoufootu[at]gmail.com
:Homepage: https://github.com/mattoufoutu/fatbotslim
:Documentation: http://fatbotslim.rtfd.org
:Issue tracker: https://github.com/mattoufoutu/fatbotslim/issues
:Git clone URI: https://github.com/mattoufoutu/fatbotslim.git

FatBotSlim is an asynchronous IRC bot library written in Python using the
``gevent`` library.

A FatBotSlim bot consists of a bot object to which handlers are registered to
make it react to events. When triggered, the handlers' methods are called
asynchronously, therefore you don't have to worry about time-consuming operations
that could block your code execution.
