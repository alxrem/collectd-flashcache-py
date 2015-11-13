# vim: ft=ruby ts=2 sts=2 sw=2 et ai

require 'etc'

Vagrant.configure('2') do |config|
  config.vm.box = 'debian/jessie64'

  config.vm.provider 'virtualbox' do |v|
    v.customize ['storagectl', :id,
                 '--name', 'SCSI Controller', '--add', 'scsi']
    4.times do |i|
      image = File.join(Etc.systmpdir, "flashcachetest#{i}.vdi")

      v.customize ['createhd', '--filename', image, '--size', 10]
      v.customize ['storageattach', :id, '--storagectl', 'SCSI Controller',
                   '--port', i, '--device', 0,
                   '--type', 'hdd', '--medium', image]
    end
  end

  config.vm.provision 'shell', inline: <<SCRIPT
echo 'DISABLE=1' > /etc/default/collectd

apt-get update
apt-get install -y --no-install-recommends \
                -o Dpkg::Options::="--force-confold" \
        linux-headers-amd64 \
        flashcache-dkms \
        flashcache-utils \
        libpython2.7 \
        collectd

flashcache_create -p back cachedev1 \
        /dev/disk/by-path/pci-0000:00:14.0-scsi-0:0:0:0 \
        /dev/disk/by-path/pci-0000:00:14.0-scsi-0:0:1:0
flashcache_create -p back cachedev2 \
        /dev/disk/by-path/pci-0000:00:14.0-scsi-0:0:2:0 \
        /dev/disk/by-path/pci-0000:00:14.0-scsi-0:0:3:0
SCRIPT
end
