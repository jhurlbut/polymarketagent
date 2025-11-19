#!/usr/bin/env python3
"""
Find and import whale traders from Polymarket.

This script helps identify high-performing traders on Polymarket
and imports them into the whale tracking database.

Methods:
1. Polymarket API - Get traders from specific markets
2. Manual entry - Add known whale addresses
3. Blockchain analysis - Find large transactions (future)

Usage:
    python3 find_whales.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import requests
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional

from agents.utils.database import db, Whale
from agents.application.whale import WhaleMonitor, WhaleScorer


class WhaleFinder:
    """Find and import whale traders."""

    def __init__(self):
        """Initialize whale finder."""
        self.monitor = WhaleMonitor()
        self.scorer = WhaleScorer()
        self.polymarket_api = "https://clob.polymarket.com"

    def get_market_traders(self, market_id: str) -> List[Dict]:
        """
        Get traders from a specific market.

        Args:
            market_id: Polymarket market ID

        Returns:
            List of trader addresses with volume
        """
        print(f"\nFetching traders for market: {market_id[:10]}...")

        try:
            # Get market orderbook to find active traders
            # Note: This is a simplified example - actual API may differ
            url = f"{self.polymarket_api}/markets/{market_id}"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                print(f"✗ Failed to fetch market data: {response.status_code}")
                return []

            # In production, you would parse the actual Polymarket API response
            # For now, this is a placeholder for the structure
            print("✓ Market data fetched (API integration needed)")
            return []

        except Exception as e:
            print(f"✗ Error fetching market traders: {e}")
            return []

    def find_whales_from_leaderboard(self) -> List[str]:
        """
        Find whales from Polymarket leaderboard.

        Returns:
            List of whale addresses
        """
        print("\n" + "=" * 70)
        print("FINDING WHALES FROM POLYMARKET LEADERBOARD")
        print("=" * 70)

        print("\n⚠️  Note: Polymarket leaderboard requires web scraping or API access")
        print("Manual steps to find whales:")
        print("  1. Visit: https://polymarket.com/leaderboard")
        print("  2. Copy top trader addresses")
        print("  3. Use add_manual_whales() to import them")

        # In production, you would:
        # 1. Scrape the leaderboard page
        # 2. Extract trader addresses and stats
        # 3. Return the addresses

        return []

    def add_manual_whales(self, whale_configs: List[Dict]) -> List[Whale]:
        """
        Manually add whale addresses to database.

        Args:
            whale_configs: List of whale configuration dicts

        Returns:
            List of created Whale objects
        """
        print("\n" + "=" * 70)
        print("ADDING MANUAL WHALES")
        print("=" * 70)

        created_whales = []

        for config in whale_configs:
            address = config.get('address')
            nickname = config.get('nickname', None)

            # Check if whale already exists
            existing = self.monitor.get_whale(address)
            if existing:
                print(f"\n⚠️  Whale {address[:10]}... already exists: {existing.nickname}")
                continue

            # Add whale with initial data
            whale = self.monitor.add_whale(
                address=address,
                nickname=nickname,
                quality_score=config.get('quality_score', 0.5),
                whale_type=config.get('whale_type', 'neutral'),
                track=config.get('track', True)
            )

            created_whales.append(whale)

            print(f"\n✓ Added whale: {whale.nickname or address[:10]}...")
            print(f"  Address: {whale.address}")
            print(f"  Initial Quality: {whale.quality_score:.2f}")
            print(f"  Type: {whale.whale_type}")

        return created_whales

    def score_and_track_whale(self, address: str, nickname: Optional[str] = None) -> Optional[Whale]:
        """
        Add whale and calculate quality score from blockchain history.

        Args:
            address: Ethereum address
            nickname: Optional friendly name

        Returns:
            Whale object if created
        """
        print(f"\n" + "=" * 70)
        print(f"ANALYZING WHALE: {nickname or address[:10]}...")
        print("=" * 70)

        # Check if exists
        whale = self.monitor.get_whale(address)

        if not whale:
            # Create new whale
            print("\n1. Creating whale record...")
            whale = self.monitor.add_whale(
                address=address,
                nickname=nickname,
                quality_score=0.0,
                whale_type="neutral",
                track=True
            )
            print(f"✓ Created whale: {whale.address}")

        # Fetch transaction history (placeholder - needs blockchain integration)
        print("\n2. Fetching transaction history...")
        print("⚠️  Blockchain integration needed - skipping for now")
        print("   (Would analyze: trades, positions, P&L, timing, etc.)")

        # Calculate quality score
        print("\n3. Calculating quality score...")

        # For now, use default scoring
        # In production, this would analyze actual transaction history
        quality_score = self.scorer.update_whale_score(address)

        if quality_score:
            print(f"✓ Quality score: {quality_score:.3f}")
            print(f"  Classification: {whale.whale_type}")
            return whale
        else:
            print("✗ Insufficient data for quality scoring")
            return None


def show_known_whales():
    """Display some known successful Polymarket traders."""
    print("\n" + "=" * 70)
    print("KNOWN SUCCESSFUL POLYMARKET TRADERS")
    print("=" * 70)

    print("\n⚠️  Note: These are EXAMPLE addresses for demonstration")
    print("Real whale addresses should be researched from:")
    print("  • Polymarket leaderboard")
    print("  • High-volume market participants")
    print("  • Polygon blockchain transaction analysis")

    known_whales = [
        {
            "nickname": "Example Top Trader #1",
            "address": "0x" + "1" * 40,  # Placeholder
            "specialization": "Politics",
            "estimated_volume": "$2M+",
            "source": "Polymarket Leaderboard"
        },
        {
            "nickname": "Example Top Trader #2",
            "address": "0x" + "2" * 40,  # Placeholder
            "specialization": "Crypto",
            "estimated_volume": "$1.5M+",
            "source": "High-volume markets"
        }
    ]

    for i, whale in enumerate(known_whales, 1):
        print(f"\n{i}. {whale['nickname']}")
        print(f"   Address: {whale['address'][:10]}...")
        print(f"   Specialization: {whale['specialization']}")
        print(f"   Volume: {whale['estimated_volume']}")
        print(f"   Source: {whale['source']}")

    print("\n" + "=" * 70)


def import_from_csv(csv_file: str) -> List[Whale]:
    """
    Import whales from CSV file.

    CSV format:
    address,nickname,specialization,quality_score

    Args:
        csv_file: Path to CSV file

    Returns:
        List of imported Whale objects
    """
    import csv

    print(f"\n" + "=" * 70)
    print(f"IMPORTING WHALES FROM CSV: {csv_file}")
    print("=" * 70)

    finder = WhaleFinder()
    whale_configs = []

    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                whale_configs.append({
                    'address': row['address'],
                    'nickname': row.get('nickname'),
                    'quality_score': float(row.get('quality_score', 0.5)),
                    'whale_type': row.get('whale_type', 'neutral'),
                    'track': True
                })

        print(f"✓ Loaded {len(whale_configs)} whale configs from CSV")

        whales = finder.add_manual_whales(whale_configs)

        print(f"\n✓ Imported {len(whales)} whales from CSV")
        return whales

    except Exception as e:
        print(f"✗ Error importing CSV: {e}")
        return []


def interactive_mode():
    """Interactive whale finder."""
    print("\n" + "=" * 70)
    print("WHALE FINDER - INTERACTIVE MODE")
    print("=" * 70)

    finder = WhaleFinder()

    while True:
        print("\n" + "=" * 70)
        print("OPTIONS:")
        print("  1. Add whale manually (by address)")
        print("  2. View known whale examples")
        print("  3. Import from CSV")
        print("  4. View current tracked whales")
        print("  5. Exit")
        print("=" * 70)

        choice = input("\nSelect option (1-5): ").strip()

        if choice == "1":
            # Manual add
            print("\n--- Add Whale Manually ---")
            address = input("Enter whale address (0x...): ").strip()

            if not address.startswith("0x") or len(address) != 42:
                print("✗ Invalid address format (should be 0x... with 42 characters)")
                continue

            nickname = input("Enter nickname (optional): ").strip() or None

            whale = finder.score_and_track_whale(address, nickname)

            if whale:
                print(f"\n✓ Whale added: {whale.nickname or whale.address[:10]}...")
            else:
                print("\n✗ Failed to add whale")

        elif choice == "2":
            # Show examples
            show_known_whales()

        elif choice == "3":
            # Import CSV
            csv_path = input("\nEnter path to CSV file: ").strip()
            import_from_csv(csv_path)

        elif choice == "4":
            # View tracked
            monitor = WhaleMonitor()
            stats = monitor.get_summary_stats()
            top_whales = monitor.get_top_whales(limit=10)

            print("\n" + "=" * 70)
            print("CURRENTLY TRACKED WHALES")
            print("=" * 70)

            print(f"\nTotal whales: {stats['total_whales']}")
            print(f"Tracked: {stats['tracked_whales']}")
            print(f"Smart money: {stats['smart_money_whales']}")
            print(f"Avg quality: {stats['avg_quality_score']:.2f}")

            if top_whales:
                print("\nTop 10 by quality:")
                for i, whale in enumerate(top_whales, 1):
                    print(f"  {i}. {whale.nickname or whale.address[:10]}... - "
                          f"Quality: {whale.quality_score:.2f} ({whale.whale_type})")

        elif choice == "5":
            print("\nExiting whale finder...")
            break

        else:
            print("\n✗ Invalid option, please select 1-5")


def main():
    """Main execution."""
    print("\n" + "=" * 70)
    print("POLYMARKET WHALE FINDER")
    print("=" * 70)

    print("\nThis tool helps you find and import high-performing traders (whales)")
    print("to track and copy via the whale following strategy.")

    print("\n" + "=" * 70)
    print("HOW TO FIND REAL WHALES:")
    print("=" * 70)

    print("\n1. POLYMARKET LEADERBOARD")
    print("   • Visit: https://polymarket.com/leaderboard")
    print("   • Copy top trader addresses")
    print("   • Add them using this tool")

    print("\n2. HIGH-VOLUME MARKETS")
    print("   • Browse popular markets on Polymarket")
    print("   • Check 'Recent Trades' for large positions")
    print("   • Note addresses with consistent big trades")

    print("\n3. BLOCKCHAIN ANALYSIS (Advanced)")
    print("   • Monitor Polygon CTF Exchange contract")
    print("   • Filter transactions > $5,000")
    print("   • Track addresses with multiple large trades")

    print("\n4. SOCIAL RESEARCH")
    print("   • Twitter: Look for Polymarket power users")
    print("   • Discord: Active community members")
    print("   • Their addresses often in bio/profile")

    # Start interactive mode
    interactive_mode()


if __name__ == "__main__":
    main()
