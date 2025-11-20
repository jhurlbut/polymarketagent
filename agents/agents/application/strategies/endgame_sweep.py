"""
Endgame Sweep Trading Strategy for Polymarket.

Targets markets priced between 0.95-0.99 that are near settlement,
capturing the final spread for low-risk consistent profits.

Strategy Overview:
- Buy outcomes that have surged to near certainty (0.95-0.99)
- Wait for market settlement to capture the final 1-5% spread
- ~90% of large trades execute above 0.95 (according to research)
- Expected profit: 0.1-0.5% per trade
- Risk: Black swan events and whale manipulation

Key Features:
1. Time-to-settlement filtering (prioritize <24h)
2. Black swan risk detection using sentiment
3. Comment section analysis for manipulation signals
4. Whale activity monitoring
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from agents.application.strategy_manager import TradingStrategy
from agents.application.risk_manager import RiskManager
from agents.utils.config import config
from agents.utils.database import db, Trade

# Use paper trading client to avoid py-clob-client dependency
try:
    from agents.polymarket.polymarket import Polymarket, SimpleMarket
except (ImportError, ModuleNotFoundError):
    from agents.polymarket.polymarket_paper import PolymarketPaper as Polymarket
    from agents.utils.objects import SimpleMarket

logger = logging.getLogger(__name__)


class EndgameSweepStrategy(TradingStrategy):
    """
    Endgame Sweep: Trade near-certain outcomes close to settlement.
    """

    def __init__(
        self,
        polymarket: Polymarket,
        risk_manager: RiskManager,
        enabled: bool = True,
        min_price: float = None,
        max_price: float = None,
        max_hours_to_settlement: int = None
    ):
        """
        Initialize Endgame Sweep strategy.

        Args:
            polymarket: Polymarket client
            risk_manager: Risk manager instance
            enabled: Whether strategy is enabled
            min_price: Minimum price threshold (default from config)
            max_price: Maximum price threshold (default from config)
            max_hours_to_settlement: Max hours until settlement (default from config)
        """
        super().__init__("endgame_sweep", polymarket, risk_manager, enabled)

        self.min_price = min_price or config.ENDGAME_MIN_PRICE
        self.max_price = max_price or config.ENDGAME_MAX_PRICE
        self.max_hours_to_settlement = max_hours_to_settlement or config.ENDGAME_MAX_TIME_TO_SETTLEMENT_HOURS

        self.min_confidence = 0.70  # Default confidence threshold

        self.logger.info(
            f"Endgame Sweep initialized: "
            f"price range [{self.min_price}, {self.max_price}], "
            f"max settlement time {self.max_hours_to_settlement}h"
        )

    def load_settings_from_db(self):
        """Load latest settings from database, falling back to config defaults."""
        try:
            settings = db.get_strategy_settings("endgame_sweep")
            if settings:
                self.min_price = settings.endgame_min_price or config.ENDGAME_MIN_PRICE
                self.max_price = settings.endgame_max_price or config.ENDGAME_MAX_PRICE
                self.max_hours_to_settlement = settings.endgame_max_hours_to_settlement or config.ENDGAME_MAX_TIME_TO_SETTLEMENT_HOURS
                self.min_confidence = settings.endgame_min_confidence or 0.70
                self.logger.info(
                    f"Loaded settings from database: "
                    f"price [{self.min_price}, {self.max_price}], "
                    f"settlement {self.max_hours_to_settlement}h, "
                    f"confidence {self.min_confidence:.0%}"
                )
        except Exception as e:
            self.logger.warning(f"Could not load settings from database, using defaults: {e}")

    def is_near_settlement(self, market: SimpleMarket) -> bool:
        """
        Check if market is close to settlement.

        Args:
            market: SimpleMarket object

        Returns:
            True if market will settle soon
        """
        # TODO: Implement proper settlement time checking
        # For now, we'll use a simple heuristic based on market metadata

        # Check if market has an end date
        if hasattr(market, 'end_date_iso') and market.end_date_iso:
            try:
                end_date = datetime.fromisoformat(market.end_date_iso.replace('Z', '+00:00'))
                time_to_settlement = end_date - datetime.now(end_date.tzinfo)

                hours_to_settlement = time_to_settlement.total_seconds() / 3600

                if hours_to_settlement <= self.max_hours_to_settlement:
                    self.logger.debug(
                        f"Market {market.market_id} settles in {hours_to_settlement:.1f}h"
                    )
                    return True

            except Exception as e:
                self.logger.debug(f"Error parsing end date for {market.market_id}: {e}")

        return False

    def calculate_black_swan_risk(self, market: SimpleMarket) -> float:
        """
        Estimate black swan risk for a market.

        Black swans are unexpected events that could reverse a "certain" outcome.
        Examples: match ruled invalid, scandal overturns election, etc.

        Args:
            market: SimpleMarket object

        Returns:
            Risk score from 0 (low risk) to 1 (high risk)
        """
        risk_score = 0.0

        # TODO: Implement sophisticated black swan detection
        # For now, use simple heuristics:

        # 1. Check market category (sports have higher reversal risk)
        if hasattr(market, 'tags') and market.tags:
            if 'sports' in [tag.lower() for tag in market.tags]:
                risk_score += 0.2
                self.logger.debug(f"Sports market - increased black swan risk")

        # 2. Check time to settlement (longer time = higher risk)
        # Markets settling in <1 hour are very low risk
        # Markets settling in 12-24 hours have medium risk
        if hasattr(market, 'end_date_iso') and market.end_date_iso:
            try:
                end_date = datetime.fromisoformat(market.end_date_iso.replace('Z', '+00:00'))
                hours_to_settlement = (end_date - datetime.now(end_date.tzinfo)).total_seconds() / 3600

                if hours_to_settlement > 12:
                    risk_score += 0.3
                elif hours_to_settlement > 6:
                    risk_score += 0.1

            except Exception:
                pass

        # 3. Check price volatility
        # If price is exactly 0.99+, it's less likely to reverse
        # If price is 0.95-0.97, there's more uncertainty
        # This would require historical price data - skip for now

        # Normalize risk score to [0, 1]
        risk_score = min(1.0, risk_score)

        return risk_score

    def detect_manipulation_signals(self, market: SimpleMarket) -> bool:
        """
        Detect potential whale manipulation signals.

        Whales may:
        1. Crash price from 0.99 to 0.90 to create panic
        2. Spread FUD in comments
        3. Create artificial reversal rumors

        Args:
            market: SimpleMarket object

        Returns:
            True if manipulation signals detected
        """
        # TODO: Implement comment section scraping and sentiment analysis
        # TODO: Monitor on-chain for large dumps
        # TODO: Check for unusual price movements

        # For now, return False (no manipulation detected)
        return False

    def find_opportunities(self) -> List[Dict[str, Any]]:
        """
        Scan markets for endgame sweep opportunities.

        Returns:
            List of opportunities
        """
        # Load latest settings from database
        self.load_settings_from_db()

        self.logger.info("Scanning for endgame sweep opportunities...")
        self.logger.info(f"Filters: price [{self.min_price}, {self.max_price}], max settlement {self.max_hours_to_settlement}h, min confidence {self.min_confidence:.0%}")

        opportunities = []

        # Track filter statistics
        stats = {
            'total_markets': 0,
            'not_binary': 0,
            'price_out_of_range': 0,
            'not_near_settlement': 0,
            'low_confidence': 0,
            'manipulation_detected': 0,
            'passed_filters': 0
        }

        try:
            # Get all tradeable markets
            markets = self.polymarket.get_all_tradeable_markets()
            stats['total_markets'] = len(markets)
            self.logger.info(f"Scanning {len(markets)} tradeable markets")

            for market in markets:
                try:
                    market_id = getattr(market, 'market_id', 'unknown')
                    market_question = getattr(market, 'question', 'Unknown question')

                    # Check if market is binary (has clear YES/NO)
                    if not hasattr(market, 'outcome_prices') or len(market.outcome_prices) != 2:
                        stats['not_binary'] += 1
                        self.logger.debug(f"  ✗ {market_id[:10]}... not binary (has {len(getattr(market, 'outcome_prices', []))} outcomes)")
                        continue

                    # Get YES and NO prices
                    yes_price = market.outcome_prices[0]
                    no_price = market.outcome_prices[1]

                    self.logger.debug(f"  → {market_id[:10]}... YES={yes_price:.3f}, NO={no_price:.3f}: {market_question[:50]}...")

                    # Track if this market passes any checks
                    market_checked = False

                    # Check YES side
                    if self.min_price <= yes_price <= self.max_price:
                        self.logger.debug(f"    YES price in range [{self.min_price}, {self.max_price}]")
                        market_checked = True

                        if self.is_near_settlement(market):
                            self.logger.debug(f"    ✓ Near settlement (< {self.max_hours_to_settlement}h)")

                            # Calculate expected profit
                            expected_profit_pct = ((1.0 - yes_price) / yes_price) * 100

                            # Check black swan risk
                            black_swan_risk = self.calculate_black_swan_risk(market)
                            self.logger.debug(f"    Black swan risk: {black_swan_risk:.2f}")

                            # Check for manipulation
                            manipulation_detected = self.detect_manipulation_signals(market)

                            if manipulation_detected:
                                stats['manipulation_detected'] += 1
                                self.logger.warning(
                                    f"    ✗ Manipulation detected in {market_id}, skipping"
                                )
                                continue

                            # Calculate confidence (inverse of black swan risk)
                            confidence = 1.0 - black_swan_risk

                            # Only proceed if confidence is high enough
                            if confidence >= self.min_confidence:
                                stats['passed_filters'] += 1
                                opportunity = {
                                    "market_id": market.market_id,
                                    "market_question": getattr(market, 'question', 'Unknown'),
                                    "side": "YES",
                                    "entry_price": yes_price,
                                    "confidence": confidence,
                                    "expected_profit_pct": expected_profit_pct,
                                    "black_swan_risk": black_swan_risk,
                                    "reasoning": (
                                        f"Endgame sweep: YES @ ${yes_price:.3f}, "
                                        f"expected profit {expected_profit_pct:.2f}%, "
                                        f"confidence {confidence:.0%}"
                                    )
                                }
                                opportunities.append(opportunity)
                                self.logger.info(
                                    f"    ✓✓ OPPORTUNITY: {market.market_id} - {opportunity['reasoning']}"
                                )
                            else:
                                stats['low_confidence'] += 1
                                self.logger.debug(f"    ✗ Confidence too low: {confidence:.2f} < {self.min_confidence}")
                        else:
                            stats['not_near_settlement'] += 1
                            self.logger.debug(f"    ✗ Not near settlement (> {self.max_hours_to_settlement}h)")
                    elif yes_price > self.max_price:
                        stats['price_out_of_range'] += 1
                        self.logger.debug(f"    ✗ YES price too high: {yes_price:.3f} > {self.max_price}")
                        market_checked = True
                    elif yes_price < self.min_price:
                        stats['price_out_of_range'] += 1
                        self.logger.debug(f"    ✗ YES price too low: {yes_price:.3f} < {self.min_price}")
                        market_checked = True

                    # Check NO side
                    if self.min_price <= no_price <= self.max_price:
                        self.logger.debug(f"    NO price in range [{self.min_price}, {self.max_price}]")
                        market_checked = True
                        if self.is_near_settlement(market):
                            self.logger.debug(f"    ✓ Near settlement (< {self.max_hours_to_settlement}h)")
                            expected_profit_pct = ((1.0 - no_price) / no_price) * 100
                            black_swan_risk = self.calculate_black_swan_risk(market)
                            self.logger.debug(f"    Black swan risk: {black_swan_risk:.2f}")
                            manipulation_detected = self.detect_manipulation_signals(market)

                            if manipulation_detected:
                                stats['manipulation_detected'] += 1
                                self.logger.warning(f"    ✗ Manipulation detected in {market_id}, skipping")
                                continue

                            confidence = 1.0 - black_swan_risk

                            if confidence >= self.min_confidence:
                                stats['passed_filters'] += 1
                                opportunity = {
                                    "market_id": market.market_id,
                                    "market_question": getattr(market, 'question', 'Unknown'),
                                    "side": "NO",
                                    "entry_price": no_price,
                                    "confidence": confidence,
                                    "expected_profit_pct": expected_profit_pct,
                                    "black_swan_risk": black_swan_risk,
                                    "reasoning": (
                                        f"Endgame sweep: NO @ ${no_price:.3f}, "
                                        f"expected profit {expected_profit_pct:.2f}%, "
                                        f"confidence {confidence:.0%}"
                                    )
                                }
                                opportunities.append(opportunity)
                                self.logger.info(
                                    f"    ✓✓ OPPORTUNITY: {market.market_id} - {opportunity['reasoning']}"
                                )
                            else:
                                stats['low_confidence'] += 1
                                self.logger.debug(f"    ✗ Confidence too low: {confidence:.2f} < {self.min_confidence}")
                        else:
                            stats['not_near_settlement'] += 1
                            self.logger.debug(f"    ✗ Not near settlement (> {self.max_hours_to_settlement}h)")
                    elif no_price > self.max_price:
                        stats['price_out_of_range'] += 1
                        self.logger.debug(f"    ✗ NO price too high: {no_price:.3f} > {self.max_price}")
                        market_checked = True
                    elif no_price < self.min_price:
                        stats['price_out_of_range'] += 1
                        self.logger.debug(f"    ✗ NO price too low: {no_price:.3f} < {self.min_price}")
                        market_checked = True

                    # If neither YES nor NO was in range, log it
                    if not market_checked:
                        self.logger.debug(f"    ✗ Both prices out of range")

                except Exception as e:
                    self.logger.debug(f"  ✗ Error analyzing market {market_id}: {e}")
                    continue

            # Log statistics summary
            self.logger.info("=" * 70)
            self.logger.info("ENDGAME SWEEP SCAN COMPLETE")
            self.logger.info("=" * 70)
            self.logger.info(f"Total markets scanned: {stats['total_markets']}")
            self.logger.info(f"  ✗ Not binary: {stats['not_binary']}")
            self.logger.info(f"  ✗ Price out of range: {stats['price_out_of_range']}")
            self.logger.info(f"  ✗ Not near settlement: {stats['not_near_settlement']}")
            self.logger.info(f"  ✗ Low confidence: {stats['low_confidence']}")
            self.logger.info(f"  ✗ Manipulation detected: {stats['manipulation_detected']}")
            self.logger.info(f"  ✓ Passed all filters: {stats['passed_filters']}")
            self.logger.info(f"\nFound {len(opportunities)} endgame sweep opportunities")

            # Sort by expected profit (highest first)
            opportunities.sort(key=lambda x: x['expected_profit_pct'], reverse=True)

            # Limit to top opportunities to avoid overexposure
            max_opportunities = 10
            if len(opportunities) > max_opportunities:
                self.logger.info(f"Limiting to top {max_opportunities} opportunities")
                opportunities = opportunities[:max_opportunities]

            return opportunities

        except Exception as e:
            self.logger.error(f"Error finding opportunities: {e}", exc_info=True)
            return []

    def execute_opportunity(self, opportunity: Dict[str, Any]) -> Optional[Trade]:
        """
        Execute an endgame sweep trade.

        Args:
            opportunity: Opportunity dictionary

        Returns:
            Trade object if executed, None otherwise
        """
        market_id = opportunity['market_id']
        self.logger.info(f"Attempting to execute: {opportunity['reasoning']}")

        try:
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(
                confidence=opportunity['confidence'],
                expected_profit_pct=opportunity['expected_profit_pct']
            )

            # Estimate expected profit in dollars
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
                return None

            # Paper trading mode - simulate trade
            if config.PAPER_TRADING_MODE:
                self.logger.info(
                    f"PAPER TRADE: Would buy {position_size:.2f} USDC of "
                    f"{opportunity['side']} @ {opportunity['entry_price']:.3f}"
                )

                # Record in database as paper trade
                trade = db.add_trade(
                    market_id=market_id,
                    market_question=opportunity['market_question'],
                    strategy=self.name,
                    side=opportunity['side'],
                    entry_price=opportunity['entry_price'],
                    size_usd=position_size,
                    paper_trade=True,
                    confidence_score=opportunity['confidence'],
                    notes=opportunity['reasoning']
                )

                self.logger.info(f"Paper trade recorded: Trade #{trade.id}")
                return trade

            # Live trading mode - execute real trade
            else:
                self.logger.info(
                    f"LIVE TRADE: Buying {position_size:.2f} USDC of "
                    f"{opportunity['side']} @ {opportunity['entry_price']:.3f}"
                )

                # TODO: Execute actual trade via Polymarket client
                # self.polymarket.execute_market_order(...)

                # For now, just log that we would execute
                self.logger.warning("Live trading not yet implemented - skipping execution")
                return None

        except Exception as e:
            self.logger.error(f"Error executing opportunity: {e}", exc_info=True)

            # Create alert
            db.add_alert(
                alert_type="error",
                severity="error",
                title="Endgame Sweep Execution Error",
                message=str(e),
                market_id=market_id,
                strategy=self.name
            )

            return None


if __name__ == "__main__":
    # Test endgame sweep strategy
    logging.basicConfig(level=logging.INFO)

    print("Testing Endgame Sweep Strategy...")

    # Initialize components
    polymarket = Polymarket()
    risk_mgr = RiskManager(polymarket)

    # Create strategy
    strategy = EndgameSweepStrategy(
        polymarket=polymarket,
        risk_manager=risk_mgr,
        enabled=True
    )

    # Find opportunities
    print("\nFinding opportunities...")
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

    print("\nEndgame Sweep Strategy testing complete!")
