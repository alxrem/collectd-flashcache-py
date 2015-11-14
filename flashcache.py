# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 sw=4 et

import collectd
import os
import os.path
import re
from subprocess import Popen, PIPE, STDOUT


PROC_ROOT = '/proc/flashcache'

DMSETUP_RE = re.compile(
        r'^(.*?): \d+ \d+ flashcache conf:\n'
        r'\s+ssd dev \(.*/(.+?)\), disk dev \(.*/(.+?)\)',
        re.M)
STATS_RE = re.compile(r'(\w+)=(\d+)')


class Config:
    DMSETUP = '/sbin/dmsetup'
    DEVICES = set()
    IGNORE_SELECTED = False
    MAPPINGS = None


def config_callback(conf):
    for node in conf.children:
        if node.key == 'Device':
            Config.DEVICES.add(node.values[0])
        elif node.key == 'DMSetup':
            Config.DMSETUP = node.values[0]
        elif node.key == 'IgnoreSelected':
            Config.IGNORE_SELECTED = node.values[0]
        else:
            log('Ignoring unknown config key "{0}".'.format(node.key))

def init_callback():
    mappings = detect_mappings()

    if not Config.DEVICES:
        Config.MAPPINGS = mappings
        return

    all_devices = set(mappings.keys())

    unknown_devices = Config.DEVICES - all_devices
    for device in unknown_devices:
        log('Unknown flashcache device "{0}".'.format(device, PROC_ROOT))

    if Config.IGNORE_SELECTED:
        devices = all_devices - Config.DEVICES
    else:
        devices = Config.DEVICES - unknown_devices
    Config.MAPPINGS = dict([(device, mappings[device]) for device in devices])

def detect_mappings():
    try:
        p = Popen([Config.DMSETUP, 'table'], stdout=PIPE, stderr=STDOUT)
    except OSError:
        raise Exception("Can't execute {0}.".format(Config.DMSETUP))
    rc = p.wait()
    if rc != 0:
         raise Exception('dmsetup execution error')
    return dict([(dmdev, '{0}+{1}'.format(ssd, disk))
                for dmdev, ssd, disk
                in DMSETUP_RE.findall(p.stdout.read())])

def read_callback():
    for device in Config.MAPPINGS:
        for name in ['flashcache_stats', 'flashcache_errors']:
            stats_file = os.path.join(PROC_ROOT, Config.MAPPINGS[device], name)
            with open(stats_file) as stats:
                dispatch_stats(stats.read(), device)

def dispatch_stats(stats, device):
    for metric, val in STATS_RE.findall(stats):
        value = collectd.Values()
        value.plugin = 'flashcache'
        value.plugin_instance = device
        value.type = 'gauge'
        value.type_instance = metric.replace(' ', '_')
        value.values = [int(val)]
        value.dispatch()

def log(message, level='warning'):
    level_method = getattr(collectd, level)
    level_method('flashcache module: {0}'.format(message))


collectd.register_config(config_callback)
collectd.register_init(init_callback)
collectd.register_read(read_callback)
