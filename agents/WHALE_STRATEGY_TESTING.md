# Whale Following Strategy - Testing Guide

## Overview
The Whale Following Strategy has been successfully implemented and integrated into the Polymarket trading system. This guide explains how to test it in paper trading mode.

## Implementation Summary

### Files Created
1. **Database Models** (`agents/utils/database.py`)
   - `Whale`: Whale trader registry with performance metrics
   - `WhalePosition`: Current whale positions in active markets
   - `WhaleTransaction`: Historical whale transactions
   - `WhaleSignal`: Copy-trading signals generated from whale activity

2. **Migration Script** (`migrate_add_whale_tables.py`)
   - Creates whale tracking database tables

3. **Whale Tracking Modules** (`agents/application/whale/`)
   - `monitor.py`: WhaleMonitor - Real-time whale activity tracking
   - `scorer.py`: WhaleScorer - Multi-factor quality scoring algorithm
   - `signals.py`: WhaleSignalGenerator - Copy-trading signal generation

4. **Strategy Implementation** (`agents/application/strategies/whale_following.py`)
   - `WhaleFollowingStrategy`: Main strategy class
   - Kelly Criterion position sizing
   - Signal filtering and validation
   - Risk-adjusted copy trading

5. **System Integration** (`run_trading_system.py`)
   - Conditional strategy registration based on `WHALE_TRACKING_ENABLED` config

## Configuration

Add these environment variables to your `.env` file:

```bash
# Enable whale following strategy
WHALE_TRACKING_ENABLED=true

# Whale tracking parameters
WHALE_MIN_VOLUME_USD=50000         # Minimum trading volume to qualify as whale
WHALE_MIN_QUALITY_SCORE=0.70       # Minimum quality score (0-1) to copy
WHALE_COPY_DELAY_SECONDS=300       # 5 minutes delay before copying
WHALE_MAX_POSITION_PCT=8           # Max position size as % of bankroll

# Polygon blockchain (for future whale monitoring)
POLYGON_WSS_URL=wss://polygon-rpc.com
```

## Testing Procedure

### Step 1: Install Dependencies
```bash
cd /Users/jbass/polymarketagent/agents
pip install -r requirements.txt
```

### Step 2: Run Database Migration
```bash
python3 migrate_add_whale_tables.py
```

This will create the whale tracking tables in your database.

### Step 3: Add Test Whale Data

Create test whales to simulate the strategy:

```python
from agents.utils.database import db, Whale
from datetime import datetime

session = db.get_session()

# Add a high-quality "smart money" whale
smart_whale = Whale(
    address="0x1234567890123456789012345678901234567890",
    nickname="Smart Money Whale",
    total_volume_usd=1000000,
    total_trades=150,
    winning_trades=120,
    losing_trades=30,
    win_rate=80.0,
    quality_score=0.85,
    whale_type="smart_money",
    specialization="politics",
    is_tracked=True,
    first_seen_at=datetime.utcnow(),
    last_activity_at=datetime.utcnow()
)

session.add(smart_whale)
session.commit()
session.close()
```

### Step 4: Generate Test Signals

```python
from agents.application.whale import WhaleSignalGenerator
from decimal import Decimal

signal_gen = WhaleSignalGenerator()

# Create an entry signal
signal = signal_gen.generate_entry_signal(
    whale_address="0x1234567890123456789012345678901234567890",
    market_id="test-market-123",
    side="YES",
    price=0.65,
    size_usd=Decimal("10000"),
    reasoning="Test whale entered position"
)

print(f"Generated signal #{signal.id}")
```

### Step 5: Test Strategy Execution

```bash
# Test mode (find opportunities without executing)
python3 run_trading_system.py --strategy whale_following --test

# Paper trading mode (simulate execution)
python3 run_trading_system.py --strategy whale_following
```

### Step 6: Verify Results

Check the database for executed trades:

```python
from agents.utils.database import db

# Get whale following trades
trades = db.get_trades_by_strategy("whale_following", limit=10)

for trade in trades:
    print(f"Trade #{trade.id}: {trade.side} @ ${trade.entry_price} - ${trade.size_usd}")
```

## Quality Scoring Algorithm

The whale scorer evaluates traders based on:

1. **Win Rate (40%)**: Historical percentage of winning trades
   - Perfect score at 85%+ win rate
   - Linear scaling below 85%

