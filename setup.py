#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 sw=4 et

from distutils.core import setup

setup(name='collectd_flashcache',
      version='0.1.0',
      description='flashcache plugin for CollectD',
      author='Alexey Remizov',
      author_email='alexey@remizov.org',
      url='https://github.com/alxrem/collectd-flashcache-py',
      py_modules=['collectd_flashcache'],
      license='GPLv3+',
      keywords='collectd plugin flashcache',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Plugins',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: System :: Networking :: Monitoring',
          'Topic :: System :: Systems Administration',
      ]
     )
