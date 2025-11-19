"""
Automatic Whale Discovery via Polymarket CLOB API.

This module monitors Polymarket markets in real-time to automatically discover
and track whale traders based on their transaction volumes.

Architecture:
1. Poll Polymarket CLOB API for market trades
2. Identify large transactions (>$5k default)
3. Track trader addresses and build profiles
4. Score traders based on performance
5. Auto-generate signals for high-quality whales
"""

import logging
import time
import requests
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

from agents.utils.database import db, Whale, WhaleTransaction
from agents.utils.config import config
from agents.application.whale import WhaleMonitor, WhaleScorer, WhaleSignalGenerator

logger = logging.getLogger(__name__)


class PolymarketWhaleDiscovery:
    """
    Automatic whale discovery from Polymarket CLOB API.

    Monitors all active markets for large trades and automatically
    identifies, scores, and tracks successful traders.
    """

    def __init__(
        self,
        min_trade_size_usd: float = None,
        min_total_volume_usd: float = None,
        min_trades_for_scoring: int = 10
    ):
        """
        Initialize whale discovery service.

        Args:
            min_trade_size_usd: Minimum trade size to consider (default: $500)
            min_total_volume_usd: Minimum total volume to track (default: from config)
            min_trades_for_scoring: Minimum trades before scoring whale
        """
        self.whale_monitor = WhaleMonitor()
        self.whale_scorer = WhaleScorer()
        self.signal_generator = WhaleSignalGenerator()

        # Configuration
        self.min_trade_size_usd = min_trade_size_usd or 500.0
        self.min_total_volume_usd = min_total_volume_usd or config.WHALE_MIN_VOLUME_USD
        self.min_trades_for_scoring = min_trades_for_scoring

        # Polymarket CLOB API
        self.clob_api_base = "https://clob.polymarket.com"

        # Track addresses we've seen
        self.tracked_addresses: Set[str] = set()

        # Track trader stats (in-memory cache)
        self.trader_stats: Dict[str, Dict] = defaultdict(lambda: {
            'total_volume': 0.0,
            'trade_count': 0,
            'first_seen': datetime.utcnow(),
            'last_seen': datetime.utcnow(),
            'markets_traded': set()
        })

        logger.info(
            f"Whale Discovery initialized: "
            f"min_trade=${self.min_trade_size_usd:,.0f}, "
            f"min_volume=${self.min_total_volume_usd:,.0f}"
        )

    def get_market_trades(
        self,
        token_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get recent trades for a specific market token.

        Args:
            token_id: Polymarket token ID
            limit: Max number of trades to fetch

        Returns:
            List of trade dictionaries
        """
        try:
            url = f"{self.clob_api_base}/trades"
            params = {
                'id': token_id,
                'limit': limit
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                trades = response.json()
                logger.debug(f"Fetched {len(trades)} trades for token {token_id[:8]}...")
                return trades
            else:
                logger.warning(f"Failed to fetch trades: HTTP {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error fetching market trades: {e}")
            return []

    def get_orderbook(self, token_id: str) -> Dict:
        """
        Get current orderbook for a market.

        Args:
            token_id: Polymarket token ID

        Returns:
            Orderbook data with bids/asks
        """
        try:
            url = f"{self.clob_api_base}/book"
            params = {'token_id': token_id}

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch orderbook: HTTP {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"Error fetching orderbook: {e}")
            return {}

    def process_trade(self, trade: Dict, market_id: str) -> Optional[str]:
        """
        Process a single trade and update trader stats.

        Args:
            trade: Trade data from CLOB API
            market_id: Market ID this trade belongs to

        Returns:
            Trader address if trade is whale-sized, None otherwise
        """
        try:
            # Extract trade details
            # Note: Actual field names may vary - adjust based on real API response
            maker = trade.get('maker', '').lower()
            taker = trade.get('taker', '').lower()
            size = float(trade.get('size', 0))
            price = float(trade.get('price', 0))

            # Calculate USD value (assuming price is in cents)
            trade_value_usd = size * price

            # Check if trade is large enough
            if trade_value_usd < self.min_trade_size_usd:
                return None

            # Update stats for both maker and taker
            for address in [maker, taker]:
                if not address or address == '0x' + '0'*40:
                    continue

                stats = self.trader_stats[address]
                stats['total_volume'] += trade_value_usd
                stats['trade_count'] += 1
                stats['last_seen'] = datetime.utcnow()
                stats['markets_traded'].add(market_id)

                logger.debug(
                    f"Trader {address[:8]}...: "
                    f"${trade_value_usd:,.0f} trade, "
                    f"total: ${stats['total_volume']:,.0f}"
                )

                # Check if this trader qualifies as a whale
                if stats['total_volume'] >= self.min_total_volume_usd:
                    return address

            return None

        except Exception as e:
            logger.error(f"Error processing trade: {e}")
            return None

    def create_or_update_whale(self, address: str) -> Optional[Whale]:
        """
        Create or update whale record from tracked stats.

        Args:
            address: Trader address

        Returns:
            Whale object if created/updated
        """
        stats = self.trader_stats[address]

        # Check if whale already exists
        whale = self.whale_monitor.get_whale(address)

        if whale:
            # Update existing whale
            logger.debug(f"Updating existing whale: {whale.nickname or address[:8]}...")

            self.whale_monitor.update_whale_stats(
                address=address,
                total_volume_usd=Decimal(str(stats['total_volume'])),
                total_trades=stats['trade_count']
            )

            return whale

        else:
            # Create new whale
            logger.info(
                f"🐋 NEW WHALE DISCOVERED: {address[:8]}... "
                f"(volume: ${stats['total_volume']:,.0f}, "
                f"trades: {stats['trade_count']})"
            )

            whale = self.whale_monitor.add_whale(
                address=address,
                nickname=None,  # Can be set manually later
                quality_score=0.0,  # Will be scored when enough data
                whale_type="neutral",
                track=False  # Don't track until scored
            )

            self.tracked_addresses.add(address)

            return whale

    def score_whale_if_ready(self, address: str) -> Optional[float]:
        """
        Score whale if they have enough trade history.

        Args:
            address: Whale address

        Returns:
            Quality score if calculated, None otherwise
        """
        stats = self.trader_stats[address]

        # Need minimum trades for reliable scoring
        if stats['trade_count'] < self.min_trades_for_scoring:
            logger.debug(
                f"Whale {address[:8]}... needs more trades for scoring "
                f"({stats['trade_count']}/{self.min_trades_for_scoring})"
            )
            return None

        # Calculate quality score
        quality_score = self.whale_scorer.update_whale_score(address)

        if quality_score:
            whale = self.whale_monitor.get_whale(address)

            logger.info(
                f"📊 WHALE SCORED: {whale.nickname or address[:8]}... "
                f"quality={quality_score:.2f} ({whale.whale_type})"
            )

            # Auto-track if quality is high enough
            if quality_score >= config.WHALE_MIN_QUALITY_SCORE:
                session = db.get_session()
                try:
                    whale = session.query(Whale).filter(
                        Whale.address == address.lower()
                    ).first()

                    if whale and not whale.is_tracked:
                        whale.is_tracked = True
                        session.commit()

                        logger.info(
                            f"✅ AUTO-TRACKING WHALE: {whale.nickname or address[:8]}... "
                            f"(quality {quality_score:.2f})"
                        )
                finally:
                    session.close()

            return quality_score

        return None

    def scan_market_for_whales(self, market_id: str, token_ids: List[str]) -> int:
        """
        Scan a single market for whale activity.

        Args:
            market_id: Market ID to scan
            token_ids: Token IDs for this market (YES/NO)

        Returns:
            Number of potential whales found
        """
        whales_found = 0

        for token_id in token_ids:
            # Get recent trades
            trades = self.get_market_trades(token_id, limit=50)

            for trade in trades:
                # Process trade and check if whale-sized
                whale_address = self.process_trade(trade, market_id)

                if whale_address:
                    # Create or update whale
                    whale = self.create_or_update_whale(whale_address)

                    if whale:
                        # Try to score if ready
                        self.score_whale_if_ready(whale_address)
                        whales_found += 1

        return whales_found

    def scan_all_markets(
        self,
        limit: int = 100,
        min_volume_24h: float = 10000.0
    ) -> Dict[str, int]:
        """
        Scan all active markets for whale activity.

        Args:
            limit: Max markets to scan per run
            min_volume_24h: Only scan markets with >$X 24h volume

        Returns:
            Dict with scan statistics
        """
        logger.info("=" * 70)
        logger.info("SCANNING MARKETS FOR WHALE ACTIVITY")
        logger.info("=" * 70)

        try:
            # Get active markets from Polymarket
            from agents.polymarket.polymarket_paper import PolymarketPaper
            polymarket = PolymarketPaper()

            markets = polymarket.get_all_tradeable_markets()
            logger.info(f"Found {len(markets)} active markets")

            # Filter high-volume markets
            high_volume_markets = [
                m for m in markets
                if hasattr(m, 'volume24hr') and float(m.volume24hr or 0) >= min_volume_24h
            ]

            logger.info(
                f"Scanning {len(high_volume_markets)} high-volume markets "
                f"(>${min_volume_24h:,.0f}+ 24h volume)"
            )

            # Scan markets
            total_whales = 0
            markets_scanned = 0

            for market in high_volume_markets[:limit]:
                try:
                    # Get token IDs for this market
                    token_ids = []
                    if hasattr(market, 'clob_token_ids'):
                        token_ids = market.clob_token_ids
                    elif hasattr(market, 'clobTokenIds'):
                        token_ids = market.clobTokenIds

                    if not token_ids:
                        continue

                    # Scan market
                    whales = self.scan_market_for_whales(market.market_id, token_ids)
                    total_whales += whales
                    markets_scanned += 1

                    if whales > 0:
                        logger.info(
                            f"  Market {market.market_id[:10]}...: "
                            f"found {whales} whale trade(s)"
                        )

                except Exception as e:
                    logger.error(f"Error scanning market {market.market_id}: {e}")
                    continue

            # Summary
            stats = {
                'markets_scanned': markets_scanned,
                'whale_trades_found': total_whales,
                'unique_whales_tracked': len(self.tracked_addresses),
                'total_traders_seen': len(self.trader_stats)
            }

            logger.info("=" * 70)
            logger.info("SCAN COMPLETE")
            logger.info("=" * 70)
            logger.info(f"Markets scanned: {stats['markets_scanned']}")
            logger.info(f"Whale trades found: {stats['whale_trades_found']}")
            logger.info(f"Unique whales: {stats['unique_whales_tracked']}")
            logger.info(f"Total traders seen: {stats['total_traders_seen']}")

            return stats

        except Exception as e:
            logger.error(f"Error in market scan: {e}", exc_info=True)
            return {}

    def run_continuous_discovery(
        self,
        scan_interval_seconds: int = 300,
        markets_per_scan: int = 50
    ):
        """
        Run continuous whale discovery in background.

        Args:
            scan_interval_seconds: Seconds between scans (default 5 minutes)
            markets_per_scan: Markets to scan per run
        """
        logger.info("=" * 70)
        logger.info("STARTING CONTINUOUS WHALE DISCOVERY")
        logger.info("=" * 70)
        logger.info(f"Scan interval: {scan_interval_seconds}s ({scan_interval_seconds//60} minutes)")
        logger.info(f"Markets per scan: {markets_per_scan}")
        logger.info("=" * 70)

        scan_count = 0

        while True:
            try:
                scan_count += 1
                logger.info(f"\n🔍 Scan #{scan_count} starting...")

                # Scan markets
                stats = self.scan_all_markets(limit=markets_per_scan)

                # Log whale summary
                monitor = WhaleMonitor()
                whale_stats = monitor.get_summary_stats()

                logger.info(f"\n📊 Current whale database:")
                logger.info(f"  Total whales: {whale_stats['total_whales']}")
                logger.info(f"  Tracked: {whale_stats['tracked_whales']}")
                logger.info(f"  Smart money: {whale_stats['smart_money_whales']}")

                # Wait for next scan
                logger.info(f"\n💤 Sleeping {scan_interval_seconds}s until next scan...")
                time.sleep(scan_interval_seconds)

            except KeyboardInterrupt:
                logger.info("\n\n⚠️  Stopping whale discovery (KeyboardInterrupt)")
                break

            except Exception as e:
                logger.error(f"Error in discovery loop: {e}", exc_info=True)
                logger.info(f"Retrying in {scan_interval_seconds}s...")
                time.sleep(scan_interval_seconds)


def start_whale_discovery_service(
    scan_interval_minutes: int = 5,
    markets_per_scan: int = 50
):
    """
    Start whale discovery service (for use in trading system).

    Args:
        scan_interval_minutes: Minutes between scans
        markets_per_scan: Markets to scan per run
    """
    logger.info("Starting Whale Discovery Service...")

    discovery = PolymarketWhaleDiscovery()

    discovery.run_continuous_discovery(
        scan_interval_seconds=scan_interval_minutes * 60,
        markets_per_scan=markets_per_scan
    )


if __name__ == "__main__":
    # Test whale discovery
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "=" * 70)
    print("POLYMARKET AUTOMATIC WHALE DISCOVERY")
    print("=" * 70)
    print("\nThis service will:")
    print("  1. Scan high-volume Polymarket markets")
    print("  2. Identify traders making >$500 trades")
    print("  3. Track traders with >$50k total volume")
    print("  4. Score whales after 10+ trades")
    print("  5. Auto-track whales with quality >= 0.70")
    print("\n" + "=" * 70)

    response = input("\nStart continuous discovery? (y/n): ")

    if response.lower() == 'y':
        discovery = PolymarketWhaleDiscovery()
        discovery.run_continuous_discovery(
            scan_interval_seconds=60,  # 1 minute for testing
            markets_per_scan=20
        )
    else:
        # One-time scan
        print("\nRunning single scan...")
        discovery = PolymarketWhaleDiscovery()
        stats = discovery.scan_all_markets(limit=20)
        print(f"\n✓ Scan complete: {stats}")
