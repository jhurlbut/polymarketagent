#!/usr/bin/env python3
"""
Run Automatic Whale Discovery Service.

This script continuously scans Polymarket markets to automatically discover
and track high-performing whale traders.

Usage:
    python3 run_whale_discovery.py [--scan-interval MINUTES] [--markets-per-scan N]

Examples:
    # Run with default settings (5 min interval, 50 markets)
    python3 run_whale_discovery.py

    # Scan every 1 minute, 20 markets at a time
    python3 run_whale_discovery.py --scan-interval 1 --markets-per-scan 20

    # One-time scan only
    python3 run_whale_discovery.py --once
"""

import argparse
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.application.whale.auto_discovery import PolymarketWhaleDiscovery
from agents.utils.config import config
from agents.utils.database import db


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('whale_discovery.log')
        ]
    )


def run_once(markets_to_scan: int = 50):
    """Run a single scan and exit."""
    print("=" * 70)
    print("WHALE DISCOVERY - ONE-TIME SCAN")
    print("=" * 70)

    # Initialize database
    db.create_tables()

    # Create discovery service
    discovery = PolymarketWhaleDiscovery()

    # Run scan
    stats = discovery.scan_all_markets(limit=markets_to_scan)

    # Print results
    print("\n" + "=" * 70)
    print("SCAN RESULTS")
    print("=" * 70)

    for key, value in stats.items():
        print(f"{key}: {value}")

    print("\n" + "=" * 70)
    print("✓ Scan complete!")
    print("=" * 70)

    # Show discovered whales
    from agents.application.whale import WhaleMonitor
    monitor = WhaleMonitor()

    top_whales = monitor.get_top_whales(limit=10)

    if top_whales:
        print("\nTop Whales Discovered:")
        for i, whale in enumerate(top_whales, 1):
            print(
                f"{i}. {whale.nickname or whale.address[:10]}... - "
                f"Quality: {whale.quality_score:.2f} ({whale.whale_type}), "
                f"Volume: ${float(whale.total_volume_usd):,.0f}"
            )
    else:
        print("\nNo whales discovered yet. Run more scans to build whale database.")


def run_continuous(
    scan_interval_minutes: int = 5,
    markets_per_scan: int = 50
):
    """Run continuous whale discovery."""
    print("=" * 70)
    print("WHALE DISCOVERY - CONTINUOUS MODE")
    print("=" * 70)
    print(f"\nScan interval: {scan_interval_minutes} minute(s)")
    print(f"Markets per scan: {markets_per_scan}")
    print("\nPress Ctrl+C to stop\n")
    print("=" * 70)

    # Initialize database
    db.create_tables()

    # Create and run discovery service
    discovery = PolymarketWhaleDiscovery()

    discovery.run_continuous_discovery(
        scan_interval_seconds=scan_interval_minutes * 60,
        markets_per_scan=markets_per_scan
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Polymarket Automatic Whale Discovery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--scan-interval',
        type=int,
        default=5,
        help='Minutes between scans (default: 5)'
    )

    parser.add_argument(
        '--markets-per-scan',
        type=int,
        default=50,
        help='Number of markets to scan per run (default: 50)'
    )

    parser.add_argument(
        '--once',
        action='store_true',
        help='Run one scan and exit (no continuous mode)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)

    # Check config
    if not config.WHALE_TRACKING_ENABLED:
        print("\n⚠️  WARNING: WHALE_TRACKING_ENABLED is false in config")
        print("Set WHALE_TRACKING_ENABLED=true in .env to enable whale strategy\n")

    # Run appropriate mode
    if args.once:
        run_once(markets_to_scan=args.markets_per_scan)
    else:
        run_continuous(
            scan_interval_minutes=args.scan_interval,
            markets_per_scan=args.markets_per_scan
        )


if __name__ == "__main__":
    main()
