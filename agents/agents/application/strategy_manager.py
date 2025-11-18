"""
Multi-Strategy Orchestrator for Polymarket Trading.

Manages multiple trading strategies, coordinates execution,
handles conflicts, and allocates capital.
"""

from typing import Dict, List, Optional, Any, Type
from datetime import datetime
import logging
from abc import ABC, abstractmethod

from agents.utils.config import config
from agents.utils.database import db, Trade, Alert
from agents.application.risk_manager import RiskManager
from agents.application.analytics import PerformanceAnalyzer

# Use paper trading client to avoid py-clob-client dependency
try:
    from agents.polymarket.polymarket import Polymarket, SimpleMarket
except (ImportError, ModuleNotFoundError):
    from agents.polymarket.polymarket_paper import PolymarketPaper as Polymarket
    from agents.utils.objects import SimpleMarket

logger = logging.getLogger(__name__)


class TradingStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    All strategies must implement these methods.
    """

    def __init__(
        self,
        name: str,
        polymarket: Polymarket,
        risk_manager: RiskManager,
        enabled: bool = True
    ):
        """
        Initialize strategy.

        Args:
            name: Strategy name
            polymarket: Polymarket client
            risk_manager: Risk management instance
            enabled: Whether strategy is enabled
        """
        self.name = name
        self.polymarket = polymarket
        self.risk_manager = risk_manager
        self.enabled = enabled
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    def find_opportunities(self) -> List[Dict[str, Any]]:
        """
        Scan markets and identify trading opportunities.

        Returns:
            List of opportunity dictionaries with keys:
            - market_id: str
            - market_question: str
            - side: str (YES/NO)
            - entry_price: float
            - confidence: float (0-1)
            - expected_profit_pct: float
            - reasoning: str
        """
        pass

    @abstractmethod
    def execute_opportunity(self, opportunity: Dict[str, Any]) -> Optional[Trade]:
        """
        Execute a trading opportunity.

        Args:
            opportunity: Opportunity dictionary from find_opportunities()

        Returns:
            Trade object if executed, None if not
        """
        pass

    def run(self) -> List[Trade]:
        """
        Main execution loop for the strategy.

        Returns:
            List of executed trades
        """
        if not self.enabled:
            self.logger.info(f"Strategy {self.name} is disabled")
            return []

        self.logger.info(f"Running strategy: {self.name}")

        try:
            # Find opportunities
            opportunities = self.find_opportunities()
            self.logger.info(f"Found {len(opportunities)} opportunities")

            # Execute opportunities
            executed_trades = []
            for opp in opportunities:
                trade = self.execute_opportunity(opp)
                if trade:
                    executed_trades.append(trade)

            self.logger.info(f"Executed {len(executed_trades)} trades")
            return executed_trades

        except Exception as e:
            self.logger.error(f"Error running strategy {self.name}: {e}", exc_info=True)

            # Create alert
            db.add_alert(
                alert_type="error",
                severity="error",
                title=f"Strategy Error: {self.name}",
                message=str(e),
                strategy=self.name
            )

            return []

    def get_performance_summary(self) -> Dict:
        """
        Get performance summary for this strategy.

        Returns:
            Performance metrics dictionary
        """
        analyzer = PerformanceAnalyzer()
        session = db.get_session()
        try:
            trades = session.query(Trade).filter(Trade.strategy == self.name).all()
            return analyzer.calculate_metrics(trades)
        finally:
            session.close()


class StrategyManager:
    """
    Orchestrates multiple trading strategies.
    Handles execution scheduling, conflict resolution, and capital allocation.
    """

    def __init__(self, polymarket: Optional[Polymarket] = None):
        """
        Initialize strategy manager.

        Args:
            polymarket: Optional Polymarket client instance
        """
        self.polymarket = polymarket or Polymarket()
        self.risk_manager = RiskManager(self.polymarket)
        self.analyzer = PerformanceAnalyzer()

        self.strategies: Dict[str, TradingStrategy] = {}
        self.logger = logging.getLogger(__name__)

    def register_strategy(self, strategy: TradingStrategy):
        """
        Register a trading strategy.

        Args:
            strategy: TradingStrategy instance
        """
        self.strategies[strategy.name] = strategy
        self.logger.info(f"Registered strategy: {strategy.name}")

    def unregister_strategy(self, strategy_name: str):
        """
        Unregister a trading strategy.

        Args:
            strategy_name: Name of strategy to remove
        """
        if strategy_name in self.strategies:
            del self.strategies[strategy_name]
            self.logger.info(f"Unregistered strategy: {strategy_name}")

    def enable_strategy(self, strategy_name: str):
        """Enable a strategy."""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].enabled = True
            self.logger.info(f"Enabled strategy: {strategy_name}")

    def disable_strategy(self, strategy_name: str):
        """Disable a strategy."""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].enabled = False
            self.logger.info(f"Disabled strategy: {strategy_name}")

    def run_all_strategies(self) -> Dict[str, List[Trade]]:
        """
        Run all enabled strategies.

        Returns:
            Dictionary mapping strategy name to list of executed trades
        """
        self.logger.info("=" * 60)
        self.logger.info(f"Running all strategies at {datetime.utcnow()}")
        self.logger.info("=" * 60)

        # Check risk limits before running any strategies
        self.logger.info("\nChecking risk limits...")
        risk_summary = self.risk_manager.get_risk_summary()

        if not risk_summary["daily_status"]["ok"]:
            self.logger.warning(f"Daily loss limit breached: {risk_summary['daily_status']['message']}")
            db.add_alert(
                alert_type="risk",
                severity="critical",
                title="Daily Loss Limit Breached",
                message=risk_summary["daily_status"]["message"]
            )
            return {}

        if not risk_summary["weekly_status"]["ok"]:
            self.logger.warning(f"Weekly loss limit breached: {risk_summary['weekly_status']['message']}")
            db.add_alert(
                alert_type="risk",
                severity="critical",
                title="Weekly Loss Limit Breached",
                message=risk_summary["weekly_status"]["message"]
            )
            return {}

        # Run each strategy
        results = {}
        for strategy_name, strategy in self.strategies.items():
            if strategy.enabled:
                self.logger.info(f"\nExecuting strategy: {strategy_name}")
                try:
                    trades = strategy.run()
                    results[strategy_name] = trades
                except Exception as e:
                    self.logger.error(f"Error executing {strategy_name}: {e}", exc_info=True)
                    results[strategy_name] = []
            else:
                self.logger.info(f"Skipping disabled strategy: {strategy_name}")
                results[strategy_name] = []

        # Summary
        total_trades = sum(len(trades) for trades in results.values())
        self.logger.info(f"\nTotal trades executed: {total_trades}")

        return results

    def run_strategy(self, strategy_name: str) -> List[Trade]:
        """
        Run a specific strategy by name.

        Args:
            strategy_name: Name of strategy to run

        Returns:
            List of executed trades
        """
        if strategy_name not in self.strategies:
            raise ValueError(f"Strategy '{strategy_name}' not registered")

        strategy = self.strategies[strategy_name]

        if not strategy.enabled:
            self.logger.warning(f"Strategy '{strategy_name}' is disabled")
            return []

        return strategy.run()

    def get_all_performance_metrics(self) -> Dict[str, Dict]:
        """
        Get performance metrics for all strategies.

        Returns:
            Dictionary mapping strategy name to metrics
        """
        return self.analyzer.get_strategy_performance()

    def print_performance_summary(self):
        """Print performance summary for all strategies."""
        print("\n" + "=" * 70)
        print("STRATEGY MANAGER PERFORMANCE SUMMARY")
        print("=" * 70)

        # Overall performance
        report = self.analyzer.generate_performance_report()
        print(report)

        # Risk summary
        print("\n" + "=" * 70)
        print("RISK SUMMARY")
        print("=" * 70)
        self.risk_manager.print_risk_summary()

    def get_status(self) -> Dict:
        """
        Get current status of the strategy manager.

        Returns:
            Status dictionary
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "paper_trading_mode": config.PAPER_TRADING_MODE,
            "strategies": {
                name: {
                    "enabled": strategy.enabled,
                    "class": strategy.__class__.__name__
                }
                for name, strategy in self.strategies.items()
            },
            "risk_summary": self.risk_manager.get_risk_summary(),
            "performance": self.get_all_performance_metrics(),
        }

    def print_status(self):
        """Print current status."""
        status = self.get_status()

        print("\n" + "=" * 70)
        print("STRATEGY MANAGER STATUS")
        print("=" * 70)
        print(f"Timestamp: {status['timestamp']}")
        print(f"Mode: {'PAPER TRADING' if status['paper_trading_mode'] else 'LIVE TRADING'}")

        print(f"\nRegistered Strategies:")
        for name, info in status["strategies"].items():
            status_str = "ENABLED" if info["enabled"] else "DISABLED"
            print(f"  - {name} ({info['class']}): {status_str}")

        print(f"\nRisk Summary:")
        risk = status["risk_summary"]
        print(f"  Available Capital: ${risk['available_capital']:.2f}")
        print(f"  Total Exposure: ${risk['total_exposure']:.2f} ({risk['exposure_pct']:.1f}%)")
        print(f"  Open Positions: {risk['open_positions']}")
        print(f"  Daily Status: {'✓' if risk['daily_status']['ok'] else '✗'} {risk['daily_status']['message']}")
        print(f"  Weekly Status: {'✓' if risk['weekly_status']['ok'] else '✗'} {risk['weekly_status']['message']}")

        print("=" * 70 + "\n")


if __name__ == "__main__":
    # Test strategy manager
    logging.basicConfig(level=logging.INFO)

    print("Testing Strategy Manager...")

    # Initialize
    manager = StrategyManager()

    # Print status
    manager.print_status()

    # Print performance
    manager.print_performance_summary()

    print("\nStrategy Manager testing complete!")
