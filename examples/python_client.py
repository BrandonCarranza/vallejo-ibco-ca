#!/usr/bin/env python3
"""
IBCo Python Client Example

Demonstrates how to use the IBCo API with Python's requests library.

Usage:
    python python_client.py
    python python_client.py --api-token YOUR_TOKEN
"""

import argparse
from typing import Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class IBCoClient:
    """Python client for IBCo API."""

    def __init__(
        self,
        base_url: str = "https://api.ibco-ca.us/api/v1",
        api_token: Optional[str] = None,
    ):
        """
        Initialize IBCo client.

        Args:
            base_url: API base URL
            api_token: Optional API token for researcher tier
        """
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token

        # Configure session with retries
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.mount("http://", HTTPAdapter(max_retries=retries))

        # Set auth header if token provided
        if api_token:
            self.session.headers.update({"Authorization": f"Bearer {api_token}"})

    def get_cities(self, state: Optional[str] = None) -> List[Dict]:
        """
        Get list of cities.

        Args:
            state: Filter by state code (e.g., 'CA')

        Returns:
            List of city dictionaries
        """
        params = {}
        if state:
            params["state"] = state

        response = self.session.get(f"{self.base_url}/cities", params=params)
        response.raise_for_status()

        return response.json()["cities"]

    def get_current_risk_score(self, city_id: int) -> Dict:
        """
        Get current risk score for a city.

        Args:
            city_id: City ID

        Returns:
            Risk score dictionary
        """
        response = self.session.get(f"{self.base_url}/risk/cities/{city_id}/current")
        response.raise_for_status()

        return response.json()

    def get_risk_history(
        self,
        city_id: int,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> Dict:
        """
        Get risk score history.

        Args:
            city_id: City ID
            start_year: Start fiscal year (optional)
            end_year: End fiscal year (optional)

        Returns:
            Risk history dictionary
        """
        params = {}
        if start_year:
            params["start_year"] = start_year
        if end_year:
            params["end_year"] = end_year

        response = self.session.get(
            f"{self.base_url}/risk/cities/{city_id}/history", params=params
        )
        response.raise_for_status()

        return response.json()

    def get_fiscal_cliff(
        self,
        city_id: int,
        scenario: str = "base",
    ) -> Dict:
        """
        Get fiscal cliff analysis.

        Args:
            city_id: City ID
            scenario: Scenario code (base, optimistic, pessimistic)

        Returns:
            Fiscal cliff analysis
        """
        params = {"scenario": scenario}

        response = self.session.get(
            f"{self.base_url}/projections/cities/{city_id}/fiscal-cliff",
            params=params,
        )
        response.raise_for_status()

        return response.json()

    def get_pension_status(self, city_id: int, fiscal_year: int) -> Dict:
        """
        Get pension status.

        Args:
            city_id: City ID
            fiscal_year: Fiscal year

        Returns:
            Pension status dictionary
        """
        params = {"fiscal_year": fiscal_year}

        response = self.session.get(
            f"{self.base_url}/pensions/cities/{city_id}/status",
            params=params,
        )
        response.raise_for_status()

        return response.json()


def main():
    parser = argparse.ArgumentParser(description="IBCo API Python Client Example")
    parser.add_argument(
        "--api-token",
        help="API token for researcher tier (optional)",
    )
    parser.add_argument(
        "--city-id",
        type=int,
        default=1,
        help="City ID (default: 1 for Vallejo)",
    )

    args = parser.parse_args()

    # Initialize client
    client = IBCoClient(api_token=args.api_token)

    print("=" * 60)
    print("IBCo API Python Client Example")
    print("=" * 60)

    # 1. Get list of cities
    print("\n1. Getting list of cities...")
    cities = client.get_cities(state="CA")
    print(f"Found {len(cities)} cities in California:")
    for city in cities[:5]:  # Show first 5
        print(f"  - {city['name']} (ID: {city['id']})")

    # 2. Get current risk score
    print(f"\n2. Getting current risk score for city {args.city_id}...")
    risk_score = client.get_current_risk_score(args.city_id)
    print(f"City: {risk_score['city_name']}")
    print(f"Fiscal Year: {risk_score['fiscal_year']}")
    print(f"Overall Score: {risk_score['overall_score']}/100 ({risk_score['risk_level']})")
    print("Category Scores:")
    for category, score in risk_score['category_scores'].items():
        print(f"  - {category}: {score}/100")

    # 3. Get risk history
    print(f"\n3. Getting risk score history...")
    history = client.get_risk_history(args.city_id, start_year=2020)
    print(f"Trend: {history['trend']}")
    print("Historical Scores:")
    for item in history['risk_scores']:
        print(f"  - FY{item['fiscal_year']}: {item['overall_score']}/100")

    # 4. Get fiscal cliff analysis
    print(f"\n4. Getting fiscal cliff analysis...")
    cliff = client.get_fiscal_cliff(args.city_id, scenario="base")
    if cliff['has_fiscal_cliff']:
        print(f"⚠ Fiscal Cliff Warning:")
        print(f"  Cliff Year: FY{cliff['fiscal_cliff_year']}")
        print(f"  Years Until Cliff: {cliff['years_until_cliff']}")
        print(f"  Revenue Increase Needed: {cliff['revenue_increase_needed_percent']:.1f}%")
    else:
        print("✓ No fiscal cliff projected under current trends")

    # 5. Get pension status
    print(f"\n5. Getting pension status...")
    pensions = client.get_pension_status(args.city_id, fiscal_year=2024)
    print(f"Average Funded Ratio: {pensions['avg_funded_ratio']:.1%}")
    print(f"Total UAL: ${pensions['total_ual']:,.0f}")
    print("Plans:")
    for plan in pensions['plans']:
        print(f"  - {plan['plan_name']}: {plan['funded_ratio']:.1%} funded")

    print("\n" + "=" * 60)
    print("✓ Examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
