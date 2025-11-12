#!/usr/bin/env python3
"""
CLI script to generate API tokens for IBCo Vallejo Console.

Usage:
    python scripts/admin/generate_api_token.py \
        --user-id "researcher@university.edu" \
        --tier researcher \
        --purpose "Municipal finance research project" \
        --email "researcher@university.edu" \
        --organization "UC Berkeley"
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.auth.tokens import TokenManager, TokenTier


def main():
    """Generate API token via CLI."""
    parser = argparse.ArgumentParser(
        description="Generate API token for IBCo Vallejo Console",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate public tier token
  python scripts/admin/generate_api_token.py \\
      --user-id "public-user-001" \\
      --tier public \\
      --purpose "General API exploration" \\
      --email "user@example.com"

  # Generate researcher tier token
  python scripts/admin/generate_api_token.py \\
      --user-id "researcher@university.edu" \\
      --tier researcher \\
      --purpose "Municipal finance research project" \\
      --email "researcher@university.edu" \\
      --organization "UC Berkeley"
        """,
    )

    # Required arguments
    parser.add_argument(
        "--user-id",
        required=True,
        help="Unique identifier for the user/requestor (e.g., email, username)",
    )

    parser.add_argument(
        "--tier",
        required=True,
        choices=["public", "researcher"],
        help="Token tier: 'public' (100 req/hr) or 'researcher' (1000 req/hr)",
    )

    parser.add_argument(
        "--purpose",
        required=True,
        help="Purpose of the token (e.g., 'Research project on municipal finance')",
    )

    parser.add_argument(
        "--email",
        required=True,
        help="Contact email for the token holder",
    )

    # Optional arguments
    parser.add_argument(
        "--organization",
        help="Organization name (optional)",
    )

    parser.add_argument(
        "--expiration-days",
        type=int,
        default=365,
        help="Token expiration in days (default: 365)",
    )

    parser.add_argument(
        "--output",
        choices=["console", "json"],
        default="console",
        help="Output format (default: console)",
    )

    args = parser.parse_args()

    try:
        # Initialize token manager
        print("Initializing token manager...")
        token_manager = TokenManager()

        # Generate token
        print(f"\nGenerating {args.tier} tier token for {args.user_id}...")
        token, metadata = token_manager.generate_token(
            user_id=args.user_id,
            tier=args.tier,
            purpose=args.purpose,
            contact_email=args.email,
            organization=args.organization,
            expiration_days=args.expiration_days,
        )

        # Output results
        if args.output == "json":
            import json

            output = {
                "token": token,
                "metadata": {
                    "token_id": metadata.token_id,
                    "user_id": metadata.user_id,
                    "tier": metadata.tier,
                    "purpose": metadata.purpose,
                    "contact_email": metadata.contact_email,
                    "organization": metadata.organization,
                    "issued_at": metadata.issued_at.isoformat(),
                    "expires_at": metadata.expires_at.isoformat(),
                },
            }
            print(json.dumps(output, indent=2))
        else:
            _print_token_info(token, metadata, args.tier)

        print("\n✅ Token generated successfully!")
        return 0

    except Exception as e:
        print(f"\n❌ Error generating token: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


def _print_token_info(token: str, metadata, tier: str):
    """Print token information in human-readable format."""
    # Rate limit info
    rate_limits = {
        "public": {"hourly": 100, "burst": 20},
        "researcher": {"hourly": 1000, "burst": 20},
    }

    limits = rate_limits.get(tier, rate_limits["public"])

    print("\n" + "=" * 80)
    print("API TOKEN GENERATED")
    print("=" * 80)
    print(f"\n📋 Token Details:")
    print(f"   Token ID:      {metadata.token_id}")
    print(f"   User ID:       {metadata.user_id}")
    print(f"   Tier:          {metadata.tier.upper()}")
    print(f"   Purpose:       {metadata.purpose}")
    print(f"   Contact Email: {metadata.contact_email}")
    if metadata.organization:
        print(f"   Organization:  {metadata.organization}")
    print(f"   Issued:        {metadata.issued_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"   Expires:       {metadata.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")

    print(f"\n⚡ Rate Limits:")
    print(f"   Hourly:        {limits['hourly']} requests/hour")
    print(f"   Burst:         {limits['burst']} requests/10 seconds")

    print(f"\n🔑 Your API Token:")
    print(f"\n   {token}\n")

    print("=" * 80)
    print("USAGE INSTRUCTIONS")
    print("=" * 80)

    print("\n1. Store your token securely (do not commit to version control)")
    print("   Add to .env file or environment variables:\n")
    print(f"     IBCO_API_TOKEN={token}\n")

    print("2. Include token in API requests as Bearer token:\n")
    print("   # Using curl")
    print(f'   curl -H "Authorization: Bearer {token}" \\')
    print("        https://api.ibco-ca.us/v1/fiscal-years/2023\n")

    print("   # Using Python requests")
    print("   import requests")
    print('   headers = {"Authorization": f"Bearer {token}"}')
    print('   response = requests.get("https://api.ibco-ca.us/v1/fiscal-years/2023", headers=headers)\n')

    print("   # Using JavaScript fetch")
    print("   fetch('https://api.ibco-ca.us/v1/fiscal-years/2023', {")
    print("     headers: {'Authorization': `Bearer ${token}`}")
    print("   })\n")

    print("3. Monitor your usage via response headers:")
    print("   - X-RateLimit-Limit: Your hourly limit")
    print("   - X-RateLimit-Remaining: Requests remaining this hour")
    print("   - X-RateLimit-Reset: Unix timestamp when limit resets\n")

    print("4. API Documentation:")
    print("   https://docs.ibco-ca.us/api\n")

    print("5. If you need to revoke this token, contact:")
    print("   support@ibco-ca.us\n")

    print("=" * 80)


if __name__ == "__main__":
    sys.exit(main())
