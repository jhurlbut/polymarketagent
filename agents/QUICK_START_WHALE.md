# 🐋 Whale Following Strategy - Quick Start

## See It In Action (3 Steps)

### Step 1: Seed Test Data
This creates 5 test whales and 6 trading signals in your database:

```bash
cd /Users/jbass/polymarketagent/agents
python3 seed_test_whales.py
```

**What it creates:**
- ✅ **3 Smart Money Whales** (quality score >= 0.75) - These WILL be copied
  - "The Oracle" - 86% win rate, politics specialist
  - "Crypto Whale" - 80% win rate, crypto specialist
  - "Sports Savant" - 75% win rate, sports specialist

- ⚠️ **1 Neutral Whale** (quality 0.68) - Below threshold, will be SKIPPED
  - "Market Maker Mike" - 65% win rate, no specialization

- ❌ **1 Dumb Money Whale** (quality 0.35) - Way below threshold, will be SKIPPED
  - "FOMO Trader" - 40% win rate, no specialization

**Result:** 4 copyable signals from smart money whales, 2 signals that will be skipped

### Step 2: Test The Strategy
Run the whale following strategy to see it copy the high-quality whales:

```bash
python3 test_whale_strategy.py
```

**What happens:**
1. Finds all copyable signals (quality >= 0.70)
2. Shows you which whales it will copy
3. Calculates position sizes using Kelly Criterion
4. Executes paper trades
5. Shows execution summary

**Expected output:**
```
Found 4 whale following opportunities

Copyable Signals:
1. Copy smart_money whale The Oracle: ENTRY YES @ $0.580 (quality: 0.88)
2. Copy smart_money whale The Oracle: ENTRY NO @ $0.720 (quality: 0.88)
3. Copy smart_money whale Crypto Whale: ENTRY YES @ $0.450 (quality: 0.82)
4. Copy smart_money whale Sports Savant: ENTRY YES @ $0.650 (quality: 0.78)

EXECUTING TRADES (PAPER MODE)
✓ Trade #1 executed
✓ Trade #2 executed
✓ Trade #3 executed
✓ Trade #4 executed

Total Capital Deployed: $XXX.XX
```

### Step 3: View Results in Dashboard
Open the Streamlit dashboard to see your whale-following trades:

```bash
cd /Users/jbass/polymarketagent/agents
python3 -m streamlit run scripts/python/dashboard.py
```

Look for:
- **Recent Trades** - Should show 4 new "whale_following" trades
- **Strategy Performance** - "whale_following" row shows stats
- **Trade History** - Details on each copied position

---

## Enable on Railway (Production)

Once you've tested locally and want to enable on Railway:

### 1. Set Environment Variable
In Railway dashboard:
- Go to your project → **Variables** tab
- Add: `WHALE_TRACKING_ENABLED` = `true`
- Save (auto-redeploys)

### 2. Seed Production Database
SSH into Railway container or run via Railway CLI:

```bash
railway run python3 seed_test_whales.py
```

Or create a one-time job in Railway to run the seeding script.

### 3. Verify in Logs
Check Railway logs for:
```
✓ Registered: Whale Following Strategy
Tracking 5 whales (3 smart money, avg quality: 0.70)
Found 4 whale following opportunities
```

### 4. Monitor Dashboard
Your Streamlit dashboard will show whale-following trades as they execute!

---

## How It Works

### Quality Scoring
Each whale gets scored 0-1 based on:
- **Win Rate (40%)**: Historical win percentage
- **Consistency (20%)**: Profit consistency over time
- **Timing (15%)**: Early vs late entry quality
- **Market Selection (15%)**: Specialization bonus
- **Risk Management (10%)**: Sharpe ratio

### Position Sizing (Kelly Criterion)
```
Position = Bankroll × Kelly Fraction × 0.25

Kelly = (whale_quality × 1 - (1 - whale_quality)) / 1
```

**Constraints:**
- Never more than 50% of whale's position
- Capped at 8% of bankroll (WHALE_MAX_POSITION_PCT)
- Minimum $5 position

### Copy Delay
5-minute delay (WHALE_COPY_DELAY_SECONDS) between whale entry and our copy to:
- Avoid front-running detection
- Allow price to stabilize
- Verify whale commitment

### Safety Checks
Before copying, the strategy verifies:
- ✅ Whale quality >= 0.70 (WHALE_MIN_QUALITY_SCORE)
- ✅ No existing position in same market
- ✅ Price hasn't moved >5% since whale entry
- ✅ Slippage < 2% tolerance
- ✅ Risk manager validation passes

---

## Configuration Options

All optional - these are the defaults:

```bash
WHALE_TRACKING_ENABLED=true          # Enable/disable strategy
WHALE_MIN_QUALITY_SCORE=0.70         # Only copy whales >= 0.70 quality
WHALE_COPY_DELAY_SECONDS=300         # Wait 5 minutes before copying
WHALE_MAX_POSITION_PCT=8             # Max 8% of bankroll per position
WHALE_MIN_VOLUME_USD=50000           # Min volume to qualify as whale
```

---

## Next Steps

### Build Real Whale Database
Replace test whales with real high-performers:

1. **Manual Research**: Find successful traders on Polymarket
2. **Historical Analysis**: Analyze their past positions
3. **Quality Scoring**: Run scorer to validate quality
4. **Track**: Add to database with `is_tracked=True`

### Blockchain Monitoring (Future)
Real-time whale detection from Polygon blockchain:

```python
# Future enhancement - monitor CTF Exchange
# Parse transactions > $5k
# Auto-score and track new whales
# Generate signals in real-time
```

### Dashboard Enhancement
Add whale-specific views:
- Whale leaderboard
- Signal feed
- Whale vs whale performance comparison
- Copy trade analytics

---

## Troubleshooting

**"Found 0 opportunities"**
- Run `python3 seed_test_whales.py` first
- Check whales exist: `SELECT * FROM whales WHERE is_tracked=true`
- Verify signals: `SELECT * FROM whale_signals WHERE status='pending'`

**"Trade not executed"**
- Check risk manager limits (daily loss, position size)
- Review logs for validation errors
- Ensure PAPER_TRADING_MODE=true

**Low position sizes**
- Strategy uses conservative 25% Kelly
- Increases with whale quality score
- Check WHALE_MAX_POSITION_PCT setting

---

**Status:** ✅ Ready to Test | 🧪 Run Scripts Above | 🚀 Deploy to Railway

**Questions?** Check `WHALE_STRATEGY_TESTING.md` for full documentation.
