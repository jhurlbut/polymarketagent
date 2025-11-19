#!/bin/bash
# ============================================================================
# Polymarket Trading System - Quick Setup & Test
# ============================================================================
# This script sets up the trading system and runs a test with whale strategy
#
# Usage:
#   chmod +x setup_and_test.sh
#   ./setup_and_test.sh

set -e  # Exit on error

echo "======================================================================"
echo "POLYMARKET TRADING SYSTEM - SETUP & TEST"
echo "======================================================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Create .env file
echo -e "\n${YELLOW}Step 1: Creating .env file...${NC}"
if [ -f .env ]; then
    echo "⚠️  .env file already exists, skipping"
else
    cat > .env << 'ENVEOF'
# Polymarket Trading System Configuration
PAPER_TRADING_MODE=true
WHALE_TRACKING_ENABLED=true
DATABASE_URL=sqlite:///polymarket_trading.db

# Whale Strategy Settings
WHALE_MIN_QUALITY_SCORE=0.70
WHALE_COPY_DELAY_SECONDS=300
WHALE_MAX_POSITION_PCT=8

# Endgame Sweep Settings
ENDGAME_MIN_PRICE=0.95
ENDGAME_MAX_PRICE=0.99
ENDGAME_MAX_TIME_TO_SETTLEMENT_HOURS=24

# Risk Management
MAX_POSITION_SIZE_PCT=10
MIN_PROFIT_THRESHOLD_PCT=0.3
DAILY_LOSS_LIMIT_PCT=5
ENVEOF
    echo -e "${GREEN}✓ Created .env file${NC}"
fi

# Step 2: Check Python
echo -e "\n${YELLOW}Step 2: Checking Python installation...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Found $PYTHON_VERSION${NC}"
else
    echo "✗ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Step 3: Install dependencies
echo -e "\n${YELLOW}Step 3: Installing dependencies...${NC}"
echo "This may take a few minutes..."
pip3 install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 4: Seed test data
echo -e "\n${YELLOW}Step 4: Seeding test whale data...${NC}"
python3 seed_test_whales.py << 'SEEDEOF'
y
SEEDEOF
echo -e "${GREEN}✓ Test data seeded${NC}"

# Step 5: Run whale strategy test
echo -e "\n${YELLOW}Step 5: Testing whale following strategy...${NC}"
python3 test_whale_strategy.py

# Success
echo ""
echo "======================================================================"
echo -e "${GREEN}✓ SETUP COMPLETE!${NC}"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "  1. View results in dashboard:"
echo "     python3 -m streamlit run scripts/python/dashboard.py"
echo ""
echo "  2. Run full trading system:"
echo "     python3 run_trading_system.py"
echo ""
echo "  3. Find real whales:"
echo "     python3 scripts/python/find_whales.py"
echo ""
echo "======================================================================"
