# -*- coding: utf-8 -*-
#
#   Copyright (c) 2010 MatToufoutu
#
#   This file is part of fatbotslim.
#   fatbotslim is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   fatbotslim is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with fatbotslim.  If not, see <http://www.gnu.org/licenses/>.
#

__all__ = (
    'memoized',
    'UnknownColorError',
    'formatted',
)

#####################################################
# memoize decorator (cache function's return value) #
#####################################################

import functools

class cached(object):
    """
    Memoize decorator that caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned and
    not re-evaluated.
    """
    def __init__(self, func):
        self.func = func
        self.cache = {}
    def __call__(self, *args):
        try:
            return self.cache[args]
        except KeyError:
            value = self.func(*args)
            self.cache[args] = value
            return value
        except TypeError:
            # value is uncachable, for instance, a list
            return self.func(*args)
    def __get__(self, obj, objtype):
        """support instance methods."""
        return functools.partial(self.__call__, obj)

##########################
# text formatting helper #
##########################

CODES = {
        'black': '',
        'bold': '\002',
        'blue': '\0032',
        'orange': '\0034',
        'red': '\0035',
        'green': '\0039',
        'brown': '\0037'
}

class UnknownColorError(Exception):
    def __init__(self, color):
        self.value = "No such color available: %s" % color
    def __str__(self):
        return repr(self.value)

def formatted(string, color='black'):
    if color not in CODES:
        raise UnknownColorError(color)
    string = "%s%s%s" % (CODES[color], string, CODES[color])
    return string
