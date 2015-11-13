#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 sw=4 et ai

import os
import os.path
import shutil
import StringIO
from subprocess import Popen, PIPE, STDOUT, call, check_output
from tempfile import mkstemp, mkdtemp
from time import strftime, sleep
import unittest


class CollectdTestCase(unittest.TestCase):
    ALL_METRICS = [
        'back_merge', 'disk_write_errors', 'metadata_cleans', 'pid_adds',
        'read_invalidates', 'ssd_writes', 'write_hit_percent', 'cleanings',
        'disk_writes', 'metadata_dirties', 'pid_dels', 'reads',
        'uncached_IO_requeue', 'write_hits', 'dirty_write_hit_percent',
        'fallow_cleanings', 'metadata_ssd_writes', 'pid_drops', 'replacement',
        'uncached_reads', 'write_invalidates', 'dirty_write_hits',
        'front_merge', 'no_room', 'pid_expiry', 'ssd_read_errors',
        'uncached_sequential_reads', 'write_replacement', 'disk_read_errors',
        'memory_alloc_errors', 'pending_enqueues', 'read_hit_percent',
        'ssd_reads', 'uncached_sequential_writes', 'writes', 'disk_reads',
        'metadata_batch', 'pending_inval', 'read_hits', 'ssd_write_errors',
        'uncached_writes']

    def setUp(self):
        self.hostname = 'flashcache.localdomain'
        self.create_metrics_dir()
        self.create_config()
        self.run_collectd()

    def tearDown(self):
        shutil.rmtree(self.metrics_dir)
        os.unlink(self.config)

    def create_metrics_dir(self):
        self.metrics_dir = mkdtemp()


    def create_config(self):
        config_fd, self.config = mkstemp()
        os.write(config_fd, """
            Hostname "{0}"
            FQDNLookup false

            LoadPlugin csv
            LoadPlugin python

            <Plugin csv>
              DataDir "{1}"
            </Plugin>

            <Plugin python>
              ModulePath "/vagrant"
              Import "flashcache"
            </Plugin>
        """.format(self.hostname, self.metrics_dir))
        os.close(config_fd)

    def run_collectd(self):
        p = Popen(['/usr/sbin/collectd', '-C', self.config, '-f'],
                   stdout=PIPE, stderr=PIPE)
        sleep(0.1)
        p.terminate()
        self.stdout, self.stderr = p.communicate()

    def assertHasMetric(self, cachedev, metric):
        self.assertTrue(
                os.path.isfile(self.metrics_file(cachedev, metric)),
                'No metric {0} for device {1}'.format(metric, cachedev))

    def assertHasAllMetrics(self, cachedev):
        for metric in CollectdTestCase.ALL_METRICS:
            self.assertHasMetric(cachedev, metric)

    def assertHasNoMetrics(self, cachedev):
        self.assertFalse(os.path.exists(self.cachedev_dir(cachedev)))

    def assertLeftNoMetrics(self, cachedev):
        unknown_metrics = os.listdir(self.cachedev_dir(cachedev))
        self.assertEqual(
            0, len(unknown_metrics),
            'Unknown metrics {0}'.format(', '.join(unknown_metrics)))

    def deleteAllMetrics(self, cachedev):
        for metric in CollectdTestCase.ALL_METRICS:
            os.unlink(self.metrics_file(cachedev, metric))

    def cachedev_dir(self, cachedev):
        return os.path.join(
                   self.metrics_dir, self.hostname,
                   '{0}-{1}'.format('flashcache', cachedev))

    def metrics_file(self, cachedev, metric):
        return os.path.join(
                   self.cachedev_dir(cachedev),
                   'gauge-{0}-{1}'.format(metric, strftime('%Y-%m-%d')))


class TestStatsFromAllCaches(CollectdTestCase):
    def test_all_devices_has_all_metrics(self):
        self.assertHasAllMetrics('cachedev1')
        self.assertHasAllMetrics('cachedev2')

    def test_all_devices_has_no_unknown_metrics(self):
        self.deleteAllMetrics('cachedev1')
        self.deleteAllMetrics('cachedev2')
        self.assertLeftNoMetrics('cachedev1')
        self.assertLeftNoMetrics('cachedev2')


if __name__ == '__main__':
    if os.geteuid() != 0:
        import sys
        sys.stderr.write('Tests must be run as root\n')
        sys.exit(1)
    unittest.main()
