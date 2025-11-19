#!/usr/bin/env python3
"""
Main runner for Polymarket Trading System.

This script initializes and runs all trading strategies with
risk management, performance tracking, and monitoring.

Usage:
    python run_trading_system.py [--strategy STRATEGY_NAME] [--test]

Examples:
    # Run all strategies
    python run_trading_system.py

    # Run specific strategy
    python run_trading_system.py --strategy endgame_sweep

    # Test mode (dry run, no execution)
    python run_trading_system.py --test
"""

import argparse
import logging
import sys
from datetime import datetime
from typing import Optional

# Add project root to path
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.utils.config import config
from agents.utils.database import db
from agents.application.risk_manager import RiskManager
from agents.application.strategy_manager import StrategyManager
from agents.application.strategies import EndgameSweepStrategy

# Whale following strategy (optional)
if config.WHALE_TRACKING_ENABLED:
    from agents.application.strategies.whale_following import WhaleFollowingStrategy

# Use paper trading client to avoid py-clob-client dependency
try:
    from agents.polymarket.polymarket import Polymarket
except (ImportError, ModuleNotFoundError):
    from agents.polymarket.polymarket_paper import PolymarketPaper as Polymarket


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('polymarket_trading.log')
        ]
    )


def initialize_database():
    """Initialize database tables and run migrations."""
    print("Initializing database...")
    try:
        db.create_tables()

        # Run migration to add scan_requested column if needed
        from sqlalchemy import text
        session = db.get_session()
        try:
            # Check if scan_requested column exists
            result = session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='strategy_settings'
                AND column_name='scan_requested'
            """))

            if not result.fetchone():
                print("Running migration: Adding scan_requested column...")
                session.execute(text("""
                    ALTER TABLE strategy_settings
                    ADD COLUMN scan_requested BOOLEAN NOT NULL DEFAULT FALSE
                """))
                session.commit()
                print("✓ Migration completed")
        finally:
            session.close()

        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Database initialization error: {e}")
        raise


def validate_configuration():
    """Validate configuration before running."""
    print("\nValidating configuration...")

    config.print_config(mask_secrets=True)

    errors = config.validate()
    if errors:
        print("\n✗ Configuration errors found:")
        for error in errors:
            print(f"  - {error}")
        return False

    print("✓ Configuration is valid")
    return True


def initialize_components():
    """Initialize trading components."""
    print("\nInitializing components...")

    # Initialize Polymarket client
    polymarket = Polymarket()
    print("✓ Polymarket client initialized")

    # Initialize risk manager
    risk_mgr = RiskManager(polymarket)
    print("✓ Risk manager initialized")

    # Initialize strategy manager
    strategy_mgr = StrategyManager(polymarket)
    print("✓ Strategy manager initialized")

    return polymarket, risk_mgr, strategy_mgr


def register_strategies(strategy_mgr: StrategyManager, risk_mgr: RiskManager, polymarket: Polymarket):
    """Register all available strategies."""
    print("\nRegistering strategies...")

    # Endgame Sweep Strategy
    endgame_sweep = EndgameSweepStrategy(
        polymarket=polymarket,
        risk_manager=risk_mgr,
        enabled=True
    )
    strategy_mgr.register_strategy(endgame_sweep)
    print("✓ Registered: Endgame Sweep Strategy")

    # Whale Following Strategy (if enabled)
    if config.WHALE_TRACKING_ENABLED:
        whale_following = WhaleFollowingStrategy(
            polymarket=polymarket,
            risk_manager=risk_mgr,
            enabled=True
        )
        strategy_mgr.register_strategy(whale_following)
        print("✓ Registered: Whale Following Strategy")
    else:
        print("⊗ Whale Following Strategy disabled (WHALE_TRACKING_ENABLED=false)")

    # TODO: Add more strategies here
    # multi_option_arb = MultiOptionArbStrategy(...)
    # strategy_mgr.register_strategy(multi_option_arb)

    return strategy_mgr


def start_whale_discovery_background():
    """Start whale discovery service in background thread."""
    if not config.WHALE_TRACKING_ENABLED:
        return

    logger.info("Starting whale discovery service in background...")

    import threading
    from agents.application.whale.auto_discovery import start_whale_discovery_service

    # Start in daemon thread so it stops when main program exits
    discovery_thread = threading.Thread(
        target=start_whale_discovery_service,
        kwargs={
            'scan_interval_minutes': 5,  # Scan every 5 minutes
            'markets_per_scan': 50
        },
        daemon=True
    )

    discovery_thread.start()
    logger.info("✓ Whale discovery service running in background")


def run_system(strategy_name: Optional[str] = None, test_mode: bool = False):
    """
    Main system execution.

    Args:
        strategy_name: Optional specific strategy to run
        test_mode: If True, only find opportunities without executing
    """
    print("=" * 70)
    print("POLYMARKET TRADING SYSTEM")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Validate configuration
    if not validate_configuration():
        print("\n✗ Cannot proceed with invalid configuration")
        return False

    # Initialize database
    initialize_database()

    # Initialize components
    polymarket, risk_mgr, strategy_mgr = initialize_components()

    # Register strategies
    strategy_mgr = register_strategies(strategy_mgr, risk_mgr, polymarket)

    # Start whale discovery in background (if enabled)
    start_whale_discovery_background()

    # Print initial status
    print("\n" + "=" * 70)
    strategy_mgr.print_status()

    # Print risk summary
    print("\n" + "=" * 70)
    risk_mgr.print_risk_summary()

    # Run strategies
    print("\n" + "=" * 70)
    print("EXECUTING STRATEGIES")
    print("=" * 70)

    if test_mode:
        print("\n⚠️  TEST MODE: Finding opportunities only (no execution)")

    try:
        if strategy_name:
            # Run specific strategy
            print(f"\nRunning strategy: {strategy_name}")
            trades = strategy_mgr.run_strategy(strategy_name)
        else:
            # Run all strategies
            print("\nRunning all enabled strategies...")
            results = strategy_mgr.run_all_strategies()
            trades = [trade for trade_list in results.values() for trade in trade_list]

        # Summary
        print("\n" + "=" * 70)
        print("EXECUTION SUMMARY")
        print("=" * 70)
        print(f"Total trades executed: {len(trades)}")

        if trades:
            total_size = sum(float(t.size_usd) for t in trades)
            print(f"Total capital deployed: ${total_size:.2f}")
            print("\nExecuted trades:")
            for i, trade in enumerate(trades, 1):
                print(f"  {i}. {trade.strategy} - {trade.market_question[:50]}... - ${float(trade.size_usd):.2f}")

        # Print updated performance
        print("\n" + "=" * 70)
        strategy_mgr.print_performance_summary()

        print("\n" + "=" * 70)
        print("✓ Execution completed successfully")
        print("=" * 70)

        return True

    except Exception as e:
        print("\n" + "=" * 70)
        print("✗ EXECUTION ERROR")
        print("=" * 70)
        print(f"Error: {e}")
        logging.exception("Execution error")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Polymarket Trading System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--strategy',
        type=str,
        help='Specific strategy to run (e.g., endgame_sweep)'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: find opportunities without executing trades'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)

    # Run system
    success = run_system(
        strategy_name=args.strategy,
        test_mode=args.test
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
