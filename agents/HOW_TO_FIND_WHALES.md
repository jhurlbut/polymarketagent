# 🐋 How Railway Deployment Finds Whales

## ⚠️ Current State: Manual Entry Required

**The deployed system does NOT automatically find whales yet.** You need to manually add whale addresses to the database. Here are your options:

---

## Option 1: Manual Entry (Works NOW) ✅

This is the **only working method** currently. You manually research and add successful traders.

### Step 1: Find Whales on Polymarket

#### A. Polymarket Leaderboard
1. Visit https://polymarket.com/leaderboard
2. Look at top traders by:
   - Total volume
   - Profit (if shown)
   - Number of trades
3. Click on traders to see their profile
4. Copy their Ethereum address

#### B. High-Volume Markets
1. Browse popular markets: https://polymarket.com
2. Look for markets with high volume ($100k+)
3. Click "Order Book" or "Recent Trades"
4. Note addresses making large trades (>$5k)
5. Track those addresses across multiple markets

#### C. Social Media Research
1. Search Twitter/X for "Polymarket"
2. Find users posting about their big wins
3. Many include their wallet address in bio
4. Verify they're actually profitable before adding

### Step 2: Add Whales to Railway Database

#### Method A: Via Railway Shell
```bash
# SSH into Railway container
railway run bash

# Run Python
python3

# Add whale
from agents.application.whale import WhaleMonitor
monitor = WhaleMonitor()

whale = monitor.add_whale(
    address="0xabc123...",  # Address you found
    nickname="Top Politics Trader",
    quality_score=0.75,  # Initial estimate
    whale_type="smart_money",
    track=True
)
```

#### Method B: Create CSV and Import
Create `whales.csv`:
```csv
address,nickname,specialization,quality_score,whale_type
0xabc123...,Top Politics Trader,politics,0.75,smart_money
0xdef456...,Crypto Whale,crypto,0.82,smart_money
0x789abc...,Sports Expert,sports,0.70,smart_money
```

Upload to Railway and import:
```bash
railway run python3 << 'EOF'
from agents.application.whale import WhaleMonitor
import csv

monitor = WhaleMonitor()

with open('whales.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        monitor.add_whale(
            address=row['address'],
            nickname=row['nickname'],
            quality_score=float(row['quality_score']),
            whale_type=row['whale_type'],
            track=True
        )
        print(f"Added: {row['nickname']}")
EOF
```

### Step 3: Strategy Starts Copying

Once whales are in the database, the strategy will:
1. ✅ Monitor those whales for new positions (via Polymarket API)
2. ✅ Generate signals when they trade
3. ✅ Copy trades after 5-minute delay
4. ✅ Use Kelly sizing based on whale quality

**Limitation:** You need to manually monitor and add new whales as you discover them.

---

## Option 2: Polymarket API Monitoring (Recommended Future) 🚧

**Status:** Not implemented, but EASIEST to build

### How It Would Work

```python
# Poll Polymarket API every 5 minutes
while True:
    # Get all active markets
    markets = polymarket_api.get_markets()

    for market in markets:
        # Get recent trades
        trades = polymarket_api.get_market_trades(market.id, limit=100)

        for trade in trades:
            # Look for large trades (>$5k)
            if trade.size_usd >= 5000:
                # Check if trader is known
                whale = monitor.get_whale(trade.trader_address)

                if not whale:
                    # New whale - add to database
                    whale = monitor.add_whale(
                        address=trade.trader_address,
                        track=False  # Don't copy yet
                    )

                # Record transaction
                record_transaction(trade)

                # Generate signal if whale is tracked
                if whale.is_tracked and whale.quality_score >= 0.70:
                    signal_generator.generate_entry_signal(...)

    time.sleep(300)  # Wait 5 minutes
```

### To Implement

1. **Find Polymarket API endpoints:**
   - Trades: `GET /trades?market={id}`
   - Markets: `GET /markets`
   - Orderbook: `GET /book?market={id}`

2. **Add to `run_trading_system.py`:**
```python
# Start API monitor in background thread
from agents.application.whale.blockchain_monitor import start_api_monitoring
import threading

api_thread = threading.Thread(target=start_api_monitoring, daemon=True)
api_thread.start()
```

3. **Deploy to Railway:**
   - Runs continuously in background
   - Auto-discovers new whales
   - Generates signals in real-time

**Pros:**
- ✅ Easier than blockchain parsing
- ✅ More reliable (official API)
- ✅ Lower resource usage

**Cons:**
- ❌ Requires finding/documenting Polymarket API
- ❌ API might have rate limits
- ❌ Delayed compared to blockchain

---

## Option 3: Blockchain Monitoring (Advanced Future) 🚧

**Status:** Not implemented, HARDEST to build

### How It Would Work

```python
from web3 import Web3

# Connect to Polygon
w3 = Web3(Web3.WebsocketProvider(config.POLYGON_WSS_URL))

# Load CTF Exchange contract
ctf_exchange = w3.eth.contract(
    address=config.CTF_EXCHANGE_ADDRESS,
    abi=CTF_EXCHANGE_ABI
)

# Listen for OrderFilled events
event_filter = ctf_exchange.events.OrderFilled.createFilter(fromBlock='latest')

while True:
    for event in event_filter.get_new_entries():
        # Parse transaction
        trader = event['args']['maker']
        size_usd = calculate_usd_value(event['args']['amount'], event['args']['price'])

        # Check if whale-sized (>$5k)
        if size_usd >= 5000:
            # Add to database or update existing
            process_whale_transaction(trader, event)

            # Generate signal if tracked
            if is_tracked_whale(trader):
                generate_signal(trader, event)
```

