"""
Whale Scorer: Quality scoring and classification of whale traders.

This module implements algorithms to score whales based on their trading performance,
consistency, timing, and risk management. The quality score helps identify which
whales are worth copying (smart money) vs those to avoid (dumb money).
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from agents.utils.database import db, Whale, WhaleTransaction
from agents.utils.config import config

logger = logging.getLogger(__name__)


class WhaleScorer:
    """
    Calculate quality scores for whale traders.

    Scoring factors:
    - Win Rate (40%): Historical percentage of winning trades
    - Consistency (20%): Profit consistency across time periods
    - Timing (15%): How early whale enters before price movement
    - Selection (15%): Market specialization and category focus
    - Risk Management (10%): Max drawdown and position sizing
    """

    def __init__(self):
        """Initialize the whale scorer."""
        logger.info("Initializing Whale Scorer...")

        # Scoring weights
        self.weights = {
            'win_rate': 0.40,
            'consistency': 0.20,
            'timing': 0.15,
            'selection': 0.15,
            'risk': 0.10
        }

    def calculate_quality_score(self, whale_address: str) -> float:
        """
        Calculate composite quality score for a whale.

        Args:
            whale_address: Ethereum address of whale

        Returns:
            Quality score from 0.0 to 1.0
        """
        session = db.get_session()
        try:
            whale = session.query(Whale).filter(
                Whale.address == whale_address.lower()
            ).first()

            if not whale:
                logger.warning(f"Whale {whale_address} not found for scoring")
                return 0.0

            # Need minimum trade history for scoring
            if whale.total_trades < 10:
                logger.debug(f"Whale {whale_address[:8]}... has insufficient trades ({whale.total_trades})")
                return 0.0

            # Calculate individual factor scores
            win_rate_score = self._score_win_rate(whale)
            consistency_score = self._score_consistency(whale_address)
            timing_score = self._score_timing(whale_address)
            selection_score = self._score_market_selection(whale_address)
            risk_score = self._score_risk_management(whale)

            # Weighted composite score
            quality_score = (
                win_rate_score * self.weights['win_rate'] +
                consistency_score * self.weights['consistency'] +
                timing_score * self.weights['timing'] +
                selection_score * self.weights['selection'] +
                risk_score * self.weights['risk']
            )

            logger.info(
                f"Whale {whale.nickname or whale_address[:8]}... scored: "
                f"{quality_score:.3f} (WR:{win_rate_score:.2f}, "
                f"C:{consistency_score:.2f}, T:{timing_score:.2f}, "
                f"S:{selection_score:.2f}, R:{risk_score:.2f})"
            )

            return quality_score

        finally:
            session.close()

    def _score_win_rate(self, whale: Whale) -> float:
        """
        Score based on win rate.

        Perfect score (1.0) at 85%+ win rate.
        Scales linearly from 0.0 (0% win rate) to 1.0 (85%+).

        Args:
            whale: Whale object

        Returns:
            Score from 0.0 to 1.0
        """
        if whale.total_trades == 0:
            return 0.0

        win_rate = whale.win_rate / 100.0  # Convert percentage to decimal

        # Score: perfect at 85%+, linear below
        score = min(win_rate / 0.85, 1.0)

        return score

    def _score_consistency(self, whale_address: str) -> float:
        """
        Score based on profit consistency over time.

        Measures how consistently profitable the whale is across
        different time periods (weekly, monthly).

        Args:
            whale_address: Whale address

        Returns:
            Score from 0.0 to 1.0
        """
        session = db.get_session()
        try:
            # Check last 3 months of activity (simplified version)
            # In production, you'd analyze weekly/monthly P&L patterns

            # Get transactions from last 90 days
            cutoff_time = datetime.utcnow() - timedelta(days=90)

            transactions = session.query(WhaleTransaction).filter(
                WhaleTransaction.whale_address == whale_address.lower(),
                WhaleTransaction.timestamp >= cutoff_time
            ).order_by(WhaleTransaction.timestamp).all()

            if len(transactions) < 10:
                return 0.5  # Neutral score for insufficient data

            # Simplified consistency: check if majority of time periods are profitable
            # Split into weekly buckets
            weekly_profits = {}
            for tx in transactions:
                week_key = tx.timestamp.strftime("%Y-W%W")
                if week_key not in weekly_profits:
                    weekly_profits[week_key] = 0.0

                # Estimate profit (simplified - in production would calculate actual P&L)
                if tx.transaction_type == "SELL":
                    weekly_profits[week_key] += float(tx.size_usd)
                else:
                    weekly_profits[week_key] -= float(tx.size_usd)

            if not weekly_profits:
                return 0.5

            # Calculate percentage of profitable weeks
            profitable_weeks = sum(1 for p in weekly_profits.values() if p > 0)
            consistency_pct = profitable_weeks / len(weekly_profits)

            return consistency_pct

        finally:
            session.close()

    def _score_timing(self, whale_address: str) -> float:
        """
        Score based on entry timing quality.

        Measures how early whale enters positions before price moves.
        Good whales enter early, bad whales chase price.

        Args:
            whale_address: Whale address

        Returns:
            Score from 0.0 to 1.0
        """
        # This requires analyzing price movement after whale entry
        # Simplified version: return neutral score
        # In production, you'd track:
        # - Time between whale entry and major price movement
        # - Whether whale is early (good) or late (bad)
        # - Counter-trend vs momentum following behavior

        # For now, return neutral score
        # TODO: Implement full timing analysis
        return 0.6

    def _score_market_selection(self, whale_address: str) -> float:
        """
        Score based on market selection quality.

        Whales that specialize in specific categories (politics, crypto)
        tend to perform better than those trading randomly.

        Args:
            whale_address: Whale address

        Returns:
            Score from 0.0 to 1.0
        """
        session = db.get_session()
        try:
            whale = session.query(Whale).filter(
                Whale.address == whale_address.lower()
            ).first()

            if not whale:
                return 0.5

            # If whale has identified specialization, good sign
            if whale.specialization:
                return 0.8

            # Otherwise neutral score
            # TODO: Analyze transaction history to detect specialization patterns
            return 0.5

        finally:
            session.close()

    def _score_risk_management(self, whale: Whale) -> float:
        """
        Score based on risk management quality.

        Looks at:
        - Max drawdown (lower is better)
        - Position sizing consistency
        - Diversification

        Args:
            whale: Whale object

        Returns:
            Score from 0.0 to 1.0
        """
        # Simplified version: use Sharpe ratio if available
        if whale.sharpe_ratio is not None and whale.sharpe_ratio > 0:
            # Sharpe > 2.0 = excellent, 1.0 = good, < 0.5 = poor
            score = min(whale.sharpe_ratio / 2.0, 1.0)
            return score

        # Default: neutral score
        # TODO: Calculate actual max drawdown from transaction history
        return 0.6

    def classify_whale(self, quality_score: float) -> str:
        """
        Classify whale based on quality score.

        Args:
            quality_score: Calculated quality score (0-1)

        Returns:
            Whale type: 'smart_money', 'neutral', or 'dumb_money'
        """
        if quality_score >= 0.75:
            return "smart_money"
        elif quality_score >= 0.50:
            return "neutral"
        else:
            return "dumb_money"

    def update_whale_score(self, whale_address: str) -> Optional[float]:
        """
        Calculate and update whale's quality score in database.

        Args:
            whale_address: Ethereum address of whale

        Returns:
            Updated quality score, or None if whale not found
        """
        quality_score = self.calculate_quality_score(whale_address)
        whale_type = self.classify_whale(quality_score)

        session = db.get_session()
        try:
            whale = session.query(Whale).filter(
                Whale.address == whale_address.lower()
            ).first()

            if not whale:
                return None

            whale.quality_score = quality_score
            whale.whale_type = whale_type
            whale.updated_at = datetime.utcnow()

            session.commit()

            logger.info(
                f"Updated whale {whale.nickname or whale_address[:8]}...: "
                f"score={quality_score:.3f}, type={whale_type}"
            )

            return quality_score

        finally:
            session.close()

    def score_all_whales(self) -> Dict[str, float]:
        """
        Calculate and update scores for all whales in database.

        Returns:
            Dict mapping addresses to quality scores
        """
        logger.info("Scoring all whales...")

        session = db.get_session()
        try:
            all_whales = session.query(Whale).all()

            logger.info(f"Found {len(all_whales)} whales to score")

            scores = {}
            for whale in all_whales:
                try:
                    score = self.update_whale_score(whale.address)
                    if score is not None:
                        scores[whale.address] = score
                except Exception as e:
                    logger.error(f"Error scoring whale {whale.address}: {e}")

            logger.info(f"Successfully scored {len(scores)} whales")

            # Log distribution
            if scores:
                smart_money = sum(1 for s in scores.values() if s >= 0.75)
                neutral = sum(1 for s in scores.values() if 0.50 <= s < 0.75)
                dumb_money = sum(1 for s in scores.values() if s < 0.50)

                logger.info(
                    f"Score distribution: {smart_money} smart money, "
                    f"{neutral} neutral, {dumb_money} dumb money"
                )

            return scores

        finally:
            session.close()

    def get_copyable_whales(self, min_quality: float = None) -> List[Whale]:
        """
        Get list of whales worth copying.

        Args:
            min_quality: Minimum quality score (defaults to config value)

        Returns:
            List of high-quality Whale objects
        """
        if min_quality is None:
            min_quality = config.WHALE_MIN_QUALITY_SCORE

        session = db.get_session()
        try:
            whales = session.query(Whale).filter(
                Whale.is_tracked == True,
                Whale.quality_score >= min_quality
            ).order_by(Whale.quality_score.desc()).all()

            logger.info(
                f"Found {len(whales)} copyable whales "
                f"(min quality: {min_quality:.2f})"
            )

            return whales

        finally:
            session.close()
