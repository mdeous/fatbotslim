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
.. module:: fatbotslim.log

.. moduleauthor:: Mathieu D. (MatToufoutu)

This module contains everything useful to enable logging.
"""

import logging

LOG_FORMAT = '%(levelname)s [%(name)s] %(asctime)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


class ColorFormatter(logging.Formatter):
    """
    A logging formatter that displays the loglevel with colors and
    the logger name in bold.
    """
    _colors_map = {
        'DEBUG': '\033[22;32m',
        'INFO': '\033[01;34m',
        'WARNING': '\033[22;35m',
        'ERROR': '\033[22;31m',
        'CRITICAL': '\033[01;31m'
    }

    def format(self, record):
        """
        Overrides the default :func:`logging.Formatter.format` to add colors to
        the :obj:`record`'s :attr:`levelname` and :attr:`name` attributes.
        """
        level_length = len(record.levelname)
        if record.levelname in self._colors_map:
            record.msg = '{0}{1}\033[0;0m'.format(
                self._colors_map[record.levelname],
                record.msg
            )
            record.levelname = '{0}{1}\033[0;0m'.format(
                self._colors_map[record.levelname],
                record.levelname
            )
        record.levelname += ' ' * (8 - level_length)
        record.name = '\033[37m\033[1m{0}\033[0;0m'.format(record.name)
        return super(ColorFormatter, self).format(record)


def create_logger(name, level='INFO'):
    """
    Creates a new ready-to-use logger.

    :param name: new logger's name
    :type name: str
    :param level: default logging level.
    :type level: :class:`str` or :class:`int`
    :return: new logger.
    :rtype: :class:`logging.Logger`
    """
    formatter = ColorFormatter(LOG_FORMAT, DATE_FORMAT)
    if not isinstance(logging.getLevelName(level), int):
        level = 'INFO'
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger
