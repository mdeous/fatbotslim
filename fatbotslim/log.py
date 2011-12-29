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

import logging


def create_logger(name):
    formatter = logging.Formatter(
        '%(asctime)s [%(name)s] %(levelname)s - %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger
