#!/usr/bin/env python3
"""
Setup script to generate Polymarket CLOB API credentials.

This script will:
1. Check if you have a Polygon wallet private key
2. Install py-clob-client if needed
3. Generate CLOB API credentials from your wallet
4. Save credentials to your .env file

Note: This requires a Polygon wallet private key. The wallet doesn't need
any funds - it's only used to generate API credentials for read access.
"""

import os
import sys
from pathlib import Path


def check_py_clob_client():
    """Check if py-clob-client is installed."""
    try:
        from py_clob_client.client import ClobClient
        print("✓ py-clob-client is installed")
        return True
    except ImportError:
        print("✗ py-clob-client not installed")
        return False


def install_py_clob_client():
    """Install py-clob-client."""
    print("\n📦 Installing py-clob-client...")
    import subprocess

    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "py-clob-client", "--quiet"
        ])
        print("✓ py-clob-client installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install py-clob-client: {e}")
        return False


def generate_clob_credentials(private_key: str):
    """Generate CLOB API credentials from wallet private key."""
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.constants import POLYGON

        print("\n🔑 Generating CLOB API credentials...")

        # Create CLOB client
        client = ClobClient(
            host="https://clob.polymarket.com",
            key=private_key,
            chain_id=POLYGON
        )

        # Generate API credentials
        creds = client.create_or_derive_api_creds()

        print("✓ API credentials generated successfully!")
        print(f"\nAPI Key: {creds.api_key[:20]}...")
        print(f"API Secret: {creds.api_secret[:20]}...")
        print(f"API Passphrase: {creds.api_passphrase[:20]}...")

        return creds

    except Exception as e:
        print(f"✗ Failed to generate credentials: {e}")
        return None


def update_env_file(creds):
    """Update .env file with CLOB API credentials."""
    env_path = Path(__file__).parent / ".env"

    print(f"\n📝 Updating {env_path}...")

    try:
        # Read existing .env
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
        else:
            lines = []

        # Remove old CLOB credentials if they exist
        lines = [
            line for line in lines
            if not any(key in line for key in ['CLOB_API_KEY=', 'CLOB_SECRET=', 'CLOB_PASS_PHRASE='])
        ]

        # Add new credentials
        lines.append(f"\n# Polymarket CLOB API Credentials (Auto-generated)\n")
        lines.append(f"CLOB_API_KEY={creds.api_key}\n")
        lines.append(f"CLOB_SECRET={creds.api_secret}\n")
        lines.append(f"CLOB_PASS_PHRASE={creds.api_passphrase}\n")

        # Write back
        with open(env_path, 'w') as f:
            f.writelines(lines)

        print(f"✓ Credentials saved to {env_path}")
        return True

    except Exception as e:
        print(f"✗ Failed to update .env: {e}")
        return False


def create_test_wallet():
    """Create a new test wallet for API access (no funds needed)."""
    print("\n🆕 Creating new test wallet for API access...")
    print("(This wallet doesn't need any funds - it's only for API credentials)")

    try:
        from eth_account import Account

        # Create new account
        account = Account.create()

        print(f"\n✓ New wallet created!")
        print(f"Address: {account.address}")
        print(f"Private Key: {account.key.hex()}")
        print(f"\nIMPORTANT: Save this private key! You'll need it in your .env file.")

        return account.key.hex()

    except Exception as e:
        print(f"✗ Failed to create wallet: {e}")
        return None


def main():
    print("=" * 70)
    print("POLYMARKET CLOB API SETUP")
    print("=" * 70)

    # Check for existing private key
    from dotenv import load_dotenv
    load_dotenv()

    private_key = os.getenv("POLYGON_WALLET_PRIVATE_KEY")

    if not private_key:
        print("\n⚠️  No POLYGON_WALLET_PRIVATE_KEY found in .env")
        print("\nYou have two options:")
        print("1. Create a new test wallet (recommended for read-only access)")
        print("2. Use an existing wallet's private key")

        choice = input("\nCreate new wallet? (y/n): ").strip().lower()

        if choice == 'y':
            private_key = create_test_wallet()
            if not private_key:
                print("\n✗ Failed to create wallet. Exiting.")
                return

            # Update .env with private key
            env_path = Path(__file__).parent / ".env"
            with open(env_path, 'a') as f:
                f.write(f"\n# Polygon Wallet (for CLOB API access only)\n")
                f.write(f"POLYGON_WALLET_PRIVATE_KEY={private_key}\n")

            print(f"✓ Private key saved to .env")
        else:
            print("\nPlease add your private key to .env:")
            print("POLYGON_WALLET_PRIVATE_KEY=0x...")
            return
    else:
        print(f"✓ Found POLYGON_WALLET_PRIVATE_KEY in .env")
        print(f"  Address: {private_key[:10]}...{private_key[-10:]}")

    # Check/install py-clob-client
    if not check_py_clob_client():
        if not install_py_clob_client():
            print("\n✗ Setup failed. Please install py-clob-client manually:")
            print("  pip install py-clob-client")
            return

    # Generate credentials
    creds = generate_clob_credentials(private_key)
    if not creds:
        print("\n✗ Setup failed.")
        return

    # Update .env
    if not update_env_file(creds):
        print("\n✗ Setup failed.")
        return

    print("\n" + "=" * 70)
    print("✅ CLOB API SETUP COMPLETE!")
    print("=" * 70)
    print("\nYour .env file now contains:")
    print(f"  - POLYGON_WALLET_PRIVATE_KEY")
    print(f"  - CLOB_API_KEY")
    print(f"  - CLOB_SECRET")
    print(f"  - CLOB_PASS_PHRASE")
    print("\nYou can now use the CLOB API to fetch trade data!")
    print("Restart your trading system to use the new credentials.")


if __name__ == "__main__":
    main()
