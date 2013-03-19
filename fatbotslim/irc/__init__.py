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

import chardet


def u(s, errors='ignore'):
    """
    Automatically detects given string's encoding and returns its unicode form.
    Decoding errors are handled according to the `errors` argument, see `unicode()`
    documentation for more details.

    :param s: string to decode.
    :type s: str
    :param errors: decoding error handling behaviour.
    :type errors: str
    :return: decoded string
    :rtype: unicode
    """
    try:
        return s.decode('utf-8', errors=errors)
    except UnicodeDecodeError:
        encoding = chardet.detect(s)['encoding']
        return unicode(s, encoding=encoding, errors=errors)
