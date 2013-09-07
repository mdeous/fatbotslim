#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
from setuptools import setup, find_packages
from fatbotslim import NAME, VERSION, AUTHOR, URL

CURRENT_DIR = os.path.dirname(__file__)

setup(
    name=NAME,
    version=VERSION,
    description='Yet another IRC bot library',
    long_description=open(os.path.join(CURRENT_DIR, 'README.rst')).read().strip(),
    author=AUTHOR,
    author_email='mattoufootu@gmail.com',
    url=URL,
    license='GPL',
    keywords='irc ircbot bot',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python :: 2.7',
        'Topic :: Communications :: Chat :: Internet Relay Chat',
        'Topic :: Internet',
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=open(os.path.join(CURRENT_DIR, 'requirements.txt')).read().strip(),
)
