# target
cd fanrui-spdk
./scripts/pkgdep.sh
./configure
make
./test/unit/unittest.sh

sudo HUGEMEM=49152 scripts/setup.sh
sudo nohup build/bin/nvmf_tgt -m 0x1 --wait-for-rpc &
#sudo scripts/rpc.py iobuf_set_options --large-pool-count 8192
sudo ./scripts/rpc.py framework_start_init
sudo scripts/rpc.py nvmf_create_transport -t TCP
sudo scripts/rpc.py bdev_malloc_create -b Malloc0 8192 512
sudo scripts/rpc.py bdev_malloc_create -b Malloc1 8192 512
sudo scripts/rpc.py bdev_malloc_create -b Malloc2 8192 512
sudo scripts/rpc.py bdev_malloc_create -b Malloc3 8192 512
sudo scripts/rpc.py bdev_delay_create -b Malloc0 -d delay0 -r 300 --nine-nine-read-latency 900 -w 500 --nine-nine-write-latency 1500
sudo scripts/rpc.py bdev_delay_create -b Malloc1 -d delay1 -r 300 --nine-nine-read-latency 900 -w 500 --nine-nine-write-latency 1500
sudo scripts/rpc.py bdev_delay_create -b Malloc2 -d delay2 -r 300 --nine-nine-read-latency 900 -w 500 --nine-nine-write-latency 1500
sudo scripts/rpc.py bdev_delay_create -b Malloc3 -d delay3 -r 300 --nine-nine-read-latency 900 -w 500 --nine-nine-write-latency 1500
sudo scripts/rpc.py nvmf_create_subsystem nqn.2016-06.io.spdk:cnode0 -a -s SPDK00000000000000 -d "SPDK RAM Disk 0"
sudo scripts/rpc.py nvmf_create_subsystem nqn.2016-06.io.spdk:cnode1 -a -s SPDK00000000000001 -d "SPDK RAM Disk 1"
sudo scripts/rpc.py nvmf_create_subsystem nqn.2016-06.io.spdk:cnode2 -a -s SPDK00000000000002 -d "SPDK RAM Disk 2"
sudo scripts/rpc.py nvmf_create_subsystem nqn.2016-06.io.spdk:cnode3 -a -s SPDK00000000000003 -d "SPDK RAM Disk 3"
sudo scripts/rpc.py nvmf_subsystem_add_ns nqn.2016-06.io.spdk:cnode0 delay0 -n 1
sudo scripts/rpc.py nvmf_subsystem_add_ns nqn.2016-06.io.spdk:cnode1 delay1 -n 1
sudo scripts/rpc.py nvmf_subsystem_add_ns nqn.2016-06.io.spdk:cnode2 delay2 -n 1
sudo scripts/rpc.py nvmf_subsystem_add_ns nqn.2016-06.io.spdk:cnode3 delay3 -n 1
sudo scripts/rpc.py nvmf_subsystem_add_listener nqn.2016-06.io.spdk:cnode0 -t TCP -a 172.26.234.107 -s 4420
sudo scripts/rpc.py nvmf_subsystem_add_listener nqn.2016-06.io.spdk:cnode1 -t TCP -a 172.26.234.107 -s 4421
sudo scripts/rpc.py nvmf_subsystem_add_listener nqn.2016-06.io.spdk:cnode2 -t TCP -a 172.26.234.107 -s 4422
sudo scripts/rpc.py nvmf_subsystem_add_listener nqn.2016-06.io.spdk:cnode3 -t TCP -a 172.26.234.107 -s 4423
sudo scripts/rpc.py bdev_set_qos_limit Malloc0 --rw-ios-per-sec 10000
sudo scripts/rpc.py bdev_set_qos_limit Malloc1 --rw-ios-per-sec 10000
sudo scripts/rpc.py bdev_set_qos_limit Malloc2 --rw-ios-per-sec 10000
sudo scripts/rpc.py bdev_set_qos_limit Malloc3 --rw-ios-per-sec 10000
sudo scripts/rpc.py bdev_get_iostat -b Malloc0

# initiator
cd liburing
./configure --cc=gcc --cxx=g++;
make -j$(nproc);
make liburing.pc
sudo make install;
cd ..
sudo modprobe ublk_drv
cd fanrui-spdk
./scripts/pkgdep.sh
./configure --with-ublk
make -j
./test/unit/unittest.sh

sudo yum install fio -y
sudo HUGEMEM=49152 scripts/setup.sh
sudo nohup build/bin/spdk_tgt -m 0x1 &
sudo scripts/rpc.py ublk_create_target
sudo scripts/rpc.py bdev_nvme_attach_controller -b Nvmf0 -t TCP -a 172.26.234.107 -s 4420 -n nqn.2016-06.io.spdk:cnode0 -f IPv4
sudo scripts/rpc.py bdev_nvme_attach_controller -b Nvmf1 -t TCP -a 172.26.234.107 -s 4421 -n nqn.2016-06.io.spdk:cnode1 -f IPv4
sudo scripts/rpc.py bdev_nvme_attach_controller -b Nvmf2 -t TCP -a 172.26.234.107 -s 4422 -n nqn.2016-06.io.spdk:cnode2 -f IPv4
sudo scripts/rpc.py bdev_nvme_attach_controller -b Nvmf3 -t TCP -a 172.26.234.107 -s 4423 -n nqn.2016-06.io.spdk:cnode3 -f IPv4
sudo scripts/rpc.py bdev_raid_create -n Raid0 -z 64 -r 0 -b "Nvmf0n1 Nvmf1n1 Nvmf2n1 Nvmf3n1"
sudo scripts/rpc.py ublk_start_disk Raid0 1 -q 2 -d 128
sudo scripts/rpc.py bdev_malloc_create -b Malloc0 8192 512
sudo scripts/rpc.py bdev_delay_create -b Malloc0 -d delay0 -r 300 --nine-nine-read-latency 900 -w 500 --nine-nine-write-latency 1500
sudo scripts/rpc.py ublk_start_disk delay0 2 -q 2 -d 128
sudo scripts/rpc.py bdev_set_qos_limit Malloc0 --rw-ios-per-sec 10000

fio --name=test --filename=/dev/ublkb1 --rw=randrw --bs=4k --iodepth=1 --numjobs=1 --runtime=60 --time_based --ioengine=libaio --direct=1 --group_reporting
fio --name=test --filename=/dev/ublkb2 --rw=randrw --bs=4k --iodepth=1 --numjobs=1 --runtime=60 --time_based --ioengine=libaio --direct=1 --group_reporting

fio --name=test --filename=/dev/ublkb1 --rw=randrw --bs=4k --iodepth=64 --numjobs=2 --runtime=60 --time_based --ioengine=libaio --direct=1 --group_reporting