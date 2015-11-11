# vim: ft=ruby ts=2 sts=2 sw=2 et ai

require 'etc'

Vagrant.configure('2') do |config|
  config.vm.box = 'debian/jessie64'

  config.vm.provider 'virtualbox' do |v|
    v.customize ['storagectl', :id,
                 '--name', 'SATA Controller', '--add', 'sata']
    2.times do |i|
      image = File.join(Etc.systmpdir, "flashcachetest#{i}.vdi")

      v.customize ['createhd', '--filename', image, '--size', 10]
      v.customize ['storageattach', :id, '--storagectl', 'SATA Controller',
                   '--port', i, '--device', 0,
                   '--type', 'hdd', '--medium', image]
    end
  end

  config.vm.provision 'shell', path: 'vagrant/provision'
end
