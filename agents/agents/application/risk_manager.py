"""
Risk Management Module for Polymarket Trading.

Implements position sizing, portfolio limits, stop-losses, and other risk controls
to protect capital and ensure sustainable trading.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from agents.utils.config import config
from agents.utils.database import db, Trade

# Use paper trading client to avoid py-clob-client dependency
try:
    from agents.polymarket.polymarket import Polymarket
except (ImportError, ModuleNotFoundError):
    from agents.polymarket.polymarket_paper import PolymarketPaper as Polymarket

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Manages risk across all trading strategies.
    Enforces position limits, diversification, and loss limits.
    """

    def __init__(self, polymarket_client: Optional[Polymarket] = None):
        """
        Initialize risk manager.

        Args:
            polymarket_client: Optional Polymarket client for balance checks
        """
        self.polymarket = polymarket_client
        self.logger = logging.getLogger(__name__)

    def get_available_capital(self) -> float:
        """
        Get available trading capital in USDC.

        Returns:
            Available balance in USDC
        """
        if self.polymarket and not config.PAPER_TRADING_MODE:
            try:
                balance = self.polymarket.get_balance()
                return float(balance)
            except Exception as e:
                self.logger.error(f"Error getting balance: {e}")
                return 0.0

        # Paper trading mode - return mock balance
        # In production, track paper trading balance in database
        return 10000.0  # Mock $10k for testing

    def calculate_position_size(
        self,
        confidence: float,
        expected_profit_pct: float,
        max_position_pct: Optional[float] = None,
    ) -> float:
        """
        Calculate optimal position size using Kelly Criterion with safety margin.

        Args:
            confidence: Confidence in prediction (0-1)
            expected_profit_pct: Expected profit percentage if correct
            max_position_pct: Optional override for max position size

        Returns:
            Position size in USDC
        """
        available_capital = self.get_available_capital()

        # Kelly Criterion: f* = (bp - q) / b
        # where b = odds, p = win probability, q = 1 - p
        # Simplified for prediction markets where expected return is direct
        kelly_fraction = (confidence - (1 - confidence)) / 1.0

        # Apply safety margin (half Kelly for more conservative sizing)
        kelly_fraction = kelly_fraction * 0.5

        # Ensure within bounds
        kelly_fraction = max(0, min(kelly_fraction, 1.0))

        # Apply maximum position size limit
        max_pct = max_position_pct or config.MAX_POSITION_SIZE_PCT
        max_fraction = max_pct / 100.0

        # Take the minimum of Kelly and max allowed
        final_fraction = min(kelly_fraction, max_fraction)

        position_size = available_capital * final_fraction

        self.logger.info(
            f"Position sizing: confidence={confidence:.2f}, "
            f"kelly={kelly_fraction:.2f}, "
            f"final_fraction={final_fraction:.2f}, "
            f"size=${position_size:.2f}"
        )

        return position_size

    def get_open_positions(self) -> List[Trade]:
        """Get all currently open trades."""
        session = db.get_session()
        try:
            return session.query(Trade).filter(Trade.status == "open").all()
        finally:
            session.close()

    def get_position_count(self) -> int:
        """Get number of open positions."""
        return len(self.get_open_positions())

    def get_total_exposure(self) -> float:
        """Get total capital currently deployed in open positions."""
        open_positions = self.get_open_positions()
        total = sum(float(trade.size_usd) for trade in open_positions)
        return total

    def get_exposure_by_market(self) -> Dict[str, float]:
        """Get exposure grouped by market."""
        open_positions = self.get_open_positions()
        exposure = {}
        for trade in open_positions:
            market_id = trade.market_id
            if market_id in exposure:
                exposure[market_id] += float(trade.size_usd)
            else:
                exposure[market_id] = float(trade.size_usd)
        return exposure

    def check_diversification(self) -> Tuple[bool, str]:
        """
        Check if portfolio meets diversification requirements.

        Returns:
            (is_diversified, message)
        """
        position_count = self.get_position_count()
        min_markets = config.MIN_MARKETS_FOR_DIVERSIFICATION

        if position_count == 0:
            return True, "No open positions"

        if position_count < min_markets:
            return False, f"Only {position_count} positions, need at least {min_markets} for diversification"

        return True, f"Portfolio diversified with {position_count} positions"

    def check_position_limit(self, new_position_size: float, market_id: str) -> Tuple[bool, str]:
        """
        Check if a new position would exceed position size limits.

        Args:
            new_position_size: Size of proposed new position
            market_id: Market identifier

        Returns:
            (is_allowed, message)
        """
        available_capital = self.get_available_capital()
        max_position_size = available_capital * (config.MAX_POSITION_SIZE_PCT / 100.0)

        # Check single position limit
        if new_position_size > max_position_size:
            return False, f"Position size ${new_position_size:.2f} exceeds max ${max_position_size:.2f}"

        # Check if we already have exposure to this market
        market_exposure = self.get_exposure_by_market()
        existing_exposure = market_exposure.get(market_id, 0)
        total_market_exposure = existing_exposure + new_position_size

        if total_market_exposure > max_position_size:
            return (
                False,
                f"Total market exposure ${total_market_exposure:.2f} exceeds max ${max_position_size:.2f}"
            )

        return True, "Position size acceptable"

    def check_daily_loss_limit(self) -> Tuple[bool, str]:
        """
        Check if daily loss limit has been breached.

        Returns:
            (is_ok, message)
        """
        session = db.get_session()
        try:
            # Get today's trades
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_trades = (
                session.query(Trade)
                .filter(Trade.entry_time >= today_start)
                .filter(Trade.status.in_(["closed", "settled"]))
                .all()
            )

            if not today_trades:
                return True, "No completed trades today"

            # Calculate today's P&L
            today_pnl = sum(
                float(trade.net_profit_usd or 0) for trade in today_trades
            )

            available_capital = self.get_available_capital()
            max_daily_loss = available_capital * (config.DAILY_LOSS_LIMIT_PCT / 100.0)

            if today_pnl < -max_daily_loss:
                return False, f"Daily loss ${abs(today_pnl):.2f} exceeds limit ${max_daily_loss:.2f}"

            return True, f"Daily P&L: ${today_pnl:.2f}"

        finally:
            session.close()

    def check_weekly_loss_limit(self) -> Tuple[bool, str]:
        """
        Check if weekly loss limit has been breached.

        Returns:
            (is_ok, message)
        """
        session = db.get_session()
        try:
            # Get this week's trades
            week_start = datetime.utcnow() - timedelta(days=7)
            week_trades = (
                session.query(Trade)
                .filter(Trade.entry_time >= week_start)
                .filter(Trade.status.in_(["closed", "settled"]))
                .all()
            )

            if not week_trades:
                return True, "No completed trades this week"

            # Calculate week's P&L
            week_pnl = sum(
                float(trade.net_profit_usd or 0) for trade in week_trades
            )

            available_capital = self.get_available_capital()
            max_weekly_loss = available_capital * (config.WEEKLY_LOSS_LIMIT_PCT / 100.0)

            if week_pnl < -max_weekly_loss:
                return False, f"Weekly loss ${abs(week_pnl):.2f} exceeds limit ${max_weekly_loss:.2f}"

            return True, f"Weekly P&L: ${week_pnl:.2f}"

        finally:
            session.close()

    def validate_trade(
        self,
        market_id: str,
        position_size: float,
        expected_profit: float,
        gas_cost_estimate: float = 0.5,
    ) -> Tuple[bool, List[str]]:
        """
        Validate if a trade meets all risk management criteria.

        Args:
            market_id: Market identifier
            position_size: Proposed position size in USDC
            expected_profit: Expected profit in USDC
            gas_cost_estimate: Estimated gas cost in USDC

        Returns:
            (is_valid, list of error messages)
        """
        errors = []

        # Check position size limits
        is_ok, msg = self.check_position_limit(position_size, market_id)
        if not is_ok:
            errors.append(msg)

        # Check daily loss limit
        is_ok, msg = self.check_daily_loss_limit()
        if not is_ok:
            errors.append(msg)

        # Check weekly loss limit
        is_ok, msg = self.check_weekly_loss_limit()
        if not is_ok:
            errors.append(msg)

        # Check gas cost vs profit
        gas_pct = (gas_cost_estimate / expected_profit * 100) if expected_profit > 0 else 100
        if gas_pct > config.GAS_FEE_MAX_PCT_OF_PROFIT:
            errors.append(
                f"Gas cost {gas_pct:.1f}% of profit exceeds max {config.GAS_FEE_MAX_PCT_OF_PROFIT}%"
            )

        # Check minimum profit threshold
        profit_pct = (expected_profit / position_size * 100) if position_size > 0 else 0
        if profit_pct < config.MIN_PROFIT_THRESHOLD_PCT:
            errors.append(
                f"Expected profit {profit_pct:.2f}% below minimum {config.MIN_PROFIT_THRESHOLD_PCT}%"
            )

        is_valid = len(errors) == 0
        return is_valid, errors

    def get_risk_summary(self) -> Dict:
        """
        Get comprehensive risk summary.

        Returns:
            Dictionary with risk metrics
        """
        available_capital = self.get_available_capital()
        open_positions = self.get_open_positions()
        total_exposure = self.get_total_exposure()

        daily_ok, daily_msg = self.check_daily_loss_limit()
        weekly_ok, weekly_msg = self.check_weekly_loss_limit()
        diversification_ok, diversification_msg = self.check_diversification()

        return {
            "available_capital": available_capital,
            "total_exposure": total_exposure,
            "exposure_pct": (total_exposure / available_capital * 100) if available_capital > 0 else 0,
            "open_positions": len(open_positions),
            "positions_by_market": self.get_exposure_by_market(),
            "daily_status": {"ok": daily_ok, "message": daily_msg},
            "weekly_status": {"ok": weekly_ok, "message": weekly_msg},
            "diversification_status": {"ok": diversification_ok, "message": diversification_msg},
            "paper_trading_mode": config.PAPER_TRADING_MODE,
        }

    def print_risk_summary(self):
        """Print a formatted risk summary."""
        summary = self.get_risk_summary()

        print("\n" + "=" * 60)
        print("RISK MANAGEMENT SUMMARY")
        print("=" * 60)

        print(f"\nCapital:")
        print(f"  Available: ${summary['available_capital']:.2f}")
        print(f"  Deployed: ${summary['total_exposure']:.2f} ({summary['exposure_pct']:.1f}%)")

        print(f"\nPositions:")
        print(f"  Open: {summary['open_positions']}")
        if summary['positions_by_market']:
            print("  By market:")
            for market_id, exposure in summary['positions_by_market'].items():
                print(f"    {market_id}: ${exposure:.2f}")

        print(f"\nLoss Limits:")
        print(f"  Daily: {'✓' if summary['daily_status']['ok'] else '✗'} {summary['daily_status']['message']}")
        print(f"  Weekly: {'✓' if summary['weekly_status']['ok'] else '✗'} {summary['weekly_status']['message']}")

        print(f"\nDiversification:")
        print(f"  {'✓' if summary['diversification_status']['ok'] else '✗'} {summary['diversification_status']['message']}")

        print(f"\nMode: {'PAPER TRADING' if summary['paper_trading_mode'] else 'LIVE TRADING'}")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    # Test risk manager
    logging.basicConfig(level=logging.INFO)

    print("Testing Risk Manager...")

    # Initialize
    risk_mgr = RiskManager()

    # Print summary
    risk_mgr.print_risk_summary()

    # Test position sizing
    print("\nTesting Position Sizing:")
    for confidence in [0.6, 0.75, 0.9]:
        size = risk_mgr.calculate_position_size(
            confidence=confidence,
            expected_profit_pct=5.0
        )
        print(f"  Confidence {confidence:.0%}: ${size:.2f}")

    # Test trade validation
    print("\nTesting Trade Validation:")
    is_valid, errors = risk_mgr.validate_trade(
        market_id="test_market_123",
        position_size=500.0,
        expected_profit=10.0,
        gas_cost_estimate=0.5
    )

    if is_valid:
        print("  ✓ Trade passed validation")
    else:
        print("  ✗ Trade validation failed:")
        for error in errors:
            print(f"    - {error}")

    print("\nRisk Manager testing complete!")
