#!/usr/bin/env python3
"""
Import Metabase Dashboard Configurations

Reads dashboard JSON files and imports them into Metabase via API.

Usage:
    python import_dashboards.py --metabase-url http://localhost:3000 \\
                                 --metabase-user admin@ibco-ca.us \\
                                 --metabase-password secret \\
                                 --dashboard-dir ../dashboards/

    # Import single dashboard
    python import_dashboards.py --dashboard ../dashboards/vallejo_fiscal_overview.json

    # Enable public access for all dashboards
    python import_dashboards.py --enable-public-access

    # Delete existing dashboards before importing (dangerous!)
    python import_dashboards.py --delete-existing
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class MetabaseClient:
    """Client for Metabase API operations."""

    def __init__(self, base_url: str, username: str, password: str):
        """Initialize Metabase client."""
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.session_token: Optional[str] = None

        # Configure session with retries
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def authenticate(self) -> None:
        """Authenticate and get session token."""
        url = f"{self.base_url}/api/session"
        payload = {"username": self.username, "password": self.password}

        response = self.session.post(url, json=payload)
        response.raise_for_status()

        self.session_token = response.json()["id"]
        self.session.headers.update({"X-Metabase-Session": self.session_token})

        print(f"✓ Authenticated to Metabase as {self.username}")

    def get_database_id(self, database_name: str = "IBCo Production") -> Optional[int]:
        """Get database ID by name."""
        url = f"{self.base_url}/api/database"
        response = self.session.get(url)
        response.raise_for_status()

        databases = response.json()
        for db in databases:
            if db["name"] == database_name:
                return db["id"]

        return None

    def create_database(self, config: Dict[str, Any]) -> int:
        """Create database connection if not exists."""
        db_id = self.get_database_id(config["name"])
        if db_id:
            print(f"✓ Database '{config['name']}' already exists (ID: {db_id})")
            return db_id

        url = f"{self.base_url}/api/database"
        response = self.session.post(url, json=config)
        response.raise_for_status()

        db_id = response.json()["id"]
        print(f"✓ Created database '{config['name']}' (ID: {db_id})")
        return db_id

    def get_dashboard_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get dashboard by name."""
        url = f"{self.base_url}/api/dashboard"
        response = self.session.get(url)
        response.raise_for_status()

        dashboards = response.json()
        for dashboard in dashboards:
            if dashboard["name"] == name:
                return dashboard

        return None

    def delete_dashboard(self, dashboard_id: int) -> None:
        """Delete dashboard by ID."""
        url = f"{self.base_url}/api/dashboard/{dashboard_id}"
        response = self.session.delete(url)
        response.raise_for_status()
        print(f"✓ Deleted existing dashboard (ID: {dashboard_id})")

    def create_question(self, database_id: int, question_config: Dict[str, Any]) -> int:
        """Create a Metabase question (saved query)."""
        # Convert our JSON format to Metabase API format
        payload = {
            "name": question_config["name"],
            "description": question_config.get("description", ""),
            "dataset_query": {
                "type": question_config["query"]["type"],
                "database": database_id,
            },
            "display": question_config["visualization"]["type"],
            "visualization_settings": question_config.get("display", {}),
        }

        # Add native query if present
        if question_config["query"]["type"] == "native":
            payload["dataset_query"]["native"] = question_config["query"]["native"]

        url = f"{self.base_url}/api/card"
        response = self.session.post(url, json=payload)
        response.raise_for_status()

        question_id = response.json()["id"]
        print(f"  ✓ Created question: {question_config['name']} (ID: {question_id})")
        return question_id

    def create_dashboard(self, dashboard_config: Dict[str, Any]) -> int:
        """Create dashboard."""
        payload = {
            "name": dashboard_config["name"],
            "description": dashboard_config.get("description", ""),
            "parameters": dashboard_config.get("parameters", []),
        }

        url = f"{self.base_url}/api/dashboard"
        response = self.session.post(url, json=payload)
        response.raise_for_status()

        dashboard_id = response.json()["id"]
        print(f"✓ Created dashboard: {dashboard_config['name']} (ID: {dashboard_id})")
        return dashboard_id

    def add_cards_to_dashboard(
        self,
        dashboard_id: int,
        layout: Dict[str, Any],
        question_id_map: Dict[str, int],
    ) -> None:
        """Add question cards to dashboard with layout."""
        url = f"{self.base_url}/api/dashboard/{dashboard_id}/cards"

        for card in layout["cards"]:
            question_id = question_id_map[card["question_id"]]

            card_payload = {
                "cardId": question_id,
                "row": card["row"],
                "col": card["col"],
                "sizeX": card["size_x"],
                "sizeY": card["size_y"],
            }

            response = self.session.post(url, json=card_payload)
            response.raise_for_status()

        print(f"  ✓ Added {len(layout['cards'])} cards to dashboard")

    def enable_public_sharing(self, dashboard_id: int) -> str:
        """Enable public sharing for dashboard and return public URL."""
        url = f"{self.base_url}/api/dashboard/{dashboard_id}/public_link"
        response = self.session.post(url)
        response.raise_for_status()

        public_uuid = response.json()["uuid"]
        public_url = f"{self.base_url}/public/dashboard/{public_uuid}"

        print(f"  ✓ Enabled public access: {public_url}")
        return public_url

    def import_dashboard(
        self,
        dashboard_config: Dict[str, Any],
        database_id: int,
        delete_existing: bool = False,
    ) -> Dict[str, Any]:
        """Import complete dashboard configuration."""
        # Check if dashboard already exists
        existing = self.get_dashboard_by_name(dashboard_config["name"])
        if existing:
            if delete_existing:
                self.delete_dashboard(existing["id"])
            else:
                print(
                    f"✗ Dashboard '{dashboard_config['name']}' already exists. "
                    f"Use --delete-existing to overwrite."
                )
                return existing

        # Create questions
        print(f"Creating questions for '{dashboard_config['name']}'...")
        question_id_map = {}

        for question in dashboard_config.get("questions", []):
            question_id = self.create_question(database_id, question)
            question_id_map[question["id"]] = question_id
            time.sleep(0.5)  # Rate limiting

        # Create dashboard
        dashboard_id = self.create_dashboard(dashboard_config)

        # Add cards to dashboard
        if "layout" in dashboard_config:
            self.add_cards_to_dashboard(
                dashboard_id, dashboard_config["layout"], question_id_map
            )

        # Enable public access if specified
        public_url = None
        if dashboard_config.get("public_access", {}).get("enabled", False):
            public_url = self.enable_public_sharing(dashboard_id)

        return {
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard_config["name"],
            "question_count": len(question_id_map),
            "public_url": public_url,
        }


