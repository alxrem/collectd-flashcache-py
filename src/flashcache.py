#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 sw=4 et

import collectd
import re
from subprocess import Popen, PIPE


class Config:
    DMSETUP = '/sbin/dmsetup'
    DEVICES = None

def config_callback(conf):
    for node in conf.children:
        if node.key.lower() == 'dmsetup':
            Config.DMSETUP = node.values[0]
        elif node.key.lower() == 'devices':
            Config.DEVICES = node.values
        else:
            log('Unknown config key: %s.' % node.key, 'warning')

def read_callback():
    cmd = [Config.DMSETUP, 'status', Config.DEVICES[0]]
    try:
        p = Popen(cmd, stdout=PIPE)
    except Exception, e:
        log('Popen failed: {0}'.format(e))
        return

    rc = p.wait()
    if rc != 0:
         log('dmsetup execution error')
         return

    try:
        output = p.stdout.read()
    except Exception, e:
        log("Can't read dmsetup output: {0}".format(e))
        return

    for metric, value in (match.groups()
                          for match
                          in re.finditer(r'(?:,?\s+(.*?)\((\d+)\))', output)):
        dispatch_value(metric, value)

def dispatch_value(metric, val):
    value = collectd.Values()
    value.plugin = 'flashcache'
    value.plugin_instance = 'cachedev'
    value.type = 'gauge'
    value.type_instance = metric.replace(' ', '_')
    value.values = [int(val)]
    value.dispatch()

def log(message, level='error'):
    level_method = getattr(collectd, level)
    level_method('flashcache plugin: ' + message)

collectd.register_config(config_callback)
collectd.register_read(read_callback)
