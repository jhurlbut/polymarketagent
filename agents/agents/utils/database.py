"""
Database models and schema for tracking trading performance.
Uses SQLAlchemy for ORM with support for SQLite and PostgreSQL.
"""

from datetime import datetime
from typing import Optional
from decimal import Decimal

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from agents.utils.config import config

Base = declarative_base()


class Trade(Base):
    """
    Represents a single trade execution.
    Tracks entry, exit, profit/loss, and metadata.
    """

    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Trade identification
    market_id = Column(String(100), nullable=False, index=True)
    market_question = Column(Text, nullable=True)
    strategy = Column(String(50), nullable=False, index=True)

    # Position details
    side = Column(String(10), nullable=False)  # YES or NO
    outcome = Column(String(100), nullable=True)  # Specific outcome for multi-option markets

    # Pricing
    entry_price = Column(Numeric(10, 8), nullable=False)
    exit_price = Column(Numeric(10, 8), nullable=True)
    size_usd = Column(Numeric(12, 2), nullable=False)

    # Performance
    profit_loss_usd = Column(Numeric(12, 2), nullable=True)
    profit_loss_pct = Column(Float, nullable=True)
    gas_cost_usd = Column(Numeric(10, 6), nullable=True)
    net_profit_usd = Column(Numeric(12, 2), nullable=True)

    # Timing
    entry_time = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    exit_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Status
    status = Column(String(20), nullable=False, default="open")  # open, closed, settled
    paper_trade = Column(Boolean, nullable=False, default=True)

    # Metadata
    notes = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)  # AI confidence in prediction
    tx_hash_entry = Column(String(66), nullable=True)
    tx_hash_exit = Column(String(66), nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Trade(id={self.id}, market={self.market_id}, strategy={self.strategy}, pnl={self.profit_loss_usd})>"


class MarketSnapshot(Base):
    """
    Time-series data for market prices and liquidity.
    Used for analysis and backtesting.
    """

    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Market identification
    market_id = Column(String(100), nullable=False, index=True)
    market_question = Column(Text, nullable=True)

    # Price data
    price_yes = Column(Numeric(10, 8), nullable=False)
    price_no = Column(Numeric(10, 8), nullable=False)

    # Volume and liquidity
    volume_24h = Column(Numeric(15, 2), nullable=True)
    liquidity_usd = Column(Numeric(15, 2), nullable=True)

    # Sentiment (if available)
    comment_sentiment = Column(Float, nullable=True)  # -1 to 1 scale
    whale_activity_score = Column(Float, nullable=True)  # 0 to 1 scale

    # Timing
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<MarketSnapshot(market={self.market_id}, price={self.price_yes}, time={self.timestamp})>"


class PerformanceMetric(Base):
    """
    Daily/weekly/monthly performance aggregations.
    """

    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Time period
    period_type = Column(String(20), nullable=False, index=True)  # daily, weekly, monthly
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)

    # Strategy filter (null = all strategies)
    strategy = Column(String(50), nullable=True, index=True)

    # Performance metrics
    total_trades = Column(Integer, nullable=False, default=0)
    winning_trades = Column(Integer, nullable=False, default=0)
    losing_trades = Column(Integer, nullable=False, default=0)
    win_rate = Column(Float, nullable=True)

    total_profit_usd = Column(Numeric(12, 2), nullable=True)
    total_loss_usd = Column(Numeric(12, 2), nullable=True)
    net_profit_usd = Column(Numeric(12, 2), nullable=True)

    avg_profit_per_trade = Column(Numeric(12, 2), nullable=True)
    avg_win_amount = Column(Numeric(12, 2), nullable=True)
    avg_loss_amount = Column(Numeric(12, 2), nullable=True)

    max_win = Column(Numeric(12, 2), nullable=True)
    max_loss = Column(Numeric(12, 2), nullable=True)
    max_drawdown = Column(Numeric(12, 2), nullable=True)

    # Risk metrics
    sharpe_ratio = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)  # gross_profit / gross_loss

    # Costs
    total_gas_cost_usd = Column(Numeric(12, 2), nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<PerformanceMetric(period={self.period_type}, net_profit={self.net_profit_usd})>"


class Alert(Base):
    """
    System alerts and notifications.
    """

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Alert details
    alert_type = Column(String(50), nullable=False, index=True)  # opportunity, risk, error, system
    severity = Column(String(20), nullable=False, default="info")  # info, warning, error, critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # Related entities
    market_id = Column(String(100), nullable=True, index=True)
    trade_id = Column(Integer, nullable=True)
    strategy = Column(String(50), nullable=True)

    # Status
    acknowledged = Column(Boolean, nullable=False, default=False)
    resolved = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Alert(type={self.alert_type}, severity={self.severity}, title={self.title})>"


class StrategySettings(Base):
    """
    Configurable strategy parameters.
    Allows dynamic adjustment of strategy criteria through the dashboard.
    """

    __tablename__ = "strategy_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Strategy identification
    strategy_name = Column(String(50), nullable=False, unique=True, index=True)

    # Endgame Sweep Settings
    endgame_min_price = Column(Float, nullable=True, default=0.95)
    endgame_max_price = Column(Float, nullable=True, default=0.99)
    endgame_max_hours_to_settlement = Column(Integer, nullable=True, default=24)
    endgame_min_confidence = Column(Float, nullable=True, default=0.70)

    # General Settings
    enabled = Column(Boolean, nullable=False, default=True)
    min_profit_threshold_pct = Column(Float, nullable=True, default=0.3)

    # Scan trigger
    scan_requested = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<StrategySettings(strategy={self.strategy_name}, enabled={self.enabled})>"


class DatabaseManager:
    """
    Manages database connections and provides utility methods.
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database connection.

        Args:
            database_url: SQLAlchemy database URL. If None, uses config.DATABASE_URL
        """
        self.database_url = database_url or config.DATABASE_URL

        # Create engine
        if self.database_url.startswith("sqlite"):
            # SQLite-specific configuration for thread safety
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            # PostgreSQL or other databases
            self.engine = create_engine(self.database_url, pool_pre_ping=True)

        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
        print(f"Database tables created successfully at: {self.database_url}")

    def drop_tables(self):
        """Drop all database tables. Use with caution!"""
        Base.metadata.drop_all(bind=self.engine)
        print("All database tables dropped")

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def add_trade(
        self,
        market_id: str,
        strategy: str,
        side: str,
        entry_price: float,
        size_usd: float,
        paper_trade: bool = True,
        market_question: Optional[str] = None,
        outcome: Optional[str] = None,
        confidence_score: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> Trade:
        """
        Add a new trade to the database.

        Returns:
            The created Trade object
        """
        session = self.get_session()
        try:
            trade = Trade(
                market_id=market_id,
                market_question=market_question,
                strategy=strategy,
                side=side,
                outcome=outcome,
                entry_price=Decimal(str(entry_price)),
                size_usd=Decimal(str(size_usd)),
                paper_trade=paper_trade,
                confidence_score=confidence_score,
                notes=notes,
                status="open",
            )
            session.add(trade)
            session.commit()
            session.refresh(trade)
            return trade
        finally:
            session.close()

    def close_trade(
        self,
        trade_id: int,
        exit_price: float,
        gas_cost_usd: Optional[float] = None,
        tx_hash_exit: Optional[str] = None,
    ) -> Trade:
        """
        Close an open trade and calculate P&L.

        Returns:
            The updated Trade object
        """
        session = self.get_session()
        try:
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if not trade:
                raise ValueError(f"Trade {trade_id} not found")

            trade.exit_price = Decimal(str(exit_price))
            trade.exit_time = datetime.utcnow()

            # Calculate duration
            if trade.entry_time:
                duration = trade.exit_time - trade.entry_time
                trade.duration_seconds = int(duration.total_seconds())

            # Calculate P&L
            if trade.side == "YES":
                pnl = (float(trade.exit_price) - float(trade.entry_price)) * float(trade.size_usd)
            else:  # NO
                pnl = (float(trade.entry_price) - float(trade.exit_price)) * float(trade.size_usd)

            trade.profit_loss_usd = Decimal(str(pnl))
            trade.profit_loss_pct = (pnl / float(trade.size_usd)) * 100 if trade.size_usd else 0

            # Calculate net profit after gas
            if gas_cost_usd:
                trade.gas_cost_usd = Decimal(str(gas_cost_usd))
                trade.net_profit_usd = Decimal(str(pnl - gas_cost_usd))
            else:
                trade.net_profit_usd = trade.profit_loss_usd

            trade.tx_hash_exit = tx_hash_exit
            trade.status = "closed"

            session.commit()
            session.refresh(trade)
            return trade
        finally:
            session.close()

    def add_market_snapshot(
        self,
        market_id: str,
        price_yes: float,
        price_no: float,
        market_question: Optional[str] = None,
        volume_24h: Optional[float] = None,
        liquidity_usd: Optional[float] = None,
        comment_sentiment: Optional[float] = None,
        whale_activity_score: Optional[float] = None,
    ) -> MarketSnapshot:
        """Add a market data snapshot."""
        session = self.get_session()
        try:
            snapshot = MarketSnapshot(
                market_id=market_id,
                market_question=market_question,
                price_yes=Decimal(str(price_yes)),
                price_no=Decimal(str(price_no)),
                volume_24h=Decimal(str(volume_24h)) if volume_24h else None,
                liquidity_usd=Decimal(str(liquidity_usd)) if liquidity_usd else None,
                comment_sentiment=comment_sentiment,
                whale_activity_score=whale_activity_score,
            )
            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)
            return snapshot
        finally:
            session.close()

    def add_alert(
        self,
        alert_type: str,
        title: str,
        message: str,
        severity: str = "info",
        market_id: Optional[str] = None,
        trade_id: Optional[int] = None,
        strategy: Optional[str] = None,
    ) -> Alert:
        """Create a new alert."""
        session = self.get_session()
        try:
            alert = Alert(
                alert_type=alert_type,
                severity=severity,
                title=title,
                message=message,
                market_id=market_id,
                trade_id=trade_id,
                strategy=strategy,
            )
            session.add(alert)
            session.commit()
            session.refresh(alert)
            return alert
        finally:
            session.close()

    def get_strategy_settings(self, strategy_name: str) -> Optional[StrategySettings]:
        """Get settings for a specific strategy."""
        session = self.get_session()
        try:
            settings = session.query(StrategySettings).filter(
                StrategySettings.strategy_name == strategy_name
            ).first()
            return settings
        finally:
            session.close()

    def update_strategy_settings(
        self,
        strategy_name: str,
        endgame_min_price: Optional[float] = None,
        endgame_max_price: Optional[float] = None,
        endgame_max_hours_to_settlement: Optional[int] = None,
        endgame_min_confidence: Optional[float] = None,
        enabled: Optional[bool] = None,
        min_profit_threshold_pct: Optional[float] = None,
        trigger_scan: bool = False,
    ) -> StrategySettings:
        """Update or create strategy settings."""
        session = self.get_session()
        try:
            settings = session.query(StrategySettings).filter(
                StrategySettings.strategy_name == strategy_name
            ).first()

            if not settings:
                # Create new settings with defaults
                settings = StrategySettings(strategy_name=strategy_name)
                session.add(settings)

            # Update provided fields
            if endgame_min_price is not None:
                settings.endgame_min_price = endgame_min_price
            if endgame_max_price is not None:
                settings.endgame_max_price = endgame_max_price
            if endgame_max_hours_to_settlement is not None:
                settings.endgame_max_hours_to_settlement = endgame_max_hours_to_settlement
            if endgame_min_confidence is not None:
                settings.endgame_min_confidence = endgame_min_confidence
            if enabled is not None:
                settings.enabled = enabled
            if min_profit_threshold_pct is not None:
                settings.min_profit_threshold_pct = min_profit_threshold_pct

            # Set scan trigger if requested
            if trigger_scan:
                settings.scan_requested = True

            settings.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(settings)
            return settings
        finally:
            session.close()

    def check_scan_requested(self, strategy_name: str = "endgame_sweep") -> bool:
        """Check if a manual scan was requested and clear the flag."""
        session = self.get_session()
        try:
            settings = session.query(StrategySettings).filter(
                StrategySettings.strategy_name == strategy_name
            ).first()

            if settings and settings.scan_requested:
                # Clear the flag
                settings.scan_requested = False
                session.commit()
                return True
            return False
        finally:
            session.close()


# Global database instance
db = DatabaseManager()


if __name__ == "__main__":
    # Initialize database
    print("Creating database tables...")
    db.create_tables()
    print("Database initialization complete!")

    # Test adding a trade
    print("\nTesting trade creation...")
    trade = db.add_trade(
        market_id="test_market_123",
        market_question="Will Bitcoin reach $100k in 2025?",
        strategy="endgame_sweep",
        side="YES",
        entry_price=0.96,
        size_usd=100.0,
        paper_trade=True,
        confidence_score=0.85,
        notes="Test trade",
    )
    print(f"Created trade: {trade}")

    # Test closing the trade
    print("\nTesting trade closure...")
    closed_trade = db.close_trade(
        trade_id=trade.id, exit_price=1.0, gas_cost_usd=0.50
    )
    print(f"Closed trade with P&L: ${closed_trade.net_profit_usd}")

    print("\nDatabase testing complete!")
