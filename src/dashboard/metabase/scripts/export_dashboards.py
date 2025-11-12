#!/usr/bin/env python3
"""
Export Metabase Dashboard Configurations

Exports dashboard configurations from Metabase to JSON files for version control.

Usage:
    # Export all dashboards
    python export_dashboards.py --metabase-url http://localhost:3000 \\
                                 --metabase-user admin@ibco-ca.us \\
                                 --metabase-password secret \\
                                 --output-dir ../dashboards/

    # Export single dashboard by ID
    python export_dashboards.py --dashboard-id 123 --output-dir ../dashboards/

    # Export single dashboard by name
    python export_dashboards.py --dashboard-name "Vallejo Fiscal Overview" \\
                                 --output-dir ../dashboards/
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class MetabaseExporter:
    """Export dashboards from Metabase API."""

    def __init__(self, base_url: str, username: str, password: str):
        """Initialize Metabase exporter."""
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

    def get_all_dashboards(self) -> List[Dict[str, Any]]:
        """Get all dashboards."""
        url = f"{self.base_url}/api/dashboard"
        response = self.session.get(url)
        response.raise_for_status()

        return response.json()

    def get_dashboard_by_id(self, dashboard_id: int) -> Dict[str, Any]:
        """Get dashboard by ID with full details."""
        url = f"{self.base_url}/api/dashboard/{dashboard_id}"
        response = self.session.get(url)
        response.raise_for_status()

        return response.json()

    def get_dashboard_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get dashboard by name."""
        dashboards = self.get_all_dashboards()
        for dashboard in dashboards:
            if dashboard["name"] == name:
                return self.get_dashboard_by_id(dashboard["id"])

        return None

    def get_question(self, question_id: int) -> Dict[str, Any]:
        """Get question (card) details."""
        url = f"{self.base_url}/api/card/{question_id}"
        response = self.session.get(url)
        response.raise_for_status()

        return response.json()

    def convert_dashboard_to_config(self, dashboard: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Metabase dashboard format to our JSON config format."""
        # Get all questions used in dashboard
        questions = []
        question_id_map = {}

        for idx, card in enumerate(dashboard.get("ordered_cards", [])):
            card_id = card["card_id"]

            # Fetch full question details
            question = self.get_question(card_id)

            # Generate question ID for our config
            question_config_id = f"q{idx + 1}"
            question_id_map[card_id] = question_config_id

            # Convert to our format
            question_config = {
                "id": question_config_id,
                "name": question["name"],
                "description": question.get("description", ""),
                "visualization": {
                    "type": question["display"],
                },
                "query": {
                    "database": "ibco_production",
                    "type": question["dataset_query"]["type"],
                },
                "display": question.get("visualization_settings", {}),
            }

            # Add native query if present
            if question["dataset_query"]["type"] == "native":
                question_config["query"]["native"] = question["dataset_query"]["native"]

            questions.append(question_config)

        # Build layout
        layout = {
            "width": 12,
            "cards": [],
        }

        for card in dashboard.get("ordered_cards", []):
            card_id = card["card_id"]
            question_config_id = question_id_map[card_id]

            layout["cards"].append({
                "id": f"card_{question_config_id}",
                "question_id": question_config_id,
                "row": card.get("row", 0),
                "col": card.get("col", 0),
                "size_x": card.get("sizeX", 6),
                "size_y": card.get("sizeY", 4),
            })

        # Check if dashboard has public sharing enabled
        public_enabled = False
        public_url = None
        if dashboard.get("public_uuid"):
            public_enabled = True
            public_url = f"{self.base_url}/public/dashboard/{dashboard['public_uuid']}"

        # Build complete config
        config = {
            "name": dashboard["name"],
            "description": dashboard.get("description", ""),
            "dashboard_version": "1.0",
            "created_for": "IBCo Vallejo Console",
            "parameters": dashboard.get("parameters", []),
            "questions": questions,
            "layout": layout,
            "public_access": {
                "enabled": public_enabled,
                "embedding_enabled": public_enabled,
                "signed_embedding": False,
                "auto_refresh_interval": 86400,
            },
            "metadata": {
                "created_by": "IBCo System",
                "version": "1.0",
                "metabase_dashboard_id": dashboard["id"],
                "exported_at": dashboard.get("updated_at", ""),
                "data_source": "PostgreSQL - IBCo Production Database",
                "public_url": public_url,
            },
        }

        return config

    def export_dashboard(self, dashboard_id: int, output_dir: Path) -> Path:
        """Export single dashboard to JSON file."""
        dashboard = self.get_dashboard_by_id(dashboard_id)
        config = self.convert_dashboard_to_config(dashboard)

        # Generate filename from dashboard name
        filename = dashboard["name"].lower().replace(" ", "_").replace("-", "_")
        filename = f"{filename}.json"
        output_file = output_dir / filename

        # Write to file
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(config, f, indent=2)

        print(f"✓ Exported '{dashboard['name']}' to {output_file}")
        return output_file

    def export_all_dashboards(self, output_dir: Path) -> List[Path]:
        """Export all dashboards to JSON files."""
        dashboards = self.get_all_dashboards()
        exported_files = []

        print(f"\nExporting {len(dashboards)} dashboard(s)...\n")

        for dashboard in dashboards:
            try:
                output_file = self.export_dashboard(dashboard["id"], output_dir)
                exported_files.append(output_file)
            except Exception as e:
                print(f"✗ Failed to export '{dashboard['name']}': {e}")
                continue

        return exported_files


def main():
    parser = argparse.ArgumentParser(
        description="Export Metabase dashboard configurations to JSON"
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
        "--output-dir",
        type=Path,
        default=Path("../dashboards"),
        help="Output directory for JSON files (default: ../dashboards)",
    )
    parser.add_argument(
        "--dashboard-id",
        type=int,
        help="Export single dashboard by ID",
    )
    parser.add_argument(
        "--dashboard-name",
        help="Export single dashboard by name",
    )

    args = parser.parse_args()

    # Get password from args or environment
    import os

    password = args.metabase_password or os.getenv("METABASE_ADMIN_PASSWORD")
    if not password:
        print(
            "Error: Metabase password required "
            "(--metabase-password or METABASE_ADMIN_PASSWORD env var)"
        )
        sys.exit(1)

    # Initialize exporter
    exporter = MetabaseExporter(args.metabase_url, args.metabase_user, password)
    exporter.authenticate()

    # Export dashboards
    exported_files = []

    if args.dashboard_id:
        # Export single dashboard by ID
        print(f"\nExporting dashboard ID {args.dashboard_id}...\n")
        try:
            output_file = exporter.export_dashboard(args.dashboard_id, args.output_dir)
            exported_files.append(output_file)
        except Exception as e:
            print(f"✗ Failed to export dashboard: {e}")
            sys.exit(1)

    elif args.dashboard_name:
        # Export single dashboard by name
        print(f"\nExporting dashboard '{args.dashboard_name}'...\n")
        try:
            dashboard = exporter.get_dashboard_by_name(args.dashboard_name)
            if not dashboard:
                print(f"✗ Dashboard '{args.dashboard_name}' not found")
                sys.exit(1)

            output_file = exporter.export_dashboard(dashboard["id"], args.output_dir)
            exported_files.append(output_file)
        except Exception as e:
            print(f"✗ Failed to export dashboard: {e}")
            sys.exit(1)

    else:
        # Export all dashboards
        try:
            exported_files = exporter.export_all_dashboards(args.output_dir)
        except Exception as e:
            print(f"✗ Failed to export dashboards: {e}")
            sys.exit(1)

    # Summary
    print(f"\n{'=' * 60}")
    print("Export Summary")
    print(f"{'=' * 60}")
    print(f"Exported {len(exported_files)} dashboard(s) to {args.output_dir}")
    print()

    for file in exported_files:
        print(f"  • {file.name}")

    print(f"\n✓ Export complete!")
    print(f"\nNext steps:")
    print(f"  1. Review exported JSON files in {args.output_dir}")
    print(f"  2. Commit changes to version control: git add {args.output_dir} && git commit")
    print(f"  3. Push to remote: git push")


if __name__ == "__main__":
    main()
