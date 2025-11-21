# Polymarket API Authentication Setup

This guide explains how to generate and configure Polymarket API credentials for whale discovery.

## Why You Need This

The whale discovery system needs to access Polymarket's CLOB API to fetch trade data. This requires authentication via API credentials.

## Step 1: Export Your Private Key from Polymarket

1. Log into your [Polymarket.com](https://polymarket.com) account
2. Click on **"Cash"** in the navigation
3. Click the **3 dots menu** (⋯)
4. Select **"Export Private Key"**
5. Copy your private key (it will look like: `0x123abc...`)

⚠️ **IMPORTANT**: Keep this private key secure! Never share it or commit it to git.

## Step 2: Generate API Credentials

### On Your Local Machine:

```bash
# Set your private key as an environment variable (remove the 0x prefix)
export POLYMARKET_PRIVATE_KEY="your_private_key_without_0x"

# Run the generation script
python agents/generate_polymarket_api_keys.py
```

This will output three credentials:
- `POLYMARKET_API_KEY` - UUID format
- `POLYMARKET_API_SECRET` - Base64 encoded
- `POLYMARKET_API_PASSPHRASE` - Encoded string

## Step 3: Add to Railway Environment Variables

1. Go to your Railway project dashboard
2. Click on your service
3. Navigate to the **"Variables"** tab
4. Click **"Add Variable"** for each:

```
POLYMARKET_API_KEY=your_api_key_here
POLYMARKET_API_SECRET=your_api_secret_here
POLYMARKET_API_PASSPHRASE=your_api_passphrase_here
```

5. Click **"Deploy"** to restart the service with new variables

## Step 4: Verify It's Working

After deploying, check the Railway logs:

```bash
# Using Railway MCP
railway get-logs --filter "Whale Discovery initialized"
```

You should see:
```
Whale Discovery initialized: min_trade=$500, min_volume=$50,000, auth=✓ Enabled
```

If you see `auth=✗ Disabled`, the environment variables weren't loaded correctly.

## Troubleshooting

### "Error: py-clob-client not installed"
```bash
pip install py-clob-client
```

### "Error: POLYMARKET_PRIVATE_KEY environment variable not set"
Make sure you exported the variable without the `0x` prefix:
```bash
export POLYMARKET_PRIVATE_KEY="123abc..."  # NO 0x prefix
```

### Still getting HTTP 401 errors
1. Double-check all three environment variables are set in Railway
2. Verify the credentials were generated successfully
3. Restart the Railway service after adding variables

### Rate Limiting (HTTP 429)
The code already includes:
- 1.5 second delay between requests
- Exponential backoff on retries
- Reduced market scan from 50 to 20 markets

If still rate limited, you can:
- Increase `API_RATE_LIMIT_DELAY` in `auto_discovery.py`
- Further reduce `markets_per_scan`

## Security Notes

- ✅ DO store credentials in Railway environment variables
- ✅ DO keep your private key secure
- ❌ DON'T commit credentials to git
- ❌ DON'T share your private key or API credentials
- ❌ DON'T store credentials in code files

## Additional Resources

- [Polymarket API Documentation](https://docs.polymarket.com/developers/CLOB/authentication)
- [py-clob-client GitHub](https://github.com/Polymarket/py-clob-client)