2. **Consistency (20%)**: Profit consistency over time
   - Analyzes weekly profitability patterns
   - Rewards consistent performance

3. **Timing (15%)**: Entry timing quality
   - Measures how early whale enters before price moves
   - Early entries score higher than late entries

4. **Market Selection (15%)**: Specialization quality
   - Rewards whales focused on specific categories
   - Specialists outperform generalists

5. **Risk Management (10%)**: Risk control quality
   - Based on Sharpe ratio when available
   - Lower drawdowns score higher

**Classification:**
- Quality >= 0.75: **Smart Money** (copy these whales)
- Quality 0.50-0.75: **Neutral** (skip or use caution)
- Quality < 0.50: **Dumb Money** (avoid copying)

## Position Sizing: Kelly Criterion

The strategy uses fractional Kelly Criterion for position sizing:

```
Kelly Fraction = (p * b - q) / b

where:
- p = whale quality score (win probability)
- q = 1 - p (loss probability)
- b = odds (assume 1:1 for prediction markets)

Position Size = Bankroll * Kelly Fraction * 0.25 (fractional Kelly)
```

Additional constraints:
- Never exceed whale's position size
- Cap at 50% of whale's position
- Max position size: WHALE_MAX_POSITION_PCT (default 8%)
- Minimum position: $5

## Risk Controls

1. **Copy Delay**: 5-minute default delay to avoid front-running detection
2. **Price Slippage Protection**: Skip if price moved >2% since whale entry
3. **Market Price Change**: Skip if price changed >5% during delay
4. **Duplicate Position Check**: Don't copy if already in same market
5. **Risk Manager Validation**: All trades validated through existing risk manager

## Monitoring

The strategy generates alerts for:
- Whale copy executions (`whale_copy`)
- Execution errors (`error`)
- Signal rejections (logged in whale_signals table)

Check alerts:
```python
from agents.utils.database import db

alerts = db.get_recent_alerts(strategy="whale_following", limit=20)
for alert in alerts:
    print(f"{alert.alert_type}: {alert.title} - {alert.message}")
```

## Dashboard Integration (Future Enhancement)

To add whale following to the Streamlit dashboard:

1. Add whale stats panel showing:
   - Number of tracked whales
   - Smart money vs dumb money distribution
   - Recent whale signals

2. Add whale leaderboard showing top performers

3. Add whale signal feed with copy status

## Production Deployment

When deploying to Railway:

1. **Set Environment Variables**:
   - Add all WHALE_* config variables
   - Ensure PostgreSQL database URL is set

2. **Run Migration**:
   - Migration will auto-run on first deployment
   - Check logs: `railway logs`

3. **Monitor Execution**:
   - Watch for "✓ Registered: Whale Following Strategy"
   - Check for whale copy alerts
   - Monitor trade performance in dashboard

4. **Future: Blockchain Monitoring**:
   - Add WebSocket connection to Polygon
   - Parse real-time CTF exchange transactions
   - Automatically detect and score new whales

## Troubleshooting

### No Opportunities Found
- Check: Are there any tracked whales? `whale_monitor.get_summary_stats()`
- Check: Are there pending signals? `signal_gen.get_pending_signals()`
- Check: Is copy delay configured correctly?

### Signals Not Executing
- Check risk manager limits (daily loss limit, position size limits)
- Check market liquidity and price availability
- Review logs for validation errors

### Low Quality Scores
- Ensure whale has sufficient trade history (10+ trades)
- Check win rate calculation accuracy
- Review consistency scoring over 90-day period

## Next Steps

1. **Build Whale Database**: Manually add known successful traders from Polymarket
2. **Implement Blockchain Monitoring**: Real-time transaction parsing
3. **Backtesting**: Test strategy on historical whale positions
4. **Performance Tracking**: Monitor whale following vs endgame sweep performance
5. **Exit Strategy**: Implement whale exit signal detection

---

## Summary

The Whale Following Strategy is now fully implemented and ready for testing in paper trading mode. Enable it via `WHALE_TRACKING_ENABLED=true` and it will run alongside the existing endgame sweep strategy.

**Key Benefits:**
- Leverages proven whale performance through quality scoring
- Risk-adjusted position sizing via Kelly Criterion
- Built-in safety delays and price protection
- Full integration with existing risk management

**Status:** ✅ Implementation Complete | 🧪 Ready for Paper Trading | 🚀 Production Deployment Pending
