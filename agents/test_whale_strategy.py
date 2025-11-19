#!/usr/bin/env python3
"""
Quick test runner for Whale Following Strategy.

This script runs only the whale following strategy to demonstrate it in action.

Usage:
    python3 test_whale_strategy.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging

from agents.utils.config import config
from agents.utils.database import db
from agents.application.risk_manager import RiskManager
from agents.application.strategies.whale_following import WhaleFollowingStrategy

# Use paper trading client
try:
    from agents.polymarket.polymarket import Polymarket
except (ImportError, ModuleNotFoundError):
    from agents.polymarket.polymarket_paper import PolymarketPaper as Polymarket


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Run whale following strategy test."""
    print("=" * 70)
    print("WHALE FOLLOWING STRATEGY - TEST RUN")
    print("=" * 70)

    setup_logging()

    # Initialize components
    print("\nInitializing components...")
    polymarket = Polymarket()
    risk_mgr = RiskManager(polymarket)

    # Create whale following strategy
    print("Creating whale following strategy...")
    strategy = WhaleFollowingStrategy(
        polymarket=polymarket,
        risk_manager=risk_mgr,
        enabled=True
    )

    print("\n" + "=" * 70)
    print("FINDING OPPORTUNITIES")
    print("=" * 70)

    # Find opportunities
    opportunities = strategy.find_opportunities()

    print(f"\n✓ Found {len(opportunities)} whale following opportunities\n")

    if not opportunities:
        print("⚠️  No opportunities found!")
        print("\nPossible reasons:")
        print("  1. No test whales in database (run: python3 seed_test_whales.py)")
        print("  2. No copyable signals (whales need quality score >= 0.70)")
        print("  3. All signals already executed or ignored")
        return

    # Display opportunities
    print("Copyable Signals:")
    print("-" * 70)
    for i, opp in enumerate(opportunities, 1):
        print(f"\n{i}. {opp['reasoning']}")
        print(f"   Whale: {opp['whale_nickname']} ({opp['whale_type']})")
        print(f"   Quality Score: {opp['whale_quality']:.2f}")
        print(f"   Market: {opp['market_id'][:10]}...")
        print(f"   Position: {opp['side']} @ ${opp['current_price']:.3f}")
        print(f"   Whale Size: ${opp['whale_position_size_usd']:,.2f}")
        print(f"   Confidence: {opp['confidence']:.2f}")
        print(f"   Expected Profit: {opp['expected_profit_pct']:.2f}%")

    print("\n" + "=" * 70)
    print("EXECUTING TRADES (PAPER MODE)")
    print("=" * 70)

    # Execute opportunities
    trades = []
    for opp in opportunities:
        print(f"\nExecuting: {opp['whale_nickname']} signal...")
        trade = strategy.execute_opportunity(opp)
        if trade:
            trades.append(trade)
            print(f"✓ Trade #{trade.id} executed")
        else:
            print("✗ Trade not executed (check logs for reason)")

    # Summary
    print("\n" + "=" * 70)
    print("EXECUTION SUMMARY")
    print("=" * 70)

    print(f"\nTotal Opportunities: {len(opportunities)}")
    print(f"Trades Executed: {len(trades)}")

    if trades:
        total_size = sum(float(t.size_usd) for t in trades)
        print(f"Total Capital Deployed: ${total_size:.2f}")

        print("\nExecuted Trades:")
        for trade in trades:
            print(f"  • Trade #{trade.id}: {trade.side} @ ${float(trade.entry_price):.3f} - ${float(trade.size_usd):.2f}")
            print(f"    Confidence: {float(trade.confidence_score):.2f}")
            print(f"    Notes: {trade.notes[:80]}...")

    # Show whale signal status
    print("\n" + "=" * 70)
    print("SIGNAL STATUS")
    print("=" * 70)

    from agents.application.whale import WhaleSignalGenerator
    signal_gen = WhaleSignalGenerator()
    stats = signal_gen.get_signal_stats()

    print(f"\nTotal Signals: {stats['total_signals']}")
    print(f"  Pending: {stats['pending']}")
    print(f"  Executed: {stats['executed']}")
    print(f"  Ignored: {stats['ignored']}")
    print(f"  Expired: {stats['expired']}")
    print(f"\nExecution Rate: {stats['execution_rate']:.1f}%")

    print("\n" + "=" * 70)
    print("✓ TEST COMPLETE")
    print("=" * 70)

    print("\nView results in dashboard: python3 -m streamlit run scripts/python/dashboard.py")


if __name__ == "__main__":
    main()
