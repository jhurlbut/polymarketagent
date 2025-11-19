# 🚀 Run Polymarket Trading System Locally

## Quick Local Test (5 Minutes)

### Step 1: Install Dependencies
```bash
cd /Users/jbass/polymarketagent/agents
pip3 install -r requirements.txt
```

### Step 2: Setup Test Database & Whale Data
```bash
# Seed test whales and signals
python3 seed_test_whales.py
```

Press `y` when prompted. This creates:
- 5 test whales (3 smart money, 1 neutral, 1 dumb money)
- 6 test signals (4 copyable)

### Step 3: Run Trading System
```bash
# Test mode - find opportunities without executing
python3 run_trading_system.py --test

# Or execute in paper trading mode
python3 run_trading_system.py
```

You should see:
```
POLYMARKET TRADING SYSTEM
==============================================================
Registering strategies...
✓ Registered: Endgame Sweep Strategy
⊗ Whale Following Strategy disabled (WHALE_TRACKING_ENABLED=false)

EXECUTING STRATEGIES
...
Found 0 endgame sweep opportunities (no live markets with test data)
```

### Step 4: Enable Whale Strategy
Create or edit `.env` file:

```bash
# Create .env file
cat > .env << 'EOF'
# Paper Trading Mode (REQUIRED for local testing)
PAPER_TRADING_MODE=true

# Enable Whale Strategy
WHALE_TRACKING_ENABLED=true

# Database (uses local SQLite by default)
DATABASE_URL=sqlite:///polymarket_trading.db

# Optional: Add API keys if you want to test with live markets
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
EOF
```

### Step 5: Run Again With Whale Strategy
```bash
python3 run_trading_system.py
```

Now you should see:
```
Registering strategies...
✓ Registered: Endgame Sweep Strategy
✓ Registered: Whale Following Strategy
Tracking 5 whales (3 smart money, avg quality: 0.70)

EXECUTING STRATEGIES
==============================================================

Running strategy: endgame_sweep
  Found 0 endgame sweep opportunities

Running strategy: whale_following
  Found 4 whale following opportunities

  1. Copy smart_money whale The Oracle: ENTRY YES @ $0.580
  2. Copy smart_money whale The Oracle: ENTRY NO @ $0.720
  3. Copy smart_money whale Crypto Whale: ENTRY YES @ $0.450
  4. Copy smart_money whale Sports Savant: ENTRY YES @ $0.650

PAPER TRADE: Would copy whale The Oracle: buy XX.XX USDC of YES @ 0.580
✓ Trade #1 executed
...

Total trades executed: 4
Total capital deployed: $XXX.XX
```

### Step 6: View in Dashboard
```bash
python3 -m streamlit run scripts/python/dashboard.py
```

Opens browser at http://localhost:8501

Check:
- **Recent Trades** - Should show 4 whale_following trades
- **Strategy Performance** - Both strategies listed
- **Settings** - Adjust endgame sweep parameters

---

## Test Individual Strategies

### Test Only Whale Following
```bash
python3 test_whale_strategy.py
```

Shows detailed output:
- Copyable signals found
- Position sizing calculations
- Execution results
- Signal status

### Test Only Endgame Sweep
```bash
python3 run_trading_system.py --strategy endgame_sweep --test
```

Note: Won't find opportunities with test data (needs live Polymarket markets)

---

## Configuration Options

Edit `.env` file:

```bash
# === Core Settings ===
PAPER_TRADING_MODE=true                    # Always true for local testing
DATABASE_URL=sqlite:///polymarket_trading.db  # Local SQLite database

# === Whale Following ===
WHALE_TRACKING_ENABLED=true
WHALE_MIN_QUALITY_SCORE=0.70               # Only copy whales >= 0.70
WHALE_COPY_DELAY_SECONDS=300               # 5 minute delay
WHALE_MAX_POSITION_PCT=8                   # Max 8% of bankroll

# === Endgame Sweep ===
ENDGAME_MIN_PRICE=0.95                     # Min price (0.95-0.99 range)
ENDGAME_MAX_PRICE=0.99
ENDGAME_MAX_TIME_TO_SETTLEMENT_HOURS=24    # Only markets settling in 24h

# === Risk Management ===
MAX_POSITION_SIZE_PCT=10                   # Max position size
DAILY_LOSS_LIMIT_PCT=5                     # Max 5% daily loss
MIN_PROFIT_THRESHOLD_PCT=0.3               # Min 0.3% profit to execute

# === API Keys (Optional - for live market data) ===
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
```

---

## Understanding the Output

### Whale Following Strategy
```
Found 4 whale following opportunities

Copyable Signals:
1. Copy smart_money whale The Oracle: ENTRY YES @ $0.580 (quality: 0.88)
   Whale: The Oracle (smart_money)
   Quality Score: 0.88
   Market: 0x1234567890...
   Position: YES @ $0.580
   Whale Size: $25,000.00
   Confidence: 0.88
   Expected Profit: 72.41%

Executing: The Oracle signal...
PAPER TRADE: Would copy whale The Oracle: buy 45.23 USDC of YES @ 0.580
✓ Trade #1 executed
```

**Key metrics:**
- **Quality Score**: Whale's overall quality (0-1)
- **Whale Size**: How much the whale bet
- **Our Position**: Calculated via Kelly Criterion (usually much smaller)
- **Expected Profit %**: If outcome resolves to 1.0