### To Implement

1. **Get Polygon RPC endpoint:**
   - Infura: https://infura.io
   - Alchemy: https://alchemy.com
   - QuickNode: https://quicknode.com
   - Add to `.env`: `POLYGON_WSS_URL=wss://...`

2. **Get CTF Exchange ABI:**
   - Find contract on Polygonscan
   - Download ABI JSON
   - Add to codebase

3. **Parse events:**
   - OrderFilled
   - OrderCancelled
   - Transfer events

4. **Calculate USD values:**
   - Convert token amounts to USD
   - Account for price and fees

**Pros:**
- ✅ Real-time (fastest)
- ✅ Complete data
- ✅ No API dependencies

**Cons:**
- ❌ Complex to implement
- ❌ Requires paid RPC endpoint
- ❌ High resource usage
- ❌ Need to maintain contract ABIs

---

## Comparison

| Method | Status | Difficulty | Speed | Cost | Best For |
|--------|--------|------------|-------|------|----------|
| **Manual Entry** | ✅ Works Now | Easy | Slow | Free | Testing, small scale |
| **Polymarket API** | 🚧 Future | Medium | 5 min delay | Free | Production (recommended) |
| **Blockchain** | 🚧 Future | Hard | Real-time | Paid RPC | High-frequency, enterprise |

---

## Recommended Approach

### Phase 1: Manual (NOW)
1. Research top traders on Polymarket
2. Add 5-10 high-quality whales manually
3. Let strategy run and prove itself
4. Monitor performance for 1-2 weeks

### Phase 2: API Monitoring (Next)
1. Find Polymarket API endpoints
2. Implement `PolymarketAPIMonitor`
3. Auto-discover new whales
4. Still review and approve before tracking

### Phase 3: Blockchain (Future)
1. Only if you need real-time (< 1 min delay)
2. Or if Polymarket API is unreliable
3. Higher operational cost/complexity

---

## Current Workflow on Railway

### When Deployed NOW (Manual Mode)

```
Railway Deployment
├── Database (PostgreSQL)
│   ├── whales (empty initially)
│   ├── whale_signals (empty)
│   └── trades
│
├── Whale Following Strategy (enabled)
│   ├── ✅ Loads whales from database
│   ├── ✅ Monitors for signals
│   ├── ✅ Executes copy trades
│   └── ⚠️ No whales = no opportunities
│
└── Manual Management (you)
    ├── Research whales on Polymarket
    ├── Add via Railway shell/CSV
    └── Monitor and add more as needed
```

### Finding 0 Opportunities? Normal!

When you first deploy with whale strategy enabled, you'll see:
```
✓ Registered: Whale Following Strategy
Tracking 0 whales
Found 0 whale following opportunities
```

This is **expected** - you haven't added any whales yet!

---

## Quick Start: Add Your First Whales

### 1. Find Whales on Polymarket
Visit https://polymarket.com/leaderboard and note top 3 addresses

### 2. Add to Railway
```bash
railway shell

python3 << 'EOF'
from agents.application.whale import WhaleMonitor

monitor = WhaleMonitor()

# Add 3 whales (replace with real addresses)
whales_to_add = [
    {
        "address": "0x1111111111111111111111111111111111111111",
        "nickname": "Top Politics Trader",
        "quality_score": 0.80,
        "whale_type": "smart_money",
        "specialization": "politics"
    },
    {
        "address": "0x2222222222222222222222222222222222222222",
        "nickname": "Crypto Expert",
        "quality_score": 0.75,
        "whale_type": "smart_money",
        "specialization": "crypto"
    },
    {
        "address": "0x3333333333333333333333333333333333333333",
        "nickname": "All-Around Winner",
        "quality_score": 0.78,
        "whale_type": "smart_money",
        "specialization": None
    }
]

for w in whales_to_add:
    whale = monitor.add_whale(
        address=w["address"],
        nickname=w["nickname"],
        quality_score=w["quality_score"],
        whale_type=w["whale_type"],
        track=True
    )
    print(f"✓ Added: {whale.nickname}")

print(f"\nTotal tracked whales: {len(whales_to_add)}")
EOF
```

### 3. Verify
```bash
railway logs
```

Should show:
```
Tracking 3 whales (3 smart money, avg quality: 0.78)
```

### 4. Monitor Dashboard
Your Streamlit dashboard will now show whale signals when those traders make new moves!

---

## Building Automated Detection (For Later)

I've created a placeholder at `agents/application/whale/blockchain_monitor.py` showing the architecture.

To implement:
1. Choose API or Blockchain approach
2. Fill in the placeholder functions
3. Add background thread to `run_trading_system.py`
4. Test locally first
5. Deploy to Railway

**For now, manual entry is sufficient** and lets you control exactly which whales to follow.

---

## Questions?

**"How often should I add new whales?"**
- Start with 5-10 high-quality whales
- Add more as you discover them (weekly/monthly)
- Quality > Quantity

**"How do I know if a whale is good?"**
- Check their history on Polymarket
- Look for consistent big trades
- Verify they're profitable (if data available)
- Start with lower quality score (0.70) until proven

**"Will automated detection be added?"**
- Yes, likely via Polymarket API
- Not critical for MVP
- Manual works fine for 10-50 whales

**"Can I import a large list of whales?"**
- Yes, via CSV import method above
- Don't track all immediately
- Score them first, track best ones
