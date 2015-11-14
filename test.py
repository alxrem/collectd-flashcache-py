#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ts=4 sts=4 sw=4 et ai

import os
import os.path
import shutil
from subprocess import Popen, PIPE
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
        self._hostname = 'flashcache.localdomain'
        self._create_metrics_dir()
        self._create_config()
        self._run_collectd()

    def tearDown(self):
        self._delete_metrics_dir()
        self._delete_config()

    def assertHasMetric(self, cachedev, metric):
        self.assertTrue(
            os.path.isfile(self._metrics_file(cachedev, metric)),
            'No metric {0} for device {1}'.format(metric, cachedev))

    def assertHasAllMetrics(self, cachedev):
        for metric in CollectdTestCase.ALL_METRICS:
            self.assertHasMetric(cachedev, metric)

    def assertHasNoMetrics(self, cachedev):
        self.assertFalse(os.path.exists(self._cachedev_dir(cachedev)))

    def assertLeftNoMetrics(self, cachedev):
        unknown_metrics = os.listdir(self._cachedev_dir(cachedev))
        self.assertEqual(
            0, len(unknown_metrics),
            'Unknown metrics {0}'.format(', '.join(unknown_metrics)))

    def assertStderrContains(self, message):
        self.assertTrue(message in self._stderr)

    def _create_metrics_dir(self):
        self._metrics_dir = mkdtemp()

    def _delete_metrics_dir(self):
        shutil.rmtree(self._metrics_dir)

    def _create_config(self):
        current_test = getattr(self, self._testMethodName)
        if hasattr(current_test, 'config'):
            module_config = """
            <Module flashcache>
                {0}
            </Module>
            """.format(current_test.config)
        else:
            module_config = ''

        config_fd, self._config = mkstemp()
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
              LogTraces true

              {2}

            </Plugin>
        """.format(self._hostname, self._metrics_dir, module_config))
        os.close(config_fd)

    def _delete_config(self):
        os.unlink(self._config)

    def _run_collectd(self):
        p = Popen(['/usr/sbin/collectd', '-C', self._config, '-f'],
                  stdout=PIPE, stderr=PIPE)
        sleep(0.1)
        p.terminate()
        self._stdout, self._stderr = p.communicate()

    def _cachedev_dir(self, cachedev):
        return os.path.join(self._metrics_dir, self._hostname,
                            '{0}-{1}'.format('flashcache', cachedev))

    def _metrics_file(self, cachedev, metric):
        return os.path.join(
            self._cachedev_dir(cachedev),
            'gauge-{0}-{1}'.format(metric, strftime('%Y-%m-%d')))


def with_config(config):
    def set_config(method):
        method.config = config
        return method
    return set_config


class TestConfigWarnings(CollectdTestCase):
    @with_config("""
        Devices cachedevice
    """)
    def test_warning_about_unknown_config_key(self):
        self.assertStderrContains('flashcache module: '
                                  'Ignoring unknown config key "Devices".')

    @with_config("""
        Device cachedevice
    """)
    def test_warning_about_unknown_device(self):
        self.assertStderrContains('flashcache module: '
                                  'Unknown flashcache device "cachedevice".')

class TestDefautConfig(CollectdTestCase):
    def test_all_devices_has_all_metrics(self):
        self.assertHasAllMetrics('cachedev1')
        self.assertHasAllMetrics('cachedev2')

    def test_all_devices_has_no_unknown_metrics(self):
        self._delete_all_metrics('cachedev1')
        self._delete_all_metrics('cachedev2')
        self.assertLeftNoMetrics('cachedev1')
        self.assertLeftNoMetrics('cachedev2')

    def _delete_all_metrics(self, cachedev):
        for metric in CollectdTestCase.ALL_METRICS:
            os.unlink(self._metrics_file(cachedev, metric))


class TestIgnoreSelected(CollectdTestCase):
    @with_config("""
        Device cachedev2
        IgnoreSelected true
    """)
    def test_ignore_cachedev2(self):
        self.assertHasAllMetrics('cachedev1')
        self.assertHasNoMetrics('cachedev2')

    @with_config("""
        Device cachedev2
        IgnoreSelected false
    """)
    def test_collect_only_cachedev2(self):
        self.assertHasNoMetrics('cachedev1')
        self.assertHasAllMetrics('cachedev2')

    @with_config("""
        Device cachedev2
    """)
    def test_do_not_ignore_selected_by_default(self):
        self.assertHasNoMetrics('cachedev1')
        self.assertHasAllMetrics('cachedev2')


class TestCustomDmsetupPath(CollectdTestCase):
    def setUp(self):
        shutil.move('/sbin/dmsetup', '/usr/local/bin/dmsetup')
        super(TestCustomDmsetupPath, self).setUp()

    def tearDown(self):
        super(TestCustomDmsetupPath, self).tearDown()
        shutil.move('/usr/local/bin/dmsetup', '/sbin/dmsetup')

    @with_config("""
        DMSetup "/usr/local/bin/dmsetup"
    """)
    def test_custom_dmsetup_path(self):
        self.assertHasAllMetrics('cachedev1')
        self.assertHasAllMetrics('cachedev2')


class TestAbortOnInvalidDmsetupPath(CollectdTestCase):
    @with_config("""
        DMSetup "/notexists"
    """)
    def test_abort_on_invalid_dmsetup_path(self):
        self.assertStderrContains("Can't execute /notexists.")
        self.assertHasNoMetrics('cachedev1')
        self.assertHasNoMetrics('cachedev2')


if __name__ == '__main__':
    if os.geteuid() != 0:
        import sys
        sys.stderr.write('Tests must be run as root\n')
        sys.exit(1)
    unittest.main()
