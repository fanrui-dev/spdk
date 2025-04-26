#!/usr/bin/env python3
"""
SPDK IOPS Monitor - Track IOPS for SPDK block devices in real-time with utilization
"""

import json
import time
import argparse
import subprocess
from typing import Dict, Any, Optional


class SPDKIOStatMonitor:
    def __init__(self, bdev_name: str, max_iops: int = 10000, rpc_socket: str = "/var/tmp/spdk.sock"):
        """Initialize the SPDK IOPS monitor with the given block device name and RPC socket path.

        Args:
            bdev_name: Name of the SPDK block device to monitor
            max_iops: Maximum IOPS capacity (for utilization calculation)
            rpc_socket: Path to the SPDK RPC socket
        """
        self.bdev_name = bdev_name
        self.rpc_socket = rpc_socket
        self.max_iops = max_iops
        self.prev_stats: Optional[Dict[str, Any]] = None
        self.prev_time = 0.0

    def _get_iostat(self) -> Dict[str, Any]:
        """Execute the bdev_get_iostat RPC and return the results.

        Returns:
            Dict containing the iostat results
        """
        cmd = [
            "scripts/rpc.py",
            "-s", self.rpc_socket,
            "bdev_get_iostat",
            "-b", self.bdev_name
        ]

        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error executing RPC: {e}")
            print(f"Stderr: {e.stderr}")
            raise
        except json.JSONDecodeError:
            print(f"Error parsing JSON response: {result.stdout}")
            raise

    def _calculate_iops(self, current_stats: Dict[str, Any]) -> Dict[str, float]:
        """Calculate the IOPS based on current and previous statistics.

        Args:
            current_stats: Current statistics from bdev_get_iostat

        Returns:
            Dictionary with read_iops, write_iops, total_iops, and utilization
        """
        current_time = time.time()

        if self.prev_stats is None:
            self.prev_stats = current_stats
            self.prev_time = current_time
            return {"read_iops": 0.0, "write_iops": 0.0, "total_iops": 0.0, "utilization": 0.0}

        time_diff = current_time - self.prev_time

        if time_diff <= 0:
            return {"read_iops": 0.0, "write_iops": 0.0, "total_iops": 0.0, "utilization": 0.0}

        # Find the target bdev in the statistics
        bdev_stats = None
        for bdev in current_stats.get("bdevs", []):
            if bdev.get("name") == self.bdev_name:
                bdev_stats = bdev
                break

        if bdev_stats is None:
            print(f"Error: Could not find statistics for bdev {self.bdev_name}")
            return {"read_iops": 0.0, "write_iops": 0.0, "total_iops": 0.0, "utilization": 0.0}

        # Find previous stats for this bdev
        prev_bdev_stats = None
        for bdev in self.prev_stats.get("bdevs", []):
            if bdev.get("name") == self.bdev_name:
                prev_bdev_stats = bdev
                break

        if prev_bdev_stats is None:
            self.prev_stats = current_stats
            self.prev_time = current_time
            return {"read_iops": 0.0, "write_iops": 0.0, "total_iops": 0.0, "utilization": 0.0}

        # Calculate read IOPS
        read_ops_diff = bdev_stats.get("num_read_ops", 0) - prev_bdev_stats.get("num_read_ops", 0)
        read_iops = read_ops_diff / time_diff

        # Calculate write IOPS
        write_ops_diff = bdev_stats.get("num_write_ops", 0) - prev_bdev_stats.get("num_write_ops", 0)
        write_iops = write_ops_diff / time_diff

        # Calculate total IOPS and utilization
        total_iops = read_iops + write_iops
        utilization = (total_iops / self.max_iops) * 100.0

        # Update previous stats and time
        self.prev_stats = current_stats
        self.prev_time = current_time

        return {
            "read_iops": read_iops,
            "write_iops": write_iops,
            "total_iops": total_iops,
            "utilization": utilization
        }

    def monitor(self, interval: float = 1.0):
        """Monitor IOPS and display statistics periodically.

        Args:
            interval: Time interval between updates in seconds
        """
        print(f"Monitoring IOPS for SPDK block device: {self.bdev_name}")
        print(f"Maximum IOPS capacity: {self.max_iops}")
        print(f"Press Ctrl+C to stop monitoring")
        print("-" * 100)
        print(f"{'Timestamp':20} {'Read IOPS':15} {'Write IOPS':15} {'Total IOPS':15} {'Utilization (%)':15}")
        print("-" * 100)

        try:
            while True:
                try:
                    current_stats = self._get_iostat()
                    iops_stats = self._calculate_iops(current_stats)

                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{timestamp:20} {iops_stats['read_iops']:15.2f} {iops_stats['write_iops']:15.2f} "
                          f"{iops_stats['total_iops']:15.2f} {iops_stats['utilization']:15.2f}")

                    time.sleep(interval)
                except Exception as e:
                    print(f"Error during monitoring: {e}")
                    time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")


def main():
    parser = argparse.ArgumentParser(description="Monitor IOPS for SPDK block devices with utilization")
    parser.add_argument("bdev_name", help="Name of the SPDK block device to monitor")
    parser.add_argument("-s", "--socket", default="/var/tmp/spdk.sock",
                        help="Path to the SPDK RPC socket (default: /var/tmp/spdk.sock)")
    parser.add_argument("-i", "--interval", type=float, default=1.0,
                        help="Update interval in seconds (default: 1.0)")
    parser.add_argument("-m", "--max-iops", type=int, default=1000,
                        help="Maximum IOPS capacity for utilization calculation (default: 1000)")

    args = parser.parse_args()

    monitor = SPDKIOStatMonitor(args.bdev_name, args.max_iops, args.socket)
    monitor.monitor(args.interval)


if __name__ == "__main__":
    main()
