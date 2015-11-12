#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 sw=4 et

import collectd
import os
import os.path
import re
from subprocess import Popen, PIPE, STDOUT

PROC_ROOT = '/proc/flashcache'

class Config:
    DMSETUP = '/sbin/dmsetup'

def config_callback(conf):
    devices = set()
    ignore_selected = False

    for node in conf.children:
        if node.key == 'Device':
            devices.add(node.values[0])
        elif node.key == 'DMSetup':
            Config.DMSETUP = node.values[0]
        elif node.key == 'IgnoreSelected':
            value = node.values[0].lower()
            if value in ['true', 'yes', '1']:
                ignore_selected = True
            elif value in ['false', 'no', '0']:
                ignore_selected = False
            else:
                log('{0} is wrong value of IgnoreSelected'.format(value),
                    'warning')
        else:
            log('Unknown confiuration key {0}'.format(node.key))

    all_devices = set([entry
                       for entry in os.listdir(PROC_ROOT)
                       if os.path.isdir(os.path.join(PROC_ROOT, entry))])

    if devices:
        if ignore_selected:
            Config.DEVICES = all_devices - devices
        else:
            Config.DEVICES = all_devices & devices

        unknown_devices = devices - all_devices
        for device in unknown_devices:
            log('Unknown flashcache device {0}. '
                    'Examine {1}.'.format(device, PROC_ROOT), 'warning')
    else:
        Config.DEVICES = all_devices

    Config.DM_DEVICES = detect_dm_devices()

def detect_dm_devices():
    try:
        p = Popen([Config.DMSETUP, 'table'], stdout=PIPE, stderr=STDOUT)
    except OSError:
        raise Exception("Can't execute {0}".format(Config.DMSETUP))
    rc = p.wait()
    if rc != 0:
         raise Exception('dmsetup execution error')
    return dict([('{0}+{1}'.format(ssd, disk), dmdev)
                 for dmdev, ssd, disk
                 in re.findall(
                     r'^(.*?): \d+ \d+ flashcache conf:\n'
                     r'\s+ssd dev \(.*?/(\w+)\), disk dev \(.*?/(\w+)\)',
                     p.stdout.read(), re.M)])

def read_callback():
    for device in Config.DEVICES:
        for name in ['flashcache_stats', 'flashcache_errors']:
            with open(os.path.join(PROC_ROOT, device, name)) as stats:
                dispatch_stats(stats.read(), device)

def dispatch_stats(stats, device):
    for metric, value in (match.groups()
                          for match
                          in re.finditer(r'(\w+)=(\d+)', stats)):
        dispatch_value(Config.DM_DEVICES[device], metric, value)

def dispatch_value(device, metric, val):
    value = collectd.Values()
    value.plugin = 'flashcache'
    value.plugin_instance = device
    value.type = 'gauge'
    value.type_instance = metric.replace(' ', '_')
    value.values = [int(val)]
    value.dispatch()

def log(message, level='error'):
    level_method = getattr(collectd, level)
    level_method('flashcache plugin: ' + message)

collectd.register_config(config_callback)
collectd.register_read(read_callback)
