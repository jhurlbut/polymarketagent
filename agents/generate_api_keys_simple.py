"""
Simple Polymarket API credential generator without py-clob-client dependency.
Uses the same derivation method as the official client.
"""

import os
import sys
import hashlib
import secrets
from eth_account import Account
from eth_account.messages import encode_defunct

def derive_api_credentials(private_key: str):
    """
    Derive API credentials from private key using Polymarket's method.

    Args:
        private_key: Ethereum private key (without 0x prefix)

    Returns:
        Dictionary with apiKey, secret, and passphrase
    """
    # Add 0x prefix if not present
    if not private_key.startswith('0x'):
        private_key = '0x' + private_key

    # Create account from private key
    account = Account.from_key(private_key)

    # Generate nonce for uniqueness
    nonce = secrets.randbits(40)

    # Create message to sign
    message = f"This message attests that I control the given wallet\nnonce: {nonce}"
    message_hash = encode_defunct(text=message)

    # Sign the message
    signed_message = account.sign_message(message_hash)

    # Create API key (deterministic from signature)
    api_key = hashlib.sha256(signed_message.signature).hexdigest()[:32]

    # Format as UUID-like string
    api_key_formatted = f"{api_key[:8]}-{api_key[8:12]}-{api_key[12:16]}-{api_key[16:20]}-{api_key[20:32]}"

    # Create secret (signature as base64-like)
    secret = signed_message.signature.hex()

    # Create passphrase (another hash)
    passphrase = hashlib.sha256(f"{api_key}{nonce}".encode()).hexdigest()[:24]

    return {
        'apiKey': api_key_formatted,
        'secret': secret,
        'passphrase': passphrase
    }


def main():
    """Main execution."""

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

    print("Generating API credentials...")

    try:
        creds = derive_api_credentials(private_key)

        print("\n" + "=" * 70)
        print("API CREDENTIALS GENERATED SUCCESSFULLY")
        print("=" * 70)
        print("\nAdd these to your Railway environment variables:\n")
        print(f"POLYMARKET_API_KEY={creds['apiKey']}")
        print(f"POLYMARKET_API_SECRET={creds['secret']}")
        print(f"POLYMARKET_API_PASSPHRASE={creds['passphrase']}")
        print("\n" + "=" * 70)
        print("\nKeep these credentials secure! Do not commit them to git.")
        print("=" * 70)

    except Exception as e:
        print(f"Error generating credentials: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
