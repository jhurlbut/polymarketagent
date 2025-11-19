"""
Whale Signal Generator: Create copy-trading signals from whale activity.

This module monitors whale positions and transactions to generate trading signals.
Signals are created when high-quality whales enter or exit positions, with
appropriate confidence levels based on whale quality scores.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from agents.utils.database import db, Whale, WhalePosition, WhaleTransaction, WhaleSignal
from agents.utils.config import config

logger = logging.getLogger(__name__)


class WhaleSignalGenerator:
    """
    Generate copy-trading signals from whale activity.

    Signal types:
    - ENTRY: Whale opens new position
    - EXIT: Whale closes position
    - INCREASE: Whale adds to existing position
    - DECREASE: Whale reduces position size
    """

    def __init__(self):
        """Initialize the signal generator."""
        logger.info("Initializing Whale Signal Generator...")

        # Minimum whale quality for signal generation
        self.min_whale_quality = config.WHALE_MIN_QUALITY_SCORE

    def generate_entry_signal(
        self,
        whale_address: str,
        market_id: str,
        side: str,
        price: float,
        size_usd: Decimal,
        reasoning: Optional[str] = None
    ) -> Optional[WhaleSignal]:
        """
        Generate signal for whale entering a new position.

        Args:
            whale_address: Whale's Ethereum address
            market_id: Market ID
            side: YES or NO
            price: Entry price
            size_usd: Position size in USD
            reasoning: Optional explanation

        Returns:
            Created WhaleSignal or None if whale quality too low
        """
        session = db.get_session()
        try:
            # Get whale info
            whale = session.query(Whale).filter(
                Whale.address == whale_address.lower()
            ).first()

            if not whale:
                logger.warning(f"Cannot generate signal: whale {whale_address} not found")
                return None

            # Check if whale quality meets minimum
            if whale.quality_score < self.min_whale_quality:
                logger.debug(
                    f"Skipping signal from low-quality whale "
                    f"{whale.nickname or whale_address[:8]}... "
                    f"(score: {whale.quality_score:.2f})"
                )
                return None

            # Create signal
            signal = WhaleSignal(
                whale_address=whale_address.lower(),
                signal_type="ENTRY",
                market_id=market_id,
                side=side,
                price=Decimal(str(price)),
                size_usd=size_usd,
                confidence=whale.quality_score,
                reasoning=reasoning or f"Whale {whale.nickname or whale_address[:8]}... entered {side} position",
                status="pending",
                created_at=datetime.utcnow()
            )

            session.add(signal)
            session.commit()
            session.refresh(signal)

            logger.info(
                f"Generated ENTRY signal #{signal.id}: "
                f"whale={whale.nickname or whale_address[:8]}..., "
                f"market={market_id[:10]}..., side={side}, "
                f"confidence={whale.quality_score:.2f}"
            )

            return signal

        finally:
            session.close()

    def generate_exit_signal(
        self,
        whale_address: str,
        market_id: str,
        side: str,
        price: float,
        size_usd: Decimal,
        reasoning: Optional[str] = None
    ) -> Optional[WhaleSignal]:
        """
        Generate signal for whale exiting a position.

        Args:
            whale_address: Whale's Ethereum address
            market_id: Market ID
            side: YES or NO
            price: Exit price
            size_usd: Position size being exited
            reasoning: Optional explanation

        Returns:
            Created WhaleSignal or None if not applicable
        """
        session = db.get_session()
        try:
            whale = session.query(Whale).filter(
                Whale.address == whale_address.lower()
            ).first()

            if not whale or whale.quality_score < self.min_whale_quality:
                return None

            signal = WhaleSignal(
                whale_address=whale_address.lower(),
                signal_type="EXIT",
                market_id=market_id,
                side=side,
                price=Decimal(str(price)),
                size_usd=size_usd,
                confidence=whale.quality_score,
                reasoning=reasoning or f"Whale {whale.nickname or whale_address[:8]}... exited {side} position",
                status="pending",
                created_at=datetime.utcnow()
            )

            session.add(signal)
            session.commit()
            session.refresh(signal)

            logger.info(
                f"Generated EXIT signal #{signal.id}: "
                f"whale={whale.nickname or whale_address[:8]}..."
            )

            return signal

        finally:
            session.close()

    def get_pending_signals(
        self,
        min_confidence: Optional[float] = None,
        max_age_seconds: Optional[int] = None
    ) -> List[WhaleSignal]:
        """
        Get pending signals that haven't been executed yet.

        Args:
            min_confidence: Minimum confidence threshold
            max_age_seconds: Maximum signal age in seconds

        Returns:
            List of pending WhaleSignal objects
        """
        if min_confidence is None:
            min_confidence = self.min_whale_quality

        session = db.get_session()
        try:
            query = session.query(WhaleSignal).filter(
                WhaleSignal.status == "pending",
                WhaleSignal.confidence >= min_confidence
            )

            if max_age_seconds:
                cutoff_time = datetime.utcnow() - timedelta(seconds=max_age_seconds)
                query = query.filter(WhaleSignal.created_at >= cutoff_time)

            signals = query.order_by(
                WhaleSignal.created_at.desc()
            ).all()

            return signals

        finally:
            session.close()

    def get_copyable_signals(
        self,
        copy_delay_seconds: Optional[int] = None
    ) -> List[WhaleSignal]:
        """
        Get signals that are ready to be copied (after delay period).

        Args:
            copy_delay_seconds: Delay before copying (defaults to config)

        Returns:
            List of WhaleSignal objects ready for execution
        """
        if copy_delay_seconds is None:
            copy_delay_seconds = config.WHALE_COPY_DELAY_SECONDS

        session = db.get_session()
        try:
            # Signals must be:
            # 1. Status = pending
            # 2. Created >= delay seconds ago
            # 3. Confidence >= minimum threshold

            cutoff_time = datetime.utcnow() - timedelta(seconds=copy_delay_seconds)

            signals = session.query(WhaleSignal).filter(
                WhaleSignal.status == "pending",
                WhaleSignal.created_at <= cutoff_time,
                WhaleSignal.confidence >= self.min_whale_quality
            ).order_by(WhaleSignal.created_at).all()

            logger.info(
                f"Found {len(signals)} copyable signals "
                f"(delay: {copy_delay_seconds}s)"
            )

            return signals

        finally:
            session.close()

    def mark_signal_executed(
        self,
        signal_id: int,
        trade_id: int
    ):
        """
        Mark signal as executed.

        Args:
            signal_id: Signal ID
            trade_id: Trade ID from execution
        """
        session = db.get_session()
        try:
            signal = session.query(WhaleSignal).filter(
                WhaleSignal.id == signal_id
            ).first()

            if signal:
                signal.status = "executed"
                signal.executed_trade_id = trade_id
                signal.executed_at = datetime.utcnow()
                session.commit()

                logger.info(f"Marked signal #{signal_id} as executed (trade #{trade_id})")

        finally:
            session.close()

    def mark_signal_ignored(
        self,
        signal_id: int,
        reason: str
    ):
        """
        Mark signal as ignored.

        Args:
            signal_id: Signal ID
            reason: Reason for ignoring
        """
        session = db.get_session()
        try:
            signal = session.query(WhaleSignal).filter(
                WhaleSignal.id == signal_id
            ).first()

            if signal:
                signal.status = "ignored"
                signal.reasoning = f"{signal.reasoning} | Ignored: {reason}"
                session.commit()

                logger.info(f"Marked signal #{signal_id} as ignored: {reason}")

        finally:
            session.close()

    def expire_old_signals(
        self,
        max_age_hours: int = 24
    ) -> int:
        """
        Mark old pending signals as expired.

        Args:
            max_age_hours: Maximum age before expiration

        Returns:
            Number of signals expired
        """
        session = db.get_session()
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

            expired_count = session.query(WhaleSignal).filter(
                WhaleSignal.status == "pending",
                WhaleSignal.created_at < cutoff_time
            ).update({"status": "expired"}, synchronize_session=False)

            session.commit()

            if expired_count > 0:
                logger.info(f"Expired {expired_count} old signals")

            return expired_count

        finally:
            session.close()

    def get_signal_stats(self) -> Dict:
        """
        Get statistics about generated signals.

        Returns:
            Dict with signal statistics
        """
        session = db.get_session()
        try:
            total_signals = session.query(WhaleSignal).count()

            pending = session.query(WhaleSignal).filter(
                WhaleSignal.status == "pending"
            ).count()

            executed = session.query(WhaleSignal).filter(
                WhaleSignal.status == "executed"
            ).count()

            ignored = session.query(WhaleSignal).filter(
                WhaleSignal.status == "ignored"
            ).count()

            expired = session.query(WhaleSignal).filter(
                WhaleSignal.status == "expired"
            ).count()

            # Average confidence of pending signals
            avg_confidence_result = session.query(WhaleSignal).filter(
                WhaleSignal.status == "pending"
            ).with_entities(WhaleSignal.confidence).all()

            avg_confidence = (
                sum(c[0] for c in avg_confidence_result) / len(avg_confidence_result)
                if avg_confidence_result else 0
            )

            return {
                "total_signals": total_signals,
                "pending": pending,
                "executed": executed,
                "ignored": ignored,
                "expired": expired,
                "avg_confidence": avg_confidence,
                "execution_rate": (executed / total_signals * 100) if total_signals > 0 else 0
            }

        finally:
            session.close()

    def cleanup_old_signals(
        self,
        days_to_keep: int = 30
    ) -> int:
        """
        Delete old executed/expired signals to keep database clean.

        Args:
            days_to_keep: Number of days of history to retain

        Returns:
            Number of signals deleted
        """
        session = db.get_session()
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days_to_keep)

            deleted_count = session.query(WhaleSignal).filter(
                WhaleSignal.status.in_(["executed", "expired", "ignored"]),
                WhaleSignal.created_at < cutoff_time
            ).delete(synchronize_session=False)

            session.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old signals")

            return deleted_count

        finally:
            session.close()
