#!/usr/bin/env python3
"""
Seed database with test whale data and signals.

This script creates realistic test whales and signals to demonstrate
the whale following strategy in action.

Usage:
    python3 seed_test_whales.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from decimal import Decimal
import random

from agents.utils.database import db, Whale, WhaleSignal
from agents.application.whale import WhaleMonitor, WhaleScorer, WhaleSignalGenerator

def create_test_whales():
    """Create test whales with realistic performance data."""
    print("=" * 70)
    print("CREATING TEST WHALES")
    print("=" * 70)

    session = db.get_session()
    try:
        # Check if whales already exist
        existing_count = session.query(Whale).count()
        if existing_count > 0:
            print(f"\n⚠️  Found {existing_count} existing whales in database")
            response = input("Delete existing whales and start fresh? (y/n): ")
            if response.lower() == 'y':
                session.query(WhaleSignal).delete()
                session.query(Whale).delete()
                session.commit()
                print("✓ Cleared existing whale data")
            else:
                print("Keeping existing whales, adding new ones...")

        # Define test whales with different quality levels
        test_whales = [
            {
                "address": "0xa1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
                "nickname": "The Oracle",
                "total_volume_usd": Decimal("2500000"),
                "total_trades": 250,
                "winning_trades": 215,
                "losing_trades": 35,
                "win_rate": 86.0,
                "quality_score": 0.88,
                "whale_type": "smart_money",
                "specialization": "politics",
                "sharpe_ratio": 2.5,
                "is_tracked": True
            },
            {
                "address": "0xb2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1",
                "nickname": "Crypto Whale",
                "total_volume_usd": Decimal("1800000"),
                "total_trades": 180,
                "winning_trades": 144,
                "losing_trades": 36,
                "win_rate": 80.0,
                "quality_score": 0.82,
                "whale_type": "smart_money",
                "specialization": "crypto",
                "sharpe_ratio": 2.1,
                "is_tracked": True
            },
            {
                "address": "0xc3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2",
                "nickname": "Sports Savant",
                "total_volume_usd": Decimal("1200000"),
                "total_trades": 320,
                "winning_trades": 240,
                "losing_trades": 80,
                "win_rate": 75.0,
                "quality_score": 0.78,
                "whale_type": "smart_money",
                "specialization": "sports",
                "sharpe_ratio": 1.8,
                "is_tracked": True
            },
            {
                "address": "0xd4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3",
                "nickname": "Market Maker Mike",
                "total_volume_usd": Decimal("950000"),
                "total_trades": 420,
                "winning_trades": 273,
                "losing_trades": 147,
                "win_rate": 65.0,
                "quality_score": 0.68,
                "whale_type": "neutral",
                "specialization": None,
                "sharpe_ratio": 1.2,
                "is_tracked": True
            },
            {
                "address": "0xe5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4",
                "nickname": "FOMO Trader",
                "total_volume_usd": Decimal("500000"),
                "total_trades": 150,
                "winning_trades": 60,
                "losing_trades": 90,
                "win_rate": 40.0,
                "quality_score": 0.35,
                "whale_type": "dumb_money",
                "specialization": None,
                "sharpe_ratio": 0.3,
                "is_tracked": True
            }
        ]

        created_whales = []
        for whale_data in test_whales:
            whale = Whale(
                address=whale_data["address"],
                nickname=whale_data["nickname"],
                total_volume_usd=whale_data["total_volume_usd"],
                total_trades=whale_data["total_trades"],
                winning_trades=whale_data["winning_trades"],
                losing_trades=whale_data["losing_trades"],
                win_rate=whale_data["win_rate"],
                quality_score=whale_data["quality_score"],
                whale_type=whale_data["whale_type"],
                specialization=whale_data["specialization"],
                sharpe_ratio=whale_data["sharpe_ratio"],
                is_tracked=whale_data["is_tracked"],
                first_seen_at=datetime.utcnow() - timedelta(days=180),
                last_activity_at=datetime.utcnow() - timedelta(minutes=random.randint(5, 120))
            )

            session.add(whale)
            created_whales.append(whale)

            print(f"\n✓ Created whale: {whale.nickname}")
            print(f"  Address: {whale.address[:10]}...")
            print(f"  Quality Score: {whale.quality_score:.2f} ({whale.whale_type})")
            print(f"  Win Rate: {whale.win_rate:.1f}%")
            print(f"  Total Volume: ${float(whale.total_volume_usd):,.2f}")
            print(f"  Specialization: {whale.specialization or 'None'}")

        session.commit()

        print(f"\n{'=' * 70}")
        print(f"✓ Created {len(created_whales)} test whales")
        print(f"  - Smart Money: {sum(1 for w in test_whales if w['whale_type'] == 'smart_money')}")
        print(f"  - Neutral: {sum(1 for w in test_whales if w['whale_type'] == 'neutral')}")
        print(f"  - Dumb Money: {sum(1 for w in test_whales if w['whale_type'] == 'dumb_money')}")

        return created_whales

    finally:
        session.close()


def create_test_signals(whales):
    """Create test trading signals from whales."""
    print("\n" + "=" * 70)
    print("CREATING TEST SIGNALS")
    print("=" * 70)

    signal_gen = WhaleSignalGenerator()

    # Sample market IDs (using realistic-looking IDs)
    test_markets = [
        {
            "market_id": "0x1234567890abcdef1234567890abcdef12345678",
            "side": "YES",
            "price": 0.58,
            "whale_index": 0,  # The Oracle
            "size_usd": Decimal("25000")
        },
        {
            "market_id": "0x234567890abcdef1234567890abcdef123456789",
            "side": "NO",
            "price": 0.72,
            "whale_index": 0,  # The Oracle
            "size_usd": Decimal("18000")
        },
        {
            "market_id": "0x34567890abcdef1234567890abcdef1234567890",
            "side": "YES",
            "price": 0.45,
            "whale_index": 1,  # Crypto Whale
            "size_usd": Decimal("30000")
        },
        {
            "market_id": "0x4567890abcdef1234567890abcdef12345678901",
            "side": "YES",
            "price": 0.65,
            "whale_index": 2,  # Sports Savant
            "size_usd": Decimal("15000")
        },
        {
            "market_id": "0x567890abcdef1234567890abcdef123456789012",
            "side": "NO",
            "price": 0.38,
            "whale_index": 3,  # Market Maker Mike (neutral - will be skipped)
            "size_usd": Decimal("12000")
        },
        {
            "market_id": "0x67890abcdef1234567890abcdef1234567890123",
            "side": "YES",
            "price": 0.82,
            "whale_index": 4,  # FOMO Trader (dumb money - will be skipped)
            "size_usd": Decimal("8000")
        }
    ]

    created_signals = []

    for i, market in enumerate(test_markets):
        whale = whales[market["whale_index"]]

        # Create signal with timestamp in the past (so it's ready to copy)
        signal = signal_gen.generate_entry_signal(
            whale_address=whale.address,
            market_id=market["market_id"],
            side=market["side"],
            price=market["price"],
            size_usd=market["size_usd"],
            reasoning=f"{whale.nickname} entered {market['side']} position at ${market['price']:.2f}"
        )

        if signal:
            # Backdate signal creation to make it copyable immediately
            session = db.get_session()
            try:
                db_signal = session.query(WhaleSignal).filter(
                    WhaleSignal.id == signal.id
                ).first()
                if db_signal:
                    # Make signal 6 minutes old (past the 5-minute copy delay)
                    db_signal.created_at = datetime.utcnow() - timedelta(minutes=6)
                    session.commit()
            finally:
                session.close()

            created_signals.append(signal)

            status_emoji = "✅" if whale.quality_score >= 0.70 else "⊗"
            print(f"\n{status_emoji} Signal #{signal.id}: {whale.nickname}")
            print(f"   Market: {market['market_id'][:10]}...")
            print(f"   Position: {market['side']} @ ${market['price']:.2f}")
            print(f"   Size: ${float(market['size_usd']):,.2f}")
            print(f"   Confidence: {signal.confidence:.2f}")
            print(f"   Will copy: {'YES' if whale.quality_score >= 0.70 else 'NO (quality too low)'}")

    print(f"\n{'=' * 70}")
    print(f"✓ Created {len(created_signals)} test signals")

    # Count copyable signals
    copyable = sum(1 for s in created_signals if s.confidence >= 0.70)
    print(f"  - Copyable (quality >= 0.70): {copyable}")
    print(f"  - Will skip (quality < 0.70): {len(created_signals) - copyable}")

    return created_signals


def print_summary():
    """Print summary of whale following setup."""
    print("\n" + "=" * 70)
    print("WHALE FOLLOWING STRATEGY - READY TO TEST")
    print("=" * 70)

    monitor = WhaleMonitor()
    stats = monitor.get_summary_stats()

    print(f"\nTracked Whales: {stats['tracked_whales']}")
    print(f"Smart Money Whales: {stats['smart_money_whales']}")
    print(f"Average Quality Score: {stats['avg_quality_score']:.2f}")
    print(f"Open Positions: {stats['open_positions']}")

    signal_gen = WhaleSignalGenerator()
    copyable = signal_gen.get_copyable_signals()

    print(f"\nCopyable Signals: {len(copyable)}")

    if copyable:
        print("\nReady to copy:")
        for signal in copyable[:3]:  # Show first 3
            whale = monitor.get_whale(signal.whale_address)
            print(f"  • {whale.nickname}: {signal.side} @ ${float(signal.price):.2f} (confidence: {signal.confidence:.2f})")

    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("\n1. Enable whale strategy in Railway:")
    print("   Set environment variable: WHALE_TRACKING_ENABLED=true")
    print("\n2. Run the trading system:")
    print("   python3 run_trading_system.py --strategy whale_following")
    print("\n3. Or test mode (find opportunities only):")
    print("   python3 run_trading_system.py --strategy whale_following --test")
    print("\n4. Check results in the Streamlit dashboard")
    print("\n" + "=" * 70)


def main():
    """Main execution."""
    print("\n" + "=" * 70)
    print("WHALE FOLLOWING STRATEGY - TEST DATA SETUP")
    print("=" * 70)
    print("\nThis script will populate your database with:")
    print("  • 5 test whales (3 smart money, 1 neutral, 1 dumb money)")
    print("  • 6 test signals (4 copyable, 2 will be skipped)")
    print("\nThe signals will be backdated to be immediately copyable.")

    response = input("\nProceed? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return

    # Initialize database
    print("\n" + "=" * 70)
    print("INITIALIZING DATABASE")
    print("=" * 70)

    try:
        db.create_tables()
        print("✓ Database tables ready")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return

    # Create test data
    try:
        whales = create_test_whales()
        signals = create_test_signals(whales)
        print_summary()

        print("\n✓ Test data setup complete!")

    except Exception as e:
        print(f"\n✗ Error creating test data: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