### Endgame Sweep Strategy
```
Found 0 endgame sweep opportunities
```

**Why zero?**
- Test data doesn't include live Polymarket markets
- Needs real markets priced 0.95-0.99 near settlement
- To test with live data, add API keys to `.env`

---

## Test With Live Polymarket Data

### Option 1: Read-Only Testing
Just view opportunities without API keys:

```bash
# No API keys needed for read-only
python3 run_trading_system.py --test
```

Strategy will scan real Polymarket markets and show opportunities.

### Option 2: Paper Trading With Live Data
Add AI API keys to improve market analysis:

```bash
# Add to .env
ANTHROPIC_API_KEY=sk-ant-...
# or
OPENAI_API_KEY=sk-...
```

Then run:
```bash
python3 run_trading_system.py
```

This scans **real Polymarket markets** and executes **paper trades** (fake money, real strategy).

---

## Viewing Results

### Option 1: Streamlit Dashboard
```bash
python3 -m streamlit run scripts/python/dashboard.py
```

Interactive web interface showing:
- Recent trades
- Strategy performance
- Live settings control
- Trade history

### Option 2: Database Queries
```bash
python3
```

```python
from agents.utils.database import db

# Get all trades
trades = db.get_recent_trades(limit=10)
for t in trades:
    print(f"Trade #{t.id}: {t.strategy} - {t.side} @ ${float(t.entry_price):.3f}")

# Get whale trades only
whale_trades = db.get_trades_by_strategy("whale_following")
print(f"Whale following trades: {len(whale_trades)}")

# Get whale stats
from agents.application.whale import WhaleMonitor
monitor = WhaleMonitor()
stats = monitor.get_summary_stats()
print(stats)
```

### Option 3: Check Logs
All output is logged to `polymarket_trading.log`:

```bash
tail -f polymarket_trading.log
```

---

## Troubleshooting

### "ModuleNotFoundError"
```bash
pip3 install -r requirements.txt
```

### "No whale opportunities found"
Make sure you ran seeding:
```bash
python3 seed_test_whales.py
```

Check database:
```bash
sqlite3 polymarket_trading.db "SELECT COUNT(*) FROM whales;"
sqlite3 polymarket_trading.db "SELECT COUNT(*) FROM whale_signals WHERE status='pending';"
```

### "Whale strategy disabled"
Check `.env` file has:
```bash
WHALE_TRACKING_ENABLED=true
```

### "Database locked"
Close other connections:
```bash
# Kill any Python processes
pkill -f python

# Or use PostgreSQL instead of SQLite for multi-user
DATABASE_URL=postgresql://user:pass@localhost/polymarket
```

### Position sizes too small
Adjust in `.env`:
```bash
WHALE_MAX_POSITION_PCT=15    # Increase from 8% to 15%
```

Or adjust risk manager bankroll (default $10,000 for paper trading).

---

## File Structure

```
agents/
├── run_trading_system.py          # Main entry point
├── test_whale_strategy.py         # Test whale strategy only
├── seed_test_whales.py            # Create test data
├── .env                           # Your configuration
├── polymarket_trading.db          # SQLite database (created on first run)
├── polymarket_trading.log         # Execution logs
│
├── agents/
│   ├── application/
│   │   ├── strategies/
│   │   │   ├── endgame_sweep.py       # Endgame sweep strategy
│   │   │   └── whale_following.py     # Whale following strategy
│   │   ├── whale/
│   │   │   ├── monitor.py             # Whale tracker
│   │   │   ├── scorer.py              # Quality scoring
│   │   │   └── signals.py             # Signal generator
│   │   ├── risk_manager.py
│   │   └── strategy_manager.py
│   └── utils/
│       ├── database.py                # Database models
│       └── config.py                  # Configuration
│
└── scripts/
    └── python/
        ├── dashboard.py               # Streamlit dashboard
        └── find_whales.py            # Whale finder tool
```

---

## Next Steps

1. **✅ Run locally** - Test with paper trading
2. **📊 Adjust settings** - Tune via dashboard or `.env`
3. **🐋 Find real whales** - Use `python3 scripts/python/find_whales.py`
4. **🚀 Deploy to Railway** - Push with `WHALE_TRACKING_ENABLED=true`
5. **📈 Monitor performance** - Watch dashboard and logs

---

## Quick Commands Reference

```bash
# Seed test data
python3 seed_test_whales.py

# Run all strategies (paper trading)
python3 run_trading_system.py

# Test mode (no execution)
python3 run_trading_system.py --test

# Specific strategy
python3 run_trading_system.py --strategy whale_following

# Test whale strategy only
python3 test_whale_strategy.py

# Open dashboard
python3 -m streamlit run scripts/python/dashboard.py

# Find whales
python3 scripts/python/find_whales.py

# View logs
tail -f polymarket_trading.log

# Check database
sqlite3 polymarket_trading.db
> SELECT * FROM whales;
> SELECT * FROM whale_signals;
> SELECT * FROM trades ORDER BY created_at DESC LIMIT 5;
```

---

**Status:** ✅ Ready to Run | 🧪 Paper Trading Mode | 💰 No Real Money at Risk
