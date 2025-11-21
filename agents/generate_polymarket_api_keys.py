"""
Generate Polymarket API credentials from a private key.

Usage:
    1. Export your private key from Polymarket.com:
       - Log in → Cash → 3 dots menu → "Export Private Key"
    2. Set environment variable: export POLYMARKET_PRIVATE_KEY="your_key_without_0x"
    3. Run: python generate_polymarket_api_keys.py
"""

import os
import sys

try:
    from py_clob_client.client import ClobClient
except ImportError:
    print("Error: py-clob-client not installed")
    print("Install it with: pip install py-clob-client")
    sys.exit(1)


def generate_api_credentials():
    """Generate API credentials from private key."""

    # Get private key from environment
    private_key = os.environ.get('POLYMARKET_PRIVATE_KEY')

    if not private_key:
        print("Error: POLYMARKET_PRIVATE_KEY environment variable not set")
        print("\nSteps:")
        print("1. Log into Polymarket.com")
        print("2. Click 'Cash' → 3 dots menu → 'Export Private Key'")
        print("3. Set environment variable:")
        print("   export POLYMARKET_PRIVATE_KEY='your_key_without_0x_prefix'")
        sys.exit(1)

    # Remove 0x prefix if present
    if private_key.startswith('0x'):
        private_key = private_key[2:]

    print("Generating API credentials...")

    try:
        # Initialize client
        client = ClobClient(
            host="https://clob.polymarket.com",
            key=private_key,
            chain_id=137  # Polygon mainnet
        )

        # Generate or derive API credentials
        creds = client.create_or_derive_api_creds()

        print("\n" + "=" * 70)
        print("API CREDENTIALS GENERATED SUCCESSFULLY")
        print("=" * 70)
        print("\nAdd these to your Railway environment variables or .env file:\n")
        print(f"POLYMARKET_API_KEY={creds['apiKey']}")
        print(f"POLYMARKET_API_SECRET={creds['secret']}")
        print(f"POLYMARKET_API_PASSPHRASE={creds['passphrase']}")
        print("\n" + "=" * 70)
        print("\nKeep these credentials secure! Do not commit them to git.")
        print("=" * 70)

        return creds

    except Exception as e:
        print(f"Error generating credentials: {e}")
        sys.exit(1)


if __name__ == "__main__":
    generate_api_credentials()