def load_dashboard_config(file_path: Path) -> Dict[str, Any]:
    """Load dashboard configuration from JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def get_database_config() -> Dict[str, Any]:
    """Get database connection configuration."""
    import os

    return {
        "name": "IBCo Production",
        "engine": "postgres",
        "details": {
            "host": os.getenv("METABASE_DB_HOST", "postgres"),
            "port": int(os.getenv("METABASE_DB_PORT", "5432")),
            "dbname": os.getenv("METABASE_DB_NAME", "ibco_production"),
            "user": os.getenv("METABASE_DB_USER", "metabase_readonly"),
            "password": os.getenv("METABASE_DB_PASSWORD", ""),
            "ssl": False,
            "tunnel-enabled": False,
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Import Metabase dashboard configurations"
    )
    parser.add_argument(
        "--metabase-url",
        default="http://localhost:3000",
        help="Metabase URL (default: http://localhost:3000)",
    )
    parser.add_argument(
        "--metabase-user",
        default="admin@ibco-ca.us",
        help="Metabase admin username",
    )
    parser.add_argument(
        "--metabase-password",
        help="Metabase admin password (or set METABASE_ADMIN_PASSWORD env var)",
    )
    parser.add_argument(
        "--dashboard-dir",
        type=Path,
        help="Directory containing dashboard JSON files",
    )
    parser.add_argument(
        "--dashboard",
        type=Path,
        help="Single dashboard JSON file to import",
    )
    parser.add_argument(
        "--delete-existing",
        action="store_true",
        help="Delete existing dashboards before importing",
    )
    parser.add_argument(
        "--enable-public-access",
        action="store_true",
        help="Enable public access for all imported dashboards",
    )

    args = parser.parse_args()

    # Get password from args or environment
    import os

    password = args.metabase_password or os.getenv("METABASE_ADMIN_PASSWORD")
    if not password:
        print("Error: Metabase password required (--metabase-password or METABASE_ADMIN_PASSWORD env var)")
        sys.exit(1)

    # Initialize client
    client = MetabaseClient(args.metabase_url, args.metabase_user, password)
    client.authenticate()

    # Create or get database connection
    db_config = get_database_config()
    database_id = client.create_database(db_config)

    # Collect dashboard files to import
    dashboard_files = []
    if args.dashboard:
        dashboard_files = [args.dashboard]
    elif args.dashboard_dir:
        dashboard_files = list(args.dashboard_dir.glob("*.json"))
    else:
        # Default to dashboards directory
        script_dir = Path(__file__).parent
        dashboard_dir = script_dir.parent / "dashboards"
        dashboard_files = list(dashboard_dir.glob("*.json"))

    if not dashboard_files:
        print("No dashboard files found")
        sys.exit(1)

    # Import each dashboard
    print(f"\nImporting {len(dashboard_files)} dashboard(s)...\n")

    results = []
    for dashboard_file in dashboard_files:
        print(f"{'=' * 60}")
        print(f"Importing: {dashboard_file.name}")
        print(f"{'=' * 60}")

        try:
            config = load_dashboard_config(dashboard_file)

            # Override public access setting if flag provided
            if args.enable_public_access:
                config.setdefault("public_access", {})["enabled"] = True

            result = client.import_dashboard(config, database_id, args.delete_existing)
            results.append(result)

            print(f"✓ Successfully imported '{result['dashboard_name']}'\n")

        except Exception as e:
            print(f"✗ Failed to import {dashboard_file.name}: {e}\n")
            continue

    # Summary
    print(f"\n{'=' * 60}")
    print("Import Summary")
    print(f"{'=' * 60}")
    print(f"Total dashboards: {len(dashboard_files)}")
    print(f"Successfully imported: {len(results)}")
    print(f"Failed: {len(dashboard_files) - len(results)}\n")

    # Print public URLs
    public_urls = [r for r in results if r.get("public_url")]
    if public_urls:
        print("Public Dashboard URLs:")
        for result in public_urls:
            print(f"  • {result['dashboard_name']}: {result['public_url']}")
        print()

    print("✓ Import complete!")


if __name__ == "__main__":
    main()
