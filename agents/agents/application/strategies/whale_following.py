"""
Whale Following Trading Strategy for Polymarket.

Monitors high-quality "whale" traders and copies their positions with appropriate
delays and position sizing. Uses quality scoring to identify smart money vs dumb money.

Strategy Overview:
- Track whales with quality scores above threshold (default 0.70)
- Wait for copy delay (default 5 minutes) before executing
- Size positions using Kelly Criterion based on whale quality
- Exit when whale exits or independent criteria are met

Key Features:
1. Multi-factor whale quality scoring (win rate, consistency, timing, etc.)
2. Delayed execution to avoid front-running detection
3. Intelligent position sizing based on whale confidence
4. Risk-adjusted copying (never copy more than whale's relative size)

Whale Quality Factors:
- Win Rate (40%): Historical percentage of winning trades
- Consistency (20%): Profit consistency across time periods
- Timing (15%): How early whale enters before price movement
- Selection (15%): Market specialization and category focus
- Risk Management (10%): Max drawdown and position sizing
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from agents.application.strategy_manager import TradingStrategy
from agents.application.risk_manager import RiskManager
from agents.utils.config import config
from agents.utils.database import db, Trade, Whale, WhaleSignal

# Import whale tracking modules
from agents.application.whale import WhaleMonitor, WhaleScorer, WhaleSignalGenerator

# Use paper trading client to avoid py-clob-client dependency
try:
    from agents.polymarket.polymarket import Polymarket, SimpleMarket
except (ImportError, ModuleNotFoundError):
    from agents.polymarket.polymarket_paper import PolymarketPaper as Polymarket
    from agents.utils.objects import SimpleMarket

logger = logging.getLogger(__name__)


class WhaleFollowingStrategy(TradingStrategy):
    """
    Whale Following: Copy trades from high-quality whale traders.
    """

    def __init__(
        self,
        polymarket: Polymarket,
        risk_manager: RiskManager,
        enabled: bool = True,
        min_whale_quality: float = None,
        copy_delay_seconds: int = None,
        max_position_pct: float = None
    ):
        """
        Initialize Whale Following strategy.

        Args:
            polymarket: Polymarket client
            risk_manager: Risk manager instance
            enabled: Whether strategy is enabled
            min_whale_quality: Minimum whale quality score (default from config)
            copy_delay_seconds: Delay before copying trades (default from config)
            max_position_pct: Max position size as % of bankroll (default from config)
        """
        super().__init__("whale_following", polymarket, risk_manager, enabled)

        # Initialize whale tracking components
        self.whale_monitor = WhaleMonitor()
        self.whale_scorer = WhaleScorer()
        self.signal_generator = WhaleSignalGenerator()

        # Configuration
        self.min_whale_quality = min_whale_quality or config.WHALE_MIN_QUALITY_SCORE
        self.copy_delay_seconds = copy_delay_seconds or config.WHALE_COPY_DELAY_SECONDS
        self.max_position_pct = max_position_pct or config.WHALE_MAX_POSITION_PCT

        self.logger.info(
            f"Whale Following initialized: "
            f"min quality {self.min_whale_quality:.2f}, "
            f"copy delay {self.copy_delay_seconds}s, "
            f"max position {self.max_position_pct}%"
        )

        # Log tracked whales
        stats = self.whale_monitor.get_summary_stats()
        self.logger.info(
            f"Tracking {stats['tracked_whales']} whales "
            f"({stats['smart_money_whales']} smart money, "
            f"avg quality: {stats['avg_quality_score']:.2f})"
        )

    def calculate_kelly_position_size(
        self,
        whale_quality: float,
        whale_position_size_usd: float,
        bankroll: float
    ) -> float:
        """
        Calculate position size using Kelly Criterion.

        Kelly formula: f = (p * b - q) / b
        where:
        - f = fraction of bankroll to bet
        - p = probability of winning (whale quality score)
        - q = probability of losing (1 - p)
        - b = odds received on bet (assume 1:1 for simplicity)

        Args:
            whale_quality: Whale's quality score (0-1)
            whale_position_size_usd: Whale's position size in USD
            bankroll: Current bankroll in USD

        Returns:
            Position size in USD
        """
        # Use whale quality as win probability
        p = whale_quality
        q = 1 - p
        b = 1.0  # Assume 1:1 odds for prediction markets

        # Kelly fraction
        kelly_fraction = (p * b - q) / b

        # Apply fractional Kelly (use 25% of full Kelly to reduce risk)
        fractional_kelly = 0.25
        position_fraction = kelly_fraction * fractional_kelly

        # Ensure position fraction is positive and within limits
        position_fraction = max(0, min(position_fraction, self.max_position_pct / 100))

        # Calculate position size
        position_size = bankroll * position_fraction

        # Cap at whale's position size (never bet more than the whale)
        # Scale down if our bankroll allows larger positions
        max_copy_size = min(position_size, whale_position_size_usd * 0.5)  # Max 50% of whale size

        self.logger.debug(
            f"Kelly calculation: quality={whale_quality:.2f}, "
            f"kelly_fraction={kelly_fraction:.3f}, "
            f"position_size=${position_size:.2f}, "
            f"capped=${max_copy_size:.2f}"
        )

        return max_copy_size

    def get_current_market_price(self, market_id: str, side: str) -> Optional[float]:
        """
        Get current market price for a specific side.

        Args:
            market_id: Market ID
            side: YES or NO

        Returns:
            Current price or None if not available
        """
        try:
            market = self.polymarket.get_market(market_id)
            if not market or not hasattr(market, 'outcome_prices'):
                return None

            # Assume outcome_prices[0] = YES, outcome_prices[1] = NO
            if side == "YES":
                return market.outcome_prices[0] if len(market.outcome_prices) > 0 else None
            elif side == "NO":
                return market.outcome_prices[1] if len(market.outcome_prices) > 1 else None

        except Exception as e:
            self.logger.warning(f"Could not get market price for {market_id}: {e}")
            return None

    def should_skip_signal(self, signal: WhaleSignal) -> tuple[bool, Optional[str]]:
        """
        Check if signal should be skipped based on various criteria.

        Args:
            signal: WhaleSignal to evaluate

        Returns:
            Tuple of (should_skip, reason)
        """
        # Check if we already have a position in this market
        existing_trades = db.get_active_trades_for_market(signal.market_id)
        if existing_trades:
            return True, f"Already have {len(existing_trades)} active position(s) in this market"

        # Check current market price vs whale's entry price
        current_price = self.get_current_market_price(signal.market_id, signal.side)
        if current_price is not None:
            price_change_pct = abs((current_price - float(signal.price)) / float(signal.price)) * 100

            # Skip if price has moved too much (>5%)
            if price_change_pct > 5.0:
                return True, f"Price moved {price_change_pct:.1f}% since whale entry"

            # Skip if price is worse than whale's entry (slippage protection)
            if signal.signal_type == "ENTRY":
                if current_price > float(signal.price) * 1.02:  # 2% slippage tolerance
                    return True, f"Current price ${current_price:.3f} worse than whale's ${float(signal.price):.3f}"

        return False, None

    def find_opportunities(self) -> List[Dict[str, Any]]:
        """
        Find copyable whale signals ready for execution.

        Returns:
            List of opportunities based on whale signals
        """
        self.logger.info("Scanning for whale following opportunities...")
        self.logger.info(f"Copy delay: {self.copy_delay_seconds}s, Min whale quality: {self.min_whale_quality:.2f}")

        opportunities = []

        # Track filter statistics
        stats = {
            'total_signals': 0,
            'whale_not_found': 0,
            'skipped': 0,
            'no_price': 0,
            'passed_filters': 0
        }

        try:
            # Get copyable signals (past delay period)
            signals = self.signal_generator.get_copyable_signals(
                copy_delay_seconds=self.copy_delay_seconds
            )

            stats['total_signals'] = len(signals)
            self.logger.info(f"Found {len(signals)} copyable signals (delay: {self.copy_delay_seconds}s)")

            for signal in signals:
                try:
                    self.logger.debug(f"  → Signal #{signal.id}: {signal.signal_type} {signal.side} on {signal.market_id[:10]}...")

                    # Get whale info
                    whale = self.whale_monitor.get_whale(signal.whale_address)
                    if not whale:
                        stats['whale_not_found'] += 1
                        self.logger.warning(f"    ✗ Whale {signal.whale_address[:8]}... not found")
                        continue

                    self.logger.debug(f"    Whale: {whale.nickname or signal.whale_address[:8]}..., quality: {whale.quality_score:.2f}")

                    # Check if signal should be skipped
                    should_skip, skip_reason = self.should_skip_signal(signal)
                    if should_skip:
                        stats['skipped'] += 1
                        self.logger.info(f"    ✗ Skipped: {skip_reason}")
                        self.signal_generator.mark_signal_ignored(signal.id, skip_reason)
                        continue

                    # Get current market info
                    current_price = self.get_current_market_price(signal.market_id, signal.side)
                    if current_price is None:
                        stats['no_price'] += 1
                        self.logger.warning(f"    ✗ Could not get current price for {signal.market_id}")
                        continue

                    self.logger.debug(f"    Current price: {current_price:.3f}, Whale entry: {float(signal.price):.3f}")

                    # Calculate expected profit
                    if signal.signal_type == "ENTRY":
                        expected_profit_pct = ((1.0 - current_price) / current_price) * 100
                    else:
                        # EXIT signals are for closing positions
                        expected_profit_pct = 0

                    # Create opportunity
                    opportunity = {
                        "signal_id": signal.id,
                        "whale_address": signal.whale_address,
                        "whale_nickname": whale.nickname or signal.whale_address[:8],
                        "whale_quality": whale.quality_score,
                        "whale_type": whale.whale_type,
                        "signal_type": signal.signal_type,
                        "market_id": signal.market_id,
                        "side": signal.side,
                        "whale_entry_price": float(signal.price),
                        "current_price": current_price,
                        "whale_position_size_usd": float(signal.size_usd),
                        "confidence": signal.confidence,
                        "expected_profit_pct": expected_profit_pct,
                        "signal_age_seconds": (datetime.utcnow() - signal.created_at).total_seconds(),
                        "reasoning": (
                            f"Copy {whale.whale_type} whale {whale.nickname or signal.whale_address[:8]}...: "
                            f"{signal.signal_type} {signal.side} @ ${current_price:.3f} "
                            f"(quality: {whale.quality_score:.2f})"
                        )
                    }

                    stats['passed_filters'] += 1
                    opportunities.append(opportunity)

                    self.logger.info(
                        f"    ✓✓ OPPORTUNITY: Signal #{signal.id} - {opportunity['reasoning']}"
                    )

                except Exception as e:
                    self.logger.error(f"  ✗ Error processing signal #{signal.id}: {e}", exc_info=True)
                    continue

            # Log statistics summary
            self.logger.info("=" * 70)
            self.logger.info("WHALE FOLLOWING SCAN COMPLETE")
            self.logger.info("=" * 70)
            self.logger.info(f"Total signals checked: {stats['total_signals']}")
            self.logger.info(f"  ✗ Whale not found: {stats['whale_not_found']}")
            self.logger.info(f"  ✗ Skipped (already copied, quality, etc.): {stats['skipped']}")
            self.logger.info(f"  ✗ Could not get price: {stats['no_price']}")
            self.logger.info(f"  ✓ Passed all filters: {stats['passed_filters']}")
            self.logger.info(f"\nFound {len(opportunities)} whale following opportunities")

            # Sort by whale quality (highest quality first)
            opportunities.sort(key=lambda x: x['whale_quality'], reverse=True)

            # Limit to top opportunities
            max_opportunities = 5  # Conservative limit to avoid overexposure
            if len(opportunities) > max_opportunities:
                self.logger.info(f"Limiting to top {max_opportunities} opportunities")
                opportunities = opportunities[:max_opportunities]

            return opportunities

        except Exception as e:
            self.logger.error(f"Error finding whale opportunities: {e}", exc_info=True)
            return []

    def execute_opportunity(self, opportunity: Dict[str, Any]) -> Optional[Trade]:
        """
        Execute a whale following trade.

        Args:
            opportunity: Opportunity dictionary from find_opportunities()

        Returns:
            Trade object if executed, None otherwise
        """
        signal_id = opportunity['signal_id']
        market_id = opportunity['market_id']

        self.logger.info(f"Attempting to execute: {opportunity['reasoning']}")

        try:
            # Get current bankroll
            bankroll = self.risk_manager.get_available_capital()

            # Calculate position size using Kelly Criterion
            position_size = self.calculate_kelly_position_size(
                whale_quality=opportunity['whale_quality'],
                whale_position_size_usd=opportunity['whale_position_size_usd'],
                bankroll=bankroll
            )

            # Ensure minimum position size
            min_position_size = 5.0  # $5 minimum
            if position_size < min_position_size:
                self.logger.warning(
                    f"Calculated position size ${position_size:.2f} below minimum ${min_position_size}, skipping"
                )
                self.signal_generator.mark_signal_ignored(
                    signal_id,
                    f"Position size ${position_size:.2f} below minimum"
                )
                return None

            # Estimate expected profit
            expected_profit_usd = position_size * (opportunity['expected_profit_pct'] / 100)

            # Validate trade with risk manager
            is_valid, errors = self.risk_manager.validate_trade(
                market_id=market_id,
                position_size=position_size,
                expected_profit=expected_profit_usd,
                gas_cost_estimate=0.5  # Estimate
            )

            if not is_valid:
                self.logger.warning(f"Trade validation failed: {errors}")
                for error in errors:
                    self.logger.warning(f"  - {error}")

                self.signal_generator.mark_signal_ignored(
                    signal_id,
                    f"Risk validation failed: {'; '.join(errors)}"
                )
                return None

            # Paper trading mode - simulate trade
            if config.PAPER_TRADING_MODE:
                self.logger.info(
                    f"PAPER TRADE: Would copy whale {opportunity['whale_nickname']}: "
                    f"buy {position_size:.2f} USDC of {opportunity['side']} @ {opportunity['current_price']:.3f}"
                )

                # Get market question
                try:
                    market = self.polymarket.get_market(market_id)
                    market_question = getattr(market, 'question', 'Unknown')
                except Exception:
                    market_question = 'Unknown'

                # Record in database as paper trade
                trade = db.add_trade(
                    market_id=market_id,
                    market_question=market_question,
                    strategy=self.name,
                    side=opportunity['side'],
                    entry_price=opportunity['current_price'],
                    size_usd=position_size,
                    paper_trade=True,
                    confidence_score=opportunity['confidence'],
                    notes=f"{opportunity['reasoning']} | Signal #{signal_id} | Whale position: ${opportunity['whale_position_size_usd']:.2f}"
                )

                # Mark signal as executed
                self.signal_generator.mark_signal_executed(signal_id, trade.id)

                self.logger.info(f"Paper trade recorded: Trade #{trade.id}")

                # Create alert for whale copy
                db.add_alert(
                    alert_type="whale_copy",
                    severity="info",
                    title=f"Copied {opportunity['whale_type']} whale",
                    message=f"Copied {opportunity['whale_nickname']} ({opportunity['whale_type']}): {opportunity['side']} @ ${opportunity['current_price']:.3f}, size ${position_size:.2f}",
                    market_id=market_id,
                    strategy=self.name,
                    trade_id=trade.id
                )

                return trade

            # Live trading mode - execute real trade
            else:
                self.logger.info(
                    f"LIVE TRADE: Copying whale {opportunity['whale_nickname']}: "
                    f"buying {position_size:.2f} USDC of {opportunity['side']} @ {opportunity['current_price']:.3f}"
                )

                # TODO: Execute actual trade via Polymarket client
                # self.polymarket.execute_market_order(...)

                # For now, just log that we would execute
                self.logger.warning("Live trading not yet implemented - skipping execution")

                self.signal_generator.mark_signal_ignored(
                    signal_id,
                    "Live trading not yet implemented"
                )

                return None

        except Exception as e:
            self.logger.error(f"Error executing whale opportunity: {e}", exc_info=True)

            # Create alert
            db.add_alert(
                alert_type="error",
                severity="error",
                title="Whale Following Execution Error",
                message=str(e),
                market_id=market_id,
                strategy=self.name
            )

            # Mark signal as ignored due to error
            try:
                self.signal_generator.mark_signal_ignored(signal_id, f"Execution error: {str(e)}")
            except Exception:
                pass

            return None


if __name__ == "__main__":
    # Test whale following strategy
    logging.basicConfig(level=logging.INFO)

    print("Testing Whale Following Strategy...")

    # Initialize components
    polymarket = Polymarket()
    risk_mgr = RiskManager(polymarket)

    # Create strategy
    strategy = WhaleFollowingStrategy(
        polymarket=polymarket,
        risk_manager=risk_mgr,
        enabled=True
    )

    # Find opportunities
    print("\nFinding whale opportunities...")
    opportunities = strategy.find_opportunities()

    print(f"\nFound {len(opportunities)} opportunities:")
    for i, opp in enumerate(opportunities, 1):
        print(f"{i}. {opp['reasoning']}")

    # Test execution (paper trading)
    if opportunities:
        print(f"\nTesting execution of first opportunity...")
        trade = strategy.execute_opportunity(opportunities[0])
        if trade:
            print(f"✓ Trade executed: {trade}")
        else:
            print("✗ Trade not executed")
    else:
        print("\nNo opportunities found to test execution")

    print("\nWhale Following Strategy testing complete!")
