# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 sw=4 et

import collectd
import os
import os.path
import re
from subprocess import Popen, PIPE, STDOUT


PROC_ROOT = '/proc/flashcache'
"""Where to search for flashcache module statistics."""

DMSETUP_RE = re.compile(
    r'^(.*?): \d+ \d+ flashcache conf:\n'
    r'\s+ssd dev \(.*/(.+?)\), disk dev \(.*/(.+?)\)',
    re.M)
"""Regexp to parse output of `dmsetup table`."""

STATS_RE = re.compile(r'(\w+)=(\d+)')
"""Regexp to parse statistics from /proc/flashcache."""


CONFIG = {
    'DMSETUP': '/sbin/dmsetup',
    'DEVICES': set(),
    'IGNORE_SELECTED': False,
    'MAPPINGS': None
}


def config_callback(conf):
    """Configure module.

    Fill dictionary CONFIG with values of configurational directives

    - Device
    - UgnoreSelected
    - DMSetup
    """
    for node in conf.children:
        if node.key == 'Device':
            CONFIG['DEVICES'].add(node.values[0])
        elif node.key == 'DMSetup':
            CONFIG['DMSETUP'] = node.values[0]
        elif node.key == 'IgnoreSelected':
            CONFIG['IGNORE_SELECTED'] = node.values[0]
        else:
            log('Ignoring unknown config key "{0}".'.format(node.key))


def init_callback():
    """Initialize module.

    According to configuration determine the devices for which
    statistics should be collected. Initialize dictionary
    ``CONFIG['MAPPINGS']`` by items of dictionary returned by
    ``detect_mappings()``
    """
    mappings = detect_mappings()

    if not CONFIG['DEVICES']:
        CONFIG['MAPPINGS'] = mappings
        return

    all_devices = set(mappings.keys())

    unknown_devices = CONFIG['DEVICES'] - all_devices
    for device in unknown_devices:
        log('Unknown flashcache device "{0}".'.format(device))

    if CONFIG['IGNORE_SELECTED']:
        devices = all_devices - CONFIG['DEVICES']
    else:
        devices = CONFIG['DEVICES'] - unknown_devices
    CONFIG['MAPPINGS'] = dict([(device, mappings[device])
                               for device in devices])


def detect_mappings():
    """For each cache device find the appropriate disks.

    Parse output of ``dmsetup table`` in form

        cachedev1: 0 20480 flashcache conf:
            ssd dev (/dev/sda), disk dev (/dev/sdb) cache mode(WRITE_BACK)
            ...

    and return dictionary like

        {
            'cachedev1': 'sda+sdb',
            ...
        }
    """
    try:
        dmsetup = Popen([CONFIG['DMSETUP'], 'table'],
                        stdout=PIPE, stderr=STDOUT)
    except OSError:
        raise Exception("Can't execute {0}.".format(CONFIG['DMSETUP']))
    if dmsetup.wait() != 0:
        raise Exception('dmsetup execution error')
    return dict([(dmdev, '{0}+{1}'.format(ssd, disk))
                 for dmdev, ssd, disk
                 in DMSETUP_RE.findall(dmsetup.stdout.read())])


def read_callback():
    """Read and dispatch statistics of flashcache devices.

    For devices registered in the ``CONFIG['MAPPINGS']`` dispatch
    statistics from files ``flashcache_stats``, ``flashcache_errors``
    from the directory ``/proc/flashcache``.
    """
    for device in CONFIG['MAPPINGS']:
        for name in ['flashcache_stats', 'flashcache_errors']:
            stats_file = os.path.join(PROC_ROOT,
                                      CONFIG['MAPPINGS'][device], name)
            with open(stats_file) as stats:
                dispatch_stats(stats.read(), device)


def dispatch_stats(stats, device):
    """Dispatch statistics of flashcache device.

    Parse file with statistics in format

        reads=90 writes=0 ...

    and dispatch metrics named like ``flashcache-device/gauge-reads``.
    """
    for metric, val in STATS_RE.findall(stats):
        value = collectd.Values()
        value.plugin = 'flashcache'
        value.plugin_instance = device
        value.type = 'gauge'
        value.type_instance = metric.replace(' ', '_')
        value.values = [int(val)]
        value.dispatch()


def log(message, level='warning'):
    """Write message to collectd log.

    Call appropriate logging method of ``collectd`` module accordingly
    to ``level`` parameter.
    """
    level_method = getattr(collectd, level)
    level_method('flashcache module: {0}'.format(message))


collectd.register_config(config_callback, name='flashcache')
collectd.register_init(init_callback, name='flashcache')
collectd.register_read(read_callback, name='flashcache')
