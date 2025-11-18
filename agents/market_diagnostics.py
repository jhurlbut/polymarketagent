#!/usr/bin/env python3
"""
Market Diagnostics - See what the agent is analyzing.

Shows all markets scanned and explains why they were/weren't selected.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.polymarket.polymarket_paper import PolymarketPaper
from agents.utils.config import config
from datetime import datetime

def analyze_markets():
    """Analyze and display market data with filtering explanations."""

    print("=" * 80)
    print("POLYMARKET MARKET DIAGNOSTICS")
    print("=" * 80)
    print()

    # Initialize client
    client = PolymarketPaper()

    print("Fetching markets from Polymarket...")
    markets = client.get_all_tradeable_markets()
    print(f"✓ Retrieved {len(markets)} markets\n")

    # Analysis counters
    endgame_candidates = []
    too_low_price = []
    too_high_price = []
    no_price_data = []
    not_binary = []

    print("Analyzing markets for Endgame Sweep Strategy...")
    print(f"Looking for: ${config.ENDGAME_MIN_PRICE}-${config.ENDGAME_MAX_PRICE} range\n")
    print("-" * 80)

    for i, market in enumerate(markets[:20], 1):  # Show first 20 in detail
        # Handle both dict and object formats
        if isinstance(market, dict):
            question = market.get('question', 'Unknown')
            prices = market.get('outcomePrices', None)
            market_id = market.get('id', 'Unknown')
        else:
            question = getattr(market, 'question', 'Unknown')
            prices = getattr(market, 'outcome_prices', None)
            market_id = getattr(market, 'market_id', 'Unknown')

        # Parse prices if they're strings
        if isinstance(prices, str):
            import json
            try:
                prices = json.loads(prices)
            except:
                prices = None

        print(f"\n{i}. {question[:70]}")
        print(f"   Market ID: {market_id}")

        # Check if binary market
        if not prices or len(prices) != 2:
            print(f"   ⚠️  Not a binary market (has {len(prices) if prices else 0} outcomes)")
            not_binary.append(market)
            continue

        # Convert prices to float
        try:
            yes_price = float(prices[0])
            no_price = float(prices[1])
        except (ValueError, TypeError):
            print(f"   ⚠️  Invalid price data")
            continue

        print(f"   YES: ${yes_price:.3f} | NO: ${no_price:.3f}")

        # Check YES side
        if config.ENDGAME_MIN_PRICE <= yes_price <= config.ENDGAME_MAX_PRICE:
            expected_profit = ((1.0 - yes_price) / yes_price) * 100
            print(f"   ✅ YES QUALIFIES! Expected profit: {expected_profit:.2f}%")
            endgame_candidates.append({
                'market': market,
                'side': 'YES',
                'price': yes_price,
                'profit': expected_profit
            })
        elif yes_price < config.ENDGAME_MIN_PRICE:
            print(f"   ❌ YES too low (${yes_price:.3f} < ${config.ENDGAME_MIN_PRICE})")
            too_low_price.append(market)
        elif yes_price > config.ENDGAME_MAX_PRICE:
            print(f"   ❌ YES too high (${yes_price:.3f} > ${config.ENDGAME_MAX_PRICE})")
            too_high_price.append(market)

        # Check NO side
        if config.ENDGAME_MIN_PRICE <= no_price <= config.ENDGAME_MAX_PRICE:
            expected_profit = ((1.0 - no_price) / no_price) * 100
            print(f"   ✅ NO QUALIFIES! Expected profit: {expected_profit:.2f}%")
            endgame_candidates.append({
                'market': market,
                'side': 'NO',
                'price': no_price,
                'profit': expected_profit
            })
        elif no_price < config.ENDGAME_MIN_PRICE:
            print(f"   ❌ NO too low (${no_price:.3f} < ${config.ENDGAME_MIN_PRICE})")
        elif no_price > config.ENDGAME_MAX_PRICE:
            print(f"   ❌ NO too high (${no_price:.3f} > ${config.ENDGAME_MAX_PRICE})")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nTotal markets scanned: {len(markets)}")
    print(f"First 20 shown in detail above")
    print()
    print(f"✅ Endgame candidates found: {len(endgame_candidates)}")
    print(f"❌ Too low (< $0.95): {len(too_low_price)}")
    print(f"❌ Too high (> $0.99): {len(too_high_price)}")
    print(f"⚠️  Not binary markets: {len(not_binary)}")

    if endgame_candidates:
        print("\n" + "=" * 80)
        print("🎯 ENDGAME SWEEP OPPORTUNITIES")
        print("=" * 80)
        for i, opp in enumerate(endgame_candidates, 1):
            market = opp['market']
            if isinstance(market, dict):
                question = market.get('question', 'Unknown')
            else:
                question = getattr(market, 'question', 'Unknown')
            print(f"\n{i}. {question[:70]}")
            print(f"   Side: {opp['side']}")
            print(f"   Price: ${opp['price']:.3f}")
            print(f"   Expected Profit: {opp['profit']:.2f}%")
    else:
        print("\n" + "=" * 80)
        print("💡 WHY NO OPPORTUNITIES?")
        print("=" * 80)
        print("\nEndgame sweep requires VERY specific conditions:")
        print("  1. Market priced $0.95-$0.99 (near-certain outcome)")
        print("  2. Market settling soon (< 24 hours)")
        print("  3. Low black swan risk (< 30%)")
        print("  4. No manipulation detected")
        print()
        print("This is GOOD! The strategy is conservative and waits for")
        print("perfect opportunities to minimize risk and maximize profit.")
        print()
        print("🔄 Try running again at different times of day, especially:")
        print("  - Right after major events (elections, sports)")
        print("  - During high-volume trading hours")
        print("  - When new markets are about to settle")

    # Show price distribution
    print("\n" + "=" * 80)
    print("PRICE DISTRIBUTION (All Markets)")
    print("=" * 80)

    price_ranges = {
        '0.00-0.10': 0,
        '0.10-0.30': 0,
        '0.30-0.50': 0,
        '0.50-0.70': 0,
        '0.70-0.90': 0,
        '0.90-0.95': 0,
        '0.95-0.99': 0,  # Our target!
        '0.99-1.00': 0,
    }

    for market in markets:
        # Handle both dict and object formats
        if isinstance(market, dict):
            prices = market.get('outcomePrices', None)
        else:
            prices = getattr(market, 'outcome_prices', None)

        if prices and len(prices) == 2:
            for price in prices:
                if price < 0.10:
                    price_ranges['0.00-0.10'] += 1
                elif price < 0.30:
                    price_ranges['0.10-0.30'] += 1
                elif price < 0.50:
                    price_ranges['0.30-0.50'] += 1
                elif price < 0.70:
                    price_ranges['0.50-0.70'] += 1
                elif price < 0.90:
                    price_ranges['0.70-0.90'] += 1
                elif price < 0.95:
                    price_ranges['0.90-0.95'] += 1
                elif price < 0.99:
                    price_ranges['0.95-0.99'] += 1  # TARGET RANGE!
                else:
                    price_ranges['0.99-1.00'] += 1

    print()
    for range_name, count in price_ranges.items():
        bar = '█' * (count // 2)
        marker = ' 🎯 TARGET!' if range_name == '0.95-0.99' else ''
        print(f"{range_name}: {bar} {count}{marker}")

    print("\n" + "=" * 80)
    print()


if __name__ == "__main__":
    analyze_markets()
