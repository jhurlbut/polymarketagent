"""
Performance Tracking and Analytics for Polymarket Trading.

Provides real-time P&L tracking, performance metrics calculation,
and historical analysis of trading strategies.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from collections import defaultdict

from sqlalchemy import func, and_
from agents.utils.database import db, Trade, PerformanceMetric
from agents.utils.config import config

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """
    Analyzes trading performance and generates metrics.
    """

    def __init__(self):
        """Initialize performance analyzer."""
        self.logger = logging.getLogger(__name__)

    def get_all_trades(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        strategy: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Trade]:
        """
        Get trades filtered by various criteria.

        Args:
            start_date: Filter trades after this date
            end_date: Filter trades before this date
            strategy: Filter by strategy name
            status: Filter by trade status (open, closed, settled)

        Returns:
            List of Trade objects
        """
        session = db.get_session()
        try:
            query = session.query(Trade)

            if start_date:
                query = query.filter(Trade.entry_time >= start_date)

            if end_date:
                query = query.filter(Trade.entry_time <= end_date)

            if strategy:
                query = query.filter(Trade.strategy == strategy)

            if status:
                query = query.filter(Trade.status == status)

            return query.all()
        finally:
            session.close()

    def calculate_metrics(
        self,
        trades: List[Trade]
    ) -> Dict:
        """
        Calculate comprehensive performance metrics from a list of trades.

        Args:
            trades: List of Trade objects

        Returns:
            Dictionary of performance metrics
        """
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_profit": 0.0,
                "total_loss": 0.0,
                "net_profit": 0.0,
                "avg_profit_per_trade": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "max_win": 0.0,
                "max_loss": 0.0,
                "profit_factor": 0.0,
                "sharpe_ratio": 0.0,
                "total_gas_cost": 0.0,
            }

        # Separate winning and losing trades
        winning_trades = [t for t in trades if t.net_profit_usd and float(t.net_profit_usd) > 0]
        losing_trades = [t for t in trades if t.net_profit_usd and float(t.net_profit_usd) < 0]
        breakeven_trades = [t for t in trades if t.net_profit_usd and float(t.net_profit_usd) == 0]

        # Calculate totals
        total_profit = sum(float(t.net_profit_usd) for t in winning_trades)
        total_loss = abs(sum(float(t.net_profit_usd) for t in losing_trades))
        net_profit = sum(float(t.net_profit_usd or 0) for t in trades)

        total_gas = sum(float(t.gas_cost_usd or 0) for t in trades)

        # Calculate averages
        total_trades = len(trades)
        num_winning = len(winning_trades)
        num_losing = len(losing_trades)

        win_rate = (num_winning / total_trades * 100) if total_trades > 0 else 0.0
        avg_profit_per_trade = net_profit / total_trades if total_trades > 0 else 0.0
        avg_win = total_profit / num_winning if num_winning > 0 else 0.0
        avg_loss = total_loss / num_losing if num_losing > 0 else 0.0

        # Calculate max win/loss
        max_win = max((float(t.net_profit_usd) for t in winning_trades), default=0.0)
        max_loss = abs(min((float(t.net_profit_usd) for t in losing_trades), default=0.0))

        # Profit factor (gross profit / gross loss)
        profit_factor = (total_profit / total_loss) if total_loss > 0 else 0.0

        # Sharpe ratio (simplified: avg return / std dev of returns)
        returns = [float(t.net_profit_usd or 0) for t in trades]
        if len(returns) > 1:
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            std_dev = variance ** 0.5
            sharpe_ratio = (avg_return / std_dev) if std_dev > 0 else 0.0
        else:
            sharpe_ratio = 0.0

        return {
            "total_trades": total_trades,
            "winning_trades": num_winning,
            "losing_trades": num_losing,
            "breakeven_trades": len(breakeven_trades),
            "win_rate": win_rate,
            "total_profit": total_profit,
            "total_loss": total_loss,
            "net_profit": net_profit,
            "avg_profit_per_trade": avg_profit_per_trade,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "max_win": max_win,
            "max_loss": max_loss,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe_ratio,
            "total_gas_cost": total_gas,
        }

    def get_daily_pnl(self, days: int = 30) -> List[Tuple[datetime, float]]:
        """
        Get daily P&L for the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of (date, pnl) tuples
        """
        session = db.get_session()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # Query trades grouped by day
            results = (
                session.query(
                    func.date(Trade.entry_time).label('date'),
                    func.sum(Trade.net_profit_usd).label('pnl')
                )
                .filter(Trade.entry_time >= start_date)
                .filter(Trade.status.in_(["closed", "settled"]))
                .group_by(func.date(Trade.entry_time))
                .order_by('date')
                .all()
            )

            return [(r.date, float(r.pnl or 0)) for r in results]
        finally:
            session.close()

    def get_strategy_performance(self) -> Dict[str, Dict]:
        """
        Get performance metrics broken down by strategy.

        Returns:
            Dictionary mapping strategy name to metrics
        """
        session = db.get_session()
        try:
            # Get all closed trades
            trades = session.query(Trade).filter(
                Trade.status.in_(["closed", "settled"])
            ).all()

            # Group by strategy
            by_strategy = defaultdict(list)
            for trade in trades:
                by_strategy[trade.strategy].append(trade)

            # Calculate metrics for each strategy
            results = {}
            for strategy, strategy_trades in by_strategy.items():
                results[strategy] = self.calculate_metrics(strategy_trades)

            return results
        finally:
            session.close()

    def generate_performance_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Generate a formatted performance report.

        Args:
            start_date: Start of reporting period
            end_date: End of reporting period

        Returns:
            Formatted report string
        """
        # Get trades for period
        trades = self.get_all_trades(
            start_date=start_date,
            end_date=end_date,
            status="closed"
        )

        # Calculate metrics
        metrics = self.calculate_metrics(trades)

        # Get strategy breakdown
        strategy_performance = self.get_strategy_performance()

        # Format report
        report = []
        report.append("=" * 70)
        report.append("PERFORMANCE REPORT")
        report.append("=" * 70)

        if start_date and end_date:
            report.append(f"Period: {start_date.date()} to {end_date.date()}")
        elif start_date:
            report.append(f"Period: {start_date.date()} to present")
        else:
            report.append("Period: All time")

        report.append("")
        report.append("OVERALL PERFORMANCE")
        report.append("-" * 70)
        report.append(f"Total Trades: {metrics['total_trades']}")
        report.append(f"Winning: {metrics['winning_trades']} | Losing: {metrics['losing_trades']} | Breakeven: {metrics['breakeven_trades']}")
        report.append(f"Win Rate: {metrics['win_rate']:.2f}%")
        report.append("")
        report.append(f"Net Profit: ${metrics['net_profit']:.2f}")
        report.append(f"Total Profit: ${metrics['total_profit']:.2f}")
        report.append(f"Total Loss: ${metrics['total_loss']:.2f}")
        report.append(f"Total Gas Cost: ${metrics['total_gas_cost']:.2f}")
        report.append("")
        report.append(f"Avg Profit/Trade: ${metrics['avg_profit_per_trade']:.2f}")
        report.append(f"Avg Win: ${metrics['avg_win']:.2f}")
        report.append(f"Avg Loss: ${metrics['avg_loss']:.2f}")
        report.append(f"Max Win: ${metrics['max_win']:.2f}")
        report.append(f"Max Loss: ${metrics['max_loss']:.2f}")
        report.append("")
        report.append(f"Profit Factor: {metrics['profit_factor']:.2f}")
        report.append(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")

        # Strategy breakdown
        if strategy_performance:
            report.append("")
            report.append("STRATEGY PERFORMANCE")
            report.append("-" * 70)
            for strategy, strat_metrics in strategy_performance.items():
                report.append(f"\n{strategy}:")
                report.append(f"  Trades: {strat_metrics['total_trades']}")
                report.append(f"  Win Rate: {strat_metrics['win_rate']:.2f}%")
                report.append(f"  Net Profit: ${strat_metrics['net_profit']:.2f}")
                report.append(f"  Avg Profit/Trade: ${strat_metrics['avg_profit_per_trade']:.2f}")
                report.append(f"  Profit Factor: {strat_metrics['profit_factor']:.2f}")

        report.append("")
        report.append("=" * 70)

        return "\n".join(report)

    def save_performance_metric(
        self,
        period_type: str,
        period_start: datetime,
        period_end: datetime,
        strategy: Optional[str] = None
    ) -> PerformanceMetric:
        """
        Calculate and save performance metrics for a period.

        Args:
            period_type: "daily", "weekly", or "monthly"
            period_start: Start of period
            period_end: End of period
            strategy: Optional strategy filter

        Returns:
            Created PerformanceMetric object
        """
        # Get trades for period
        trades = self.get_all_trades(
            start_date=period_start,
            end_date=period_end,
            strategy=strategy,
            status="closed"
        )

        # Calculate metrics
        metrics = self.calculate_metrics(trades)

        # Save to database
        session = db.get_session()
        try:
            perf_metric = PerformanceMetric(
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
                strategy=strategy,
                total_trades=metrics["total_trades"],
                winning_trades=metrics["winning_trades"],
                losing_trades=metrics["losing_trades"],
                win_rate=metrics["win_rate"],
                total_profit_usd=Decimal(str(metrics["total_profit"])),
                total_loss_usd=Decimal(str(metrics["total_loss"])),
                net_profit_usd=Decimal(str(metrics["net_profit"])),
                avg_profit_per_trade=Decimal(str(metrics["avg_profit_per_trade"])),
                avg_win_amount=Decimal(str(metrics["avg_win"])),
                avg_loss_amount=Decimal(str(metrics["avg_loss"])),
                max_win=Decimal(str(metrics["max_win"])),
                max_loss=Decimal(str(metrics["max_loss"])),
                sharpe_ratio=metrics["sharpe_ratio"],
                profit_factor=metrics["profit_factor"],
                total_gas_cost_usd=Decimal(str(metrics["total_gas_cost"])),
            )

            session.add(perf_metric)
            session.commit()
            session.refresh(perf_metric)

            self.logger.info(
                f"Saved {period_type} performance metric: "
                f"Net P&L ${metrics['net_profit']:.2f}, "
                f"Win Rate {metrics['win_rate']:.2f}%"
            )

            return perf_metric
        finally:
            session.close()


if __name__ == "__main__":
    # Test analytics
    logging.basicConfig(level=logging.INFO)

    print("Testing Performance Analyzer...")

    analyzer = PerformanceAnalyzer()

    # Generate report
    report = analyzer.generate_performance_report()
    print(report)

    # Get strategy performance
    print("\nStrategy Performance:")
    strat_perf = analyzer.get_strategy_performance()
    for strategy, metrics in strat_perf.items():
        print(f"\n{strategy}:")
        print(f"  Net Profit: ${metrics['net_profit']:.2f}")
        print(f"  Win Rate: {metrics['win_rate']:.2f}%")

    print("\nPerformance Analyzer testing complete!")
