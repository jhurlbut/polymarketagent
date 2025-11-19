"""
Whale Monitor: Real-time tracking of large trader activity on Polymarket.

This module monitors blockchain transactions and orderbook activity to identify
and track "whale" traders - high-volume participants whose trades may provide
valuable trading signals.
"""

import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from decimal import Decimal

from agents.utils.database import db, Whale, WhalePosition, WhaleTransaction
from agents.utils.config import config

logger = logging.getLogger(__name__)


class WhaleMonitor:
    """
    Monitor and track whale trader activity on Polymarket.

    Responsibilities:
    - Load and maintain list of tracked whales
    - Identify new whale addresses from large transactions
    - Update whale positions and transaction history
    - Provide query interface for whale data
    """

    def __init__(self):
        """Initialize the whale monitor."""
        self.tracked_whales: Dict[str, Whale] = {}
        self.tracked_addresses: Set[str] = set()

        logger.info("Initializing Whale Monitor...")
        self.load_tracked_whales()

    def load_tracked_whales(self):
        """Load whales we're actively tracking from database."""
        session = db.get_session()
        try:
            whales = session.query(Whale).filter(
                Whale.is_tracked == True
            ).all()

            for whale in whales:
                addr_lower = whale.address.lower()
                self.tracked_whales[addr_lower] = whale
                self.tracked_addresses.add(addr_lower)

            logger.info(f"Loaded {len(self.tracked_whales)} tracked whales")

            if len(self.tracked_whales) > 0:
                # Log some stats
                smart_money = sum(1 for w in self.tracked_whales.values()
                                 if w.whale_type == "smart_money")
                avg_quality = sum(w.quality_score for w in self.tracked_whales.values()) / len(self.tracked_whales)
                logger.info(
                    f"  {smart_money} smart money whales, "
                    f"avg quality score: {avg_quality:.2f}"
                )

        finally:
            session.close()

    def get_whale(self, address: str) -> Optional[Whale]:
        """
        Get whale record by address.

        Args:
            address: Ethereum address of whale

        Returns:
            Whale object if found, None otherwise
        """
        addr_lower = address.lower()

        # Check in-memory cache first
        if addr_lower in self.tracked_whales:
            return self.tracked_whales[addr_lower]

        # Query database
        session = db.get_session()
        try:
            whale = session.query(Whale).filter(
                Whale.address == addr_lower
            ).first()
            return whale
        finally:
            session.close()

    def is_tracked_whale(self, address: str) -> bool:
        """
        Check if address is a tracked whale.

        Args:
            address: Ethereum address to check

        Returns:
            True if address is tracked whale
        """
        return address.lower() in self.tracked_addresses

    def add_whale(
        self,
        address: str,
        nickname: Optional[str] = None,
        quality_score: float = 0.0,
        whale_type: str = "neutral",
        track: bool = False
    ) -> Whale:
        """
        Add a new whale to the database.

        Args:
            address: Ethereum address
            nickname: Optional friendly name
            quality_score: Initial quality score (0-1)
            whale_type: Classification (smart_money, neutral, dumb_money)
            track: Whether to actively track this whale

        Returns:
            Created Whale object
        """
        session = db.get_session()
        try:
            whale = Whale(
                address=address.lower(),
                nickname=nickname,
                quality_score=quality_score,
                whale_type=whale_type,
                is_tracked=track,
                first_seen_at=datetime.utcnow(),
                last_activity_at=datetime.utcnow()
            )

            session.add(whale)
            session.commit()
            session.refresh(whale)

            if track:
                # Add to tracked set
                self.tracked_whales[address.lower()] = whale
                self.tracked_addresses.add(address.lower())

            logger.info(
                f"Added new whale: {nickname or address[:8]}... "
                f"(quality: {quality_score:.2f}, type: {whale_type})"
            )

            return whale

        finally:
            session.close()

    def update_whale_stats(
        self,
        address: str,
        total_volume_usd: Optional[Decimal] = None,
        total_trades: Optional[int] = None,
        winning_trades: Optional[int] = None,
        quality_score: Optional[float] = None,
        whale_type: Optional[str] = None
    ):
        """
        Update whale statistics.

        Args:
            address: Whale address
            total_volume_usd: Total trading volume
            total_trades: Number of trades
            winning_trades: Number of winning trades
            quality_score: Updated quality score
            whale_type: Updated classification
        """
        session = db.get_session()
        try:
            whale = session.query(Whale).filter(
                Whale.address == address.lower()
            ).first()

            if not whale:
                logger.warning(f"Whale {address} not found for stats update")
                return

            # Update fields if provided
            if total_volume_usd is not None:
                whale.total_volume_usd = total_volume_usd
            if total_trades is not None:
                whale.total_trades = total_trades
            if winning_trades is not None:
                whale.winning_trades = winning_trades
                whale.losing_trades = total_trades - winning_trades if total_trades else 0
                if total_trades > 0:
                    whale.win_rate = (winning_trades / total_trades) * 100
            if quality_score is not None:
                whale.quality_score = quality_score
            if whale_type is not None:
                whale.whale_type = whale_type

            whale.last_activity_at = datetime.utcnow()
            whale.updated_at = datetime.utcnow()

            session.commit()

            # Update in-memory cache if tracked
            if whale.address in self.tracked_whales:
                session.refresh(whale)
                self.tracked_whales[whale.address] = whale

        finally:
            session.close()

    def get_whale_positions(self, address: str, status: str = "open") -> List[WhalePosition]:
        """
        Get whale's current positions.

        Args:
            address: Whale address
            status: Position status filter (open, closed, all)

        Returns:
            List of WhalePosition objects
        """
        session = db.get_session()
        try:
            query = session.query(WhalePosition).filter(
                WhalePosition.whale_address == address.lower()
            )

            if status != "all":
                query = query.filter(WhalePosition.status == status)

            positions = query.order_by(WhalePosition.entry_time.desc()).all()
            return positions

        finally:
            session.close()

    def get_whale_transactions(
        self,
        address: str,
        hours_back: int = 24
    ) -> List[WhaleTransaction]:
        """
        Get recent transactions for a whale.

        Args:
            address: Whale address
            hours_back: How many hours of history to fetch

        Returns:
            List of WhaleTransaction objects
        """
        session = db.get_session()
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

            transactions = session.query(WhaleTransaction).filter(
                WhaleTransaction.whale_address == address.lower(),
                WhaleTransaction.timestamp >= cutoff_time
            ).order_by(WhaleTransaction.timestamp.desc()).all()

            return transactions

        finally:
            session.close()

    def get_top_whales(self, limit: int = 10) -> List[Whale]:
        """
        Get top whales by quality score.

        Args:
            limit: Maximum number of whales to return

        Returns:
            List of top-quality Whale objects
        """
        session = db.get_session()
        try:
            whales = session.query(Whale).filter(
                Whale.is_tracked == True
            ).order_by(
                Whale.quality_score.desc()
            ).limit(limit).all()

            return whales

        finally:
            session.close()

    def find_whales_by_market(self, market_id: str) -> List[Dict]:
        """
        Find whales with positions in a specific market.

        Args:
            market_id: Market ID to search

        Returns:
            List of dicts with whale and position info
        """
        session = db.get_session()
        try:
            # Join whales and positions
            results = session.query(Whale, WhalePosition).join(
                WhalePosition,
                Whale.address == WhalePosition.whale_address
            ).filter(
                WhalePosition.market_id == market_id,
                WhalePosition.status == "open"
            ).all()

            whale_positions = []
            for whale, position in results:
                whale_positions.append({
                    "whale": whale,
                    "position": position,
                    "whale_quality": whale.quality_score,
                    "whale_type": whale.whale_type,
                    "position_size_usd": float(position.position_size_usd),
                    "side": position.side
                })

            # Sort by whale quality (highest first)
            whale_positions.sort(key=lambda x: x['whale_quality'], reverse=True)

            return whale_positions

        finally:
            session.close()

    def get_summary_stats(self) -> Dict:
        """
        Get summary statistics for all tracked whales.

        Returns:
            Dict with summary stats
        """
        session = db.get_session()
        try:
            total_whales = session.query(Whale).count()
            tracked_whales = session.query(Whale).filter(Whale.is_tracked == True).count()

            smart_money = session.query(Whale).filter(
                Whale.whale_type == "smart_money",
                Whale.is_tracked == True
            ).count()

            avg_quality = session.query(Whale).filter(
                Whale.is_tracked == True
            ).with_entities(Whale.quality_score).all()

            avg_quality_score = sum(q[0] for q in avg_quality) / len(avg_quality) if avg_quality else 0

            open_positions = session.query(WhalePosition).filter(
                WhalePosition.status == "open"
            ).count()

            return {
                "total_whales": total_whales,
                "tracked_whales": tracked_whales,
                "smart_money_whales": smart_money,
                "avg_quality_score": avg_quality_score,
                "open_positions": open_positions
            }

        finally:
            session.close()

    def reload_whales(self):
        """Reload tracked whales from database."""
        self.tracked_whales.clear()
        self.tracked_addresses.clear()
        self.load_tracked_whales()
        logger.info("Reloaded tracked whales from database")
