#!/usr/bin/env python3
"""
Continuous Trading System Runner

Runs the trading system on a schedule to continuously scan for opportunities.
"""

import time
import sys
import os
from datetime import datetime
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run_trading_system import run_system
from agents.utils.database import db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('continuous_trading.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def run_continuous(interval_minutes: int = 15):
    """
    Run trading system continuously at specified interval.

    Args:
        interval_minutes: Minutes between scans (default: 15)
    """
    logger.info(f"Starting continuous trading system (scanning every {interval_minutes} minutes)")
    logger.info("Press Ctrl+C to stop")

    scan_count = 0

    try:
        while True:
            scan_count += 1
            logger.info("=" * 70)
            logger.info(f"SCAN #{scan_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 70)

            try:
                # Run the trading system
                success = run_system()

                if success:
                    logger.info(f"✓ Scan #{scan_count} completed successfully")
                else:
                    logger.warning(f"⚠ Scan #{scan_count} completed with errors")

            except Exception as e:
                logger.error(f"✗ Scan #{scan_count} failed: {e}", exc_info=True)

            # Wait for next scan (check for manual triggers every 10 seconds)
            wait_seconds = interval_minutes * 60
            next_scan = datetime.now()
            next_scan = next_scan.replace(
                minute=(next_scan.minute + interval_minutes) % 60,
                second=0,
                microsecond=0
            )

            logger.info(f"\nNext scan in {interval_minutes} minutes ({next_scan.strftime('%H:%M:%S')})")
            logger.info("Waiting... (checking for manual triggers every 10s)\n")

            # Wait in chunks to allow checking for manual scan requests
            elapsed = 0
            check_interval = 10  # Check every 10 seconds
            while elapsed < wait_seconds:
                time.sleep(min(check_interval, wait_seconds - elapsed))
                elapsed += check_interval

                # Check if manual scan was requested from dashboard
                if db.check_scan_requested():
                    logger.info("🔔 Manual scan requested from dashboard - running immediate scan!")
                    break

    except KeyboardInterrupt:
        logger.info("\n" + "=" * 70)
        logger.info("Continuous trading stopped by user")
        logger.info(f"Total scans completed: {scan_count}")
        logger.info("=" * 70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run Polymarket trading system continuously"
    )

    parser.add_argument(
        '--interval',
        type=int,
        default=15,
        help='Minutes between scans (default: 15)'
    )

    args = parser.parse_args()

    run_continuous(interval_minutes=args.interval)
