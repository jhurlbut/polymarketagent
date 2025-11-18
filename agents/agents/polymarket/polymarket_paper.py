"""
Paper Trading Compatible Polymarket Client.

This is a simplified version of the Polymarket client that works without
py-clob-client for paper trading purposes. It can fetch market data but
doesn't execute real trades.
"""

import logging
from typing import List, Optional
import requests

from agents.polymarket.gamma import GammaMarketClient
from agents.utils.objects import SimpleMarket, SimpleEvent

logger = logging.getLogger(__name__)


class PolymarketPaper:
    """
    Simplified Polymarket client for paper trading.
    Fetches market data but doesn't execute trades.
    """

    def __init__(self):
        """Initialize paper trading Polymarket client."""
        self.gamma_client = GammaMarketClient()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized Polymarket Paper Trading Client")

    def get_balance(self) -> float:
        """
        Get USDC balance (mocked for paper trading).

        Returns:
            Mock balance of 10000 USDC
        """
        return 10000.0

    def get_all_tradeable_markets(self) -> List[SimpleMarket]:
        """
        Get all tradeable markets from Polymarket.

        Returns:
            List of SimpleMarket objects
        """
        try:
            markets = self.gamma_client.get_clob_tradable_markets()
            self.logger.info(f"Retrieved {len(markets)} tradeable markets")
            return markets
        except Exception as e:
            self.logger.error(f"Error fetching markets: {e}")
            return []

    def get_all_tradeable_events(self) -> List[SimpleEvent]:
        """
        Get all tradeable events from Polymarket.

        Returns:
            List of SimpleEvent objects
        """
        try:
            events = self.gamma_client.get_current_events()
            self.logger.info(f"Retrieved {len(events)} events")
            return events
        except Exception as e:
            self.logger.error(f"Error fetching events: {e}")
            return []

    def execute_market_order(self, *args, **kwargs):
        """
        Mock execute market order (not implemented for paper trading).

        Raises:
            NotImplementedError: Always, as this is paper trading only
        """
        raise NotImplementedError(
            "Trade execution not available in paper trading mode. "
            "Set PAPER_TRADING_MODE=false and install py-clob-client for live trading."
        )


if __name__ == "__main__":
    # Test paper trading client
    logging.basicConfig(level=logging.INFO)

    print("Testing Paper Trading Polymarket Client...")

    client = PolymarketPaper()

    print(f"\nMock Balance: ${client.get_balance():.2f}")

    print("\nFetching markets...")
    markets = client.get_all_tradeable_markets()
    print(f"Found {len(markets)} markets")

    if markets:
        print("\nFirst 3 markets:")
        for i, market in enumerate(markets[:3], 1):
            print(f"{i}. {getattr(market, 'question', 'Unknown')}")

    print("\nPaper Trading Client test complete!")
