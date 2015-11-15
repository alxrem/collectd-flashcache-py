# flashcache plugin for CollectD

The *flashcache plugin* collects statistics about [flashcache][1] devices.
Gather all the metrics in /proc/flashcache in files flashcache_stats,
flashcache_errors for each device.

The *flashcache plugin* is loaded as a python module by plugin
[collectd-python][2].

The plugin was tested on Debian Jessie with collectd-5.4.1 and flashcache-3.1.1

## Parameters

Without parameters the plugin collects statistics about all flashcache devices
found in the system.

### Device _cachedev_

flashcache device for which the statistics are collected. You can specify
multiple parameters. Behavior may be changed by directive *IgnoreSelected*.

### IgnoreSelected _true|false_

If *IgnoreSelected* set to _true_, the devices listed by parameters *Device*
will be excluded from statistics collection. Default value is _false_.

### DMSetup _path/to/dmsetup_

The path to utility dmsetup. Default value is _/sbin/dmsetup_.

## Configuration examples

    # Collectd statistics about all devices
    <Plugin python>
        ModulePath "/usr/lib/collectd/python"
        Import "flashcache"
    </Plugin>

    # Collectd statistics about device cachedev1 only
    <Plugin python>
        ModulePath "/usr/lib/collectd/python"
        Import "flashcache"

        <Module flashcache>
            Device cachedev1
        </Module>
    </Plugin>

    # Collectd statistics about all devices except cachedev2
    <Plugin python>
        ModulePath "/usr/lib/collectd/python"
        Import "flashcache"

        <Module flashcache>
            Device cachedev2
            IgnoreSelected true
        </Module>
    </Plugin>

[1]: https://github.com/facebook/flashcache/
[2]: https://collectd.org/documentation/manpages/collectd-python.5.shtml
