"""
Configuration management for Polymarket trading agents.
Loads environment variables and provides typed configuration access.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Central configuration class for all trading parameters."""

    # Core Polymarket Configuration
    POLYGON_WALLET_PRIVATE_KEY: str = os.getenv("POLYGON_WALLET_PRIVATE_KEY", "")
    POLYGON_RPC_URL: str = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")

    # AI/LLM APIs
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # News & Data Sources
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    NEWSAPI_API_KEY: str = os.getenv("NEWSAPI_API_KEY", "")
    TWITTER_BEARER_TOKEN: Optional[str] = os.getenv("TWITTER_BEARER_TOKEN")

    # Database Configuration
    @staticmethod
    def get_database_url() -> str:
        """
        Get database URL with proper format handling.
        Converts postgres:// to postgresql:// for SQLAlchemy compatibility.
        """
        db_url = os.getenv("DATABASE_URL", "sqlite:///polymarket_trading.db")

        # Fix Heroku/Railway Postgres URL format
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        return db_url

    DATABASE_URL: str = get_database_url.__func__()

    # Trading Configuration
    PAPER_TRADING_MODE: bool = os.getenv("PAPER_TRADING_MODE", "true").lower() == "true"
    MAX_POSITION_SIZE_PCT: float = float(os.getenv("MAX_POSITION_SIZE_PCT", "10"))
    MIN_PROFIT_THRESHOLD_PCT: float = float(os.getenv("MIN_PROFIT_THRESHOLD_PCT", "0.3"))

    # Risk Management
    DAILY_LOSS_LIMIT_PCT: float = float(os.getenv("DAILY_LOSS_LIMIT_PCT", "5"))
    WEEKLY_LOSS_LIMIT_PCT: float = float(os.getenv("WEEKLY_LOSS_LIMIT_PCT", "10"))
    MIN_MARKETS_FOR_DIVERSIFICATION: int = int(os.getenv("MIN_MARKETS_FOR_DIVERSIFICATION", "5"))
    GAS_FEE_MAX_PCT_OF_PROFIT: float = float(os.getenv("GAS_FEE_MAX_PCT_OF_PROFIT", "10"))

    # Monitoring & Alerts
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")
    DISCORD_WEBHOOK_URL: Optional[str] = os.getenv("DISCORD_WEBHOOK_URL")

    # Strategy-Specific Configuration
    ENDGAME_MIN_PRICE: float = float(os.getenv("ENDGAME_MIN_PRICE", "0.95"))
    ENDGAME_MAX_PRICE: float = float(os.getenv("ENDGAME_MAX_PRICE", "0.99"))
    ENDGAME_MAX_TIME_TO_SETTLEMENT_HOURS: int = int(os.getenv("ENDGAME_MAX_TIME_TO_SETTLEMENT_HOURS", "24"))

    MULTI_OPTION_MIN_PROFIT_PCT: float = float(os.getenv("MULTI_OPTION_MIN_PROFIT_PCT", "0.3"))

    NEWS_TRADING_MAX_REACTION_TIME_SECONDS: int = int(os.getenv("NEWS_TRADING_MAX_REACTION_TIME_SECONDS", "30"))

    # Whale Following Strategy Configuration
    WHALE_TRACKING_ENABLED: bool = os.getenv("WHALE_TRACKING_ENABLED", "false").lower() == "true"
    WHALE_MIN_VOLUME_USD: float = float(os.getenv("WHALE_MIN_VOLUME_USD", "50000"))
    WHALE_MIN_QUALITY_SCORE: float = float(os.getenv("WHALE_MIN_QUALITY_SCORE", "0.70"))
    WHALE_COPY_DELAY_SECONDS: int = int(os.getenv("WHALE_COPY_DELAY_SECONDS", "300"))  # 5 minutes
    WHALE_MAX_POSITION_PCT: float = float(os.getenv("WHALE_MAX_POSITION_PCT", "8"))

    # Polygon Blockchain (for whale monitoring)
    POLYGON_WSS_URL: str = os.getenv("POLYGON_WSS_URL", "wss://polygon-rpc.com")
    CTF_EXCHANGE_ADDRESS: str = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"  # Polymarket CTF Exchange
    CTF_CONTRACT_ADDRESS: str = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"  # Conditional Tokens Framework

    @classmethod
    def validate(cls) -> list[str]:
        """
        Validate that required configuration is present.
        Returns list of missing/invalid configuration items.
        """
        errors = []

        if not cls.POLYGON_WALLET_PRIVATE_KEY and not cls.PAPER_TRADING_MODE:
            errors.append("POLYGON_WALLET_PRIVATE_KEY required for live trading")

        if not cls.OPENAI_API_KEY and not cls.ANTHROPIC_API_KEY:
            errors.append("Either OPENAI_API_KEY or ANTHROPIC_API_KEY must be set")

        if cls.MAX_POSITION_SIZE_PCT <= 0 or cls.MAX_POSITION_SIZE_PCT > 100:
            errors.append("MAX_POSITION_SIZE_PCT must be between 0 and 100")

        if cls.MIN_PROFIT_THRESHOLD_PCT < 0:
            errors.append("MIN_PROFIT_THRESHOLD_PCT must be non-negative")

        return errors

    @classmethod
    def is_valid(cls) -> bool:
        """Check if configuration is valid."""
        return len(cls.validate()) == 0

    @classmethod
    def print_config(cls, mask_secrets: bool = True) -> None:
        """Print current configuration (optionally masking secrets)."""
        print("=" * 60)
        print("Current Configuration")
        print("=" * 60)

        for key, value in cls.__dict__.items():
            if key.startswith("_") or callable(value):
                continue

            # Mask sensitive values
            if mask_secrets and any(
                secret in key.lower()
                for secret in ["key", "token", "password", "secret"]
            ):
                if value:
                    value = f"{value[:4]}...{value[-4:]}" if len(str(value)) > 8 else "***"
                else:
                    value = "(not set)"

            print(f"{key}: {value}")

        print("=" * 60)

        # Print validation errors if any
        errors = cls.validate()
        if errors:
            print("\nCONFIGURATION ERRORS:")
            for error in errors:
                print(f"  - {error}")
            print()


# Create global config instance
config = Config()


if __name__ == "__main__":
    # Test configuration
    config.print_config()

    if config.is_valid():
        print("\nConfiguration is valid!")
    else:
        print("\nConfiguration has errors. Please fix before running.")
