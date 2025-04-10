#!/usr/bin/env python3
import time
import os
import argparse


def get_disk_stats(device_name=None):
    """Get read and write statistics for block devices"""
    result = {}
    with open('/proc/diskstats', 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 14:  # diskstats should have at least 14 fields
                continue

            current_device = parts[2]
            # If a specific device is requested, only track that one
            if device_name and current_device != device_name:
                continue

            # Fields from /proc/diskstats
            # sectors read (field 5) * 512 = bytes read
            # sectors written (field 9) * 512 = bytes written
            sectors_read = int(parts[5])
            sectors_written = int(parts[9])

            # Convert sectors to bytes (1 sector = 512 bytes typically)
            bytes_read = sectors_read * 512
            bytes_written = sectors_written * 512

            result[current_device] = {
                'read_bytes': bytes_read,
                'write_bytes': bytes_written
            }
    return result


def get_network_stats(interface_name=None):
    """Get network statistics for interfaces"""
    result = {}
    with open('/proc/net/dev', 'r') as f:
        # Skip the first two header lines
        next(f)
        next(f)

        for line in f:
            parts = line.strip().split(':', 1)
            if len(parts) != 2:
                continue

            interface = parts[0].strip()
            # If a specific interface is requested, only track that one
            if interface_name and interface != interface_name:
                continue

            values = parts[1].strip().split()
            # First value is received bytes, 9th value is transmitted bytes
            rx_bytes = int(values[0])
            tx_bytes = int(values[8])

            result[interface] = {
                'rx_bytes': rx_bytes,
                'tx_bytes': tx_bytes
            }
    return result


def print_stats(device, interface, prev_disk, curr_disk, prev_net, curr_net, interval):
    """Print the I/O statistics in a single table with utilization ratio"""
    timestamp = time.strftime("%H:%M:%S")

    # Calculate disk rates
    read_rate = 0
    write_rate = 0
    if device in curr_disk and device in prev_disk:
        read_rate = (curr_disk[device]['read_bytes'] - prev_disk[device]['read_bytes']) / interval
        write_rate = (curr_disk[device]['write_bytes'] - prev_disk[device]['write_bytes']) / interval

    # Calculate network rates
    rx_rate = 0
    tx_rate = 0
    if interface in curr_net and interface in prev_net:
        rx_rate = (curr_net[interface]['rx_bytes'] - prev_net[interface]['rx_bytes']) / interval
        tx_rate = (curr_net[interface]['tx_bytes'] - prev_net[interface]['tx_bytes']) / interval

    # Calculate utilization ratio (disk I/O to network I/O)
    total_disk = read_rate + write_rate
    total_network = rx_rate + tx_rate

    if total_network > 0:
        utilization = total_disk / total_network * 100.0
    else:
        utilization = float('inf')  # To indicate division by zero

    # Print header on first run or every 20 lines
    if not hasattr(print_stats, "counter"):
        print_stats.counter = 0
        print(
            f"\n{'Time':<10} | {'Disk':<10} | {'Read (B/s)':<12} | {'Write (B/s)':<12} | {'Interface':<10} | {'In (B/s)':<12} | {'Out (B/s)':<12} | {'Util (%)':<10}")
        print(f"{'-' * 10}-+-{'-' * 10}-+-{'-' * 12}-+-{'-' * 12}-+-{'-' * 10}-+-{'-' * 12}-+-{'-' * 12}-+-{'-' * 10}")

    print_stats.counter += 1
    # if print_stats.counter % 20 == 0:
    #     print(
    #         f"\n{'Time':<10} | {'Disk':<10} | {'Read (B/s)':<12} | {'Write (B/s)':<12} | {'Interface':<10} | {'In (B/s)':<12} | {'Out (B/s)':<12} | {'Util (%)':<10}")
    #     print(f"{'-' * 10}-+-{'-' * 10}-+-{'-' * 12}-+-{'-' * 12}-+-{'-' * 10}-+-{'-' * 12}-+-{'-' * 12}-+-{'-' * 10}")

    # Format the utilization ratio
    if utilization == float('inf'):
        util_display = "∞"  # Infinity symbol for division by zero
    else:
        util_display = f"{utilization:.2f}"

    # Print the stats in a single row
    print(
        f"{timestamp:<10} | {device:<10} | {int(read_rate):<12} | {int(write_rate):<12} | {interface:<10} | {int(rx_rate):<12} | {int(tx_rate):<12} | {util_display:<10}")


def list_available_devices():
    """List available block devices and network interfaces"""
    print("Available Block Devices:")
    disk_stats = get_disk_stats()
    for device in sorted(disk_stats.keys()):
        print(f"  - {device}")

    print("\nAvailable Network Interfaces:")
    net_stats = get_network_stats()
    for interface in sorted(net_stats.keys()):
        print(f"  - {interface}")


def main():
    parser = argparse.ArgumentParser(description='Monitor disk and network I/O with utilization ratio.')
    parser.add_argument('-d', '--disk', help='Block device to monitor (e.g., sda, sda1)')
    parser.add_argument('-i', '--interface', help='Network interface to monitor (e.g., eth0, wlan0)')
    parser.add_argument('-l', '--list', action='store_true', help='List available devices and interfaces')
    parser.add_argument('-t', '--time', type=int, default=1,
                        help='Interval between measurements in seconds (default: 1)')

    args = parser.parse_args()

    if args.list:
        list_available_devices()
        return

    # If no disk or interface specified, use the first available ones
    if not args.disk:
        disk_stats = get_disk_stats()
        if disk_stats:
            args.disk = sorted(disk_stats.keys())[0]
            print(f"No disk specified. Using {args.disk}")
        else:
            print("No block devices found.")
            return

    if not args.interface:
        net_stats = get_network_stats()
        if net_stats:
            # Try to get a non-loopback interface first
            interfaces = sorted([i for i in net_stats.keys() if i != 'lo'])
            if not interfaces and 'lo' in net_stats:
                args.interface = 'lo'
            else:
                args.interface = interfaces[0]
            print(f"No interface specified. Using {args.interface}")
        else:
            print("No network interfaces found.")
            return

    interval = args.time

    try:
        # Get initial stats
        prev_disk_stats = get_disk_stats(args.disk)
        prev_net_stats = get_network_stats(args.interface)

        print(f"\nStarting I/O monitoring for disk {args.disk} and interface {args.interface}.")
        print(f"Interval: {interval} second(s). Press Ctrl+C to stop.")
        print("Utilization Ratio = (Disk Read + Write) / (Network In + Out)")

        while True:
            # Wait for the specified interval
            time.sleep(interval)

            # Get current stats
            curr_disk_stats = get_disk_stats(args.disk)
            curr_net_stats = get_network_stats(args.interface)

            # Print the stats
            print_stats(args.disk, args.interface, prev_disk_stats, curr_disk_stats, prev_net_stats, curr_net_stats,
                        interval)

            # Update previous stats for next iteration
            prev_disk_stats = curr_disk_stats
            prev_net_stats = curr_net_stats

    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Check if running as root, as /proc/diskstats might require elevated permissions
    if os.geteuid() != 0:
        print("Warning: This script may need to be run with sudo to access all disk statistics.")
    main()
