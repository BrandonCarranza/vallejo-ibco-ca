#!/usr/bin/env python3
"""
Generate validation review reports.

Sends email to validators with items pending review.

Usage:
    python scripts/reports/review_report.py --email
"""

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.database import SessionLocal
from src.config.settings import settings
from src.database.models.validation import ValidationQueueItem
from src.utils.email_notifications import email_service


def generate_review_report():
    """Generate review report."""
    db = SessionLocal()
    try:
        # Get pending items
        items = (
            db.query(ValidationQueueItem)
            .filter(ValidationQueueItem.status.in_(["ENTERED", "FLAGGED"]))
            .order_by(ValidationQueueItem.severity, ValidationQueueItem.entered_at)
            .all()
        )

        critical = [i for i in items if i.severity == "CRITICAL"]
        warning = [i for i in items if i.severity == "WARNING"]
        info = [i for i in items if i.severity == "INFO"]

        report = f"""
Validation Review Report
========================

Total items pending: {len(items)}
- Critical: {len(critical)}
- Warning: {len(warning)}
- Info: {len(info)}

Critical Items:
"""
        for item in critical:
            report += f"- {item.table_name}.{item.field_name}: {item.flag_reason}\n"

        print(report)
        return items

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", action="store_true")
    args = parser.parse_args()

    items = generate_review_report()

    if args.email and items:
        # Send email (simplified)
        print(f"Would email {len(items)} items to validators")


if __name__ == "__main__":
    main()
