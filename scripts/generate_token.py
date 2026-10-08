import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import create_access_token


def main():
    parser = argparse.ArgumentParser(description="Generate mock or development JWT tokens for SLSEA Solar Data API")
    parser.add_argument("--role", choices=["admin", "analyst", "device"], default="analyst")
    parser.add_argument("--sub", default="test_client")
    parser.add_argument("--scope", nargs="+", default=["analyst-read-national"])
    parser.add_argument("--jurisdiction-type", choices=["national", "province", "district", "installation"], default="national")
    parser.add_argument("--jurisdiction-id", type=int, default=None)
    
    args = parser.parse_args()

    token = create_access_token(
        subject=args.sub,
        scopes=args.scope,
        role=args.role,
        jurisdiction_type=args.jurisdiction_type,
        jurisdiction_id=args.jurisdiction_id
    )

    print("=" * 60)
    print("SLSEA Solar Data API - Generated JWT Token")
    print("=" * 60)
    print(f"Subject:           {args.sub}")
    print(f"Role:              {args.role}")
    print(f"Scopes:            {', '.join(args.scope)}")
    print(f"Jurisdiction Type: {args.jurisdiction_type}")
    print(f"Jurisdiction ID:   {args.jurisdiction_id}")
    print("-" * 60)
    print(f"Bearer Token:\n{token}")
    print("=" * 60)


if __name__ == "__main__":
    main()
