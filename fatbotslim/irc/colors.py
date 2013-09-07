# -*- coding: utf-8 -*-
#
# This file is part of FatBotSlim.
#
# FatBotSlim is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FatBotSlim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FatBotSlim. If not, see <http://www.gnu.org/licenses/>.
#
"""
.. module:: fatbotslim.irc.colors

.. moduleauthor:: Mathieu D. (MatToufoutu)

This module provides message colors capabilities.
"""


class ColorMessage(object):
    """
    Allows to create colorized strings.
    Created objects behave like real strings, allowing to call `str` methods.
    """
    _colors = {
        'white':        u'\u000300',
        'black':        u'\u000301',
        'dark_blue':    u'\u000302',
        'dark_green':   u'\u000303',
        'red':          u'\u000304',
        'brown':        u'\u000305',
        'purple':       u'\u000306',
        'olive':        u'\u000307',
        'yellow':       u'\u000308',
        'green':        u'\u000309',
        'teal':         u'\u000310',
        'cyan':         u'\u000311',
        'blue':         u'\u000312',
        'magenta':      u'\u000313',
        'dark_grey':    u'\u000314',
        'light_grey':   u'\u000315'
    }
    _bold = u'\u0002'
    _underline = u'\u001f'
    _highlight = u'\u0016'

    def __init__(self, content, color='black', bold=False, underline=False, highlight=False):
        """
        :param content: message to colorize.
        :type content: unicode
        :param color: one of :attr:`fatbotslim.irc.colors.ColorMessage._colors`.
        :type color: str
        :param bold: if the string has to be in bold.
        :type bold: bool
        :param underline: if the string has to be underlined.
        :type underline: bool
        :param highlight: if the string foreground and background has to be switched.
        :type highlight: bool
        """
        self.content = self.colorize(content, color, bold, underline, highlight)
        self.color = color
        self.bold = bold
        self.underline = underline
        self.highlight = highlight

    def __getattr__(self, item):
        if not hasattr(self.content, item):
            if not hasattr(self, item):
                raise AttributeError(
                    "%s object has no %s attribute" % (self.__class__.___name__, item)
                )
            return getattr(self, item)
        return getattr(self.content, item)

    def __str__(self):
        return self.content

    @staticmethod
    def colorize(string, color='black', bold=False, underline=False, highlight=False):
        """
        :param string: message to colorize.
        :type string: unicode
        :param color: one of :attr:`fatbotslim.irc.colors.ColorMessage._colors`.
        :type color: str
        :param bold: if the string has to be in bold.
        :type bold: bool
        :param underline: if the string has to be underlined.
        :type underline: bool
        :param highlight: if the string foreground and background has to be switched.
        :type highlight: bool
        """
        result = ''
        if bold:
            result += ColorMessage._bold
        if underline:
            result += ColorMessage._underline
        if highlight:
            result += ColorMessage._highlight
        result += ColorMessage._colors.get(color, ColorMessage._colors['black'])
        return result+string
