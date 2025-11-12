"""
Email notification utilities for data refresh workflows.

Sends notifications to operators when new source documents are available,
and sends reports to stakeholders after data refreshes are complete.
"""

import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

import structlog

from src.config.settings import settings

logger = structlog.get_logger(__name__)


class EmailNotificationService:
    """Service for sending email notifications."""

    def __init__(self):
        """Initialize email service with settings."""
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.enabled = settings.enable_email_notifications

    def send_email(
        self,
        to: List[str],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
    ) -> bool:
        """
        Send an email notification.

        Args:
            to: List of recipient email addresses
            subject: Email subject line
            body_text: Plain text email body
            body_html: Optional HTML email body

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning(
                "email_disabled",
                message="Email notifications are disabled in settings",
            )
            return False

        if not self.smtp_host or not self.smtp_user or not self.smtp_password:
            logger.error(
                "email_config_missing",
                message="Email configuration incomplete. Check SMTP settings.",
            )
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_email
            msg["To"] = ", ".join(to)
            msg["Subject"] = subject

            # Attach text part
            msg.attach(MIMEText(body_text, "plain"))

            # Attach HTML part if provided
            if body_html:
                msg.attach(MIMEText(body_html, "html"))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(
                "email_sent",
                to=to,
                subject=subject,
            )
            return True

        except Exception as e:
            logger.error(
                "email_send_failed",
                error=str(e),
                to=to,
                subject=subject,
            )
            return False

    def send_cafr_available_notification(
        self,
        operator_emails: List[str],
        city_name: str,
        fiscal_year: int,
        document_url: str,
        document_title: Optional[str] = None,
    ) -> bool:
        """
        Notify operator that new CAFR is available for manual entry.

        Args:
            operator_emails: List of operator email addresses
            city_name: Name of the city
            fiscal_year: Fiscal year of the CAFR
            document_url: URL to the CAFR PDF
            document_title: Optional title of the document

        Returns:
            True if notification sent successfully
        """
        subject = f"[IBCo] New CAFR Available - {city_name} FY{fiscal_year}"

        body_text = f"""
New CAFR Available for Manual Entry

City: {city_name}
Fiscal Year: FY{fiscal_year}
Document: {document_title or 'CAFR'}

A new Comprehensive Annual Financial Report (CAFR) has been published and is ready for manual transcription.

Document URL: {document_url}

Estimated Entry Time: 60-120 minutes

Next Steps:
1. Download the CAFR from the URL above
2. Use the CAFR manual entry script: python scripts/data_entry/manual_cafr_entry.py
3. Enter data from the following sections:
   - Statement of Activities (Government-wide)
   - General Fund Revenues and Expenditures
   - Fund Balances
4. The system will automatically validate data and recalculate risk scores

Please acknowledge receipt of this notification and begin data entry when convenient.

---
IBCo Vallejo Console - Data Refresh System
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
        """.strip()

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .content {{ padding: 20px; background-color: #f9f9f9; margin-top: 20px; border-radius: 5px; }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .steps {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #3498db; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>📊 New CAFR Available for Manual Entry</h2>
        </div>

        <div class="content">
            <h3>Document Details</h3>
            <ul>
                <li><strong>City:</strong> {city_name}</li>
                <li><strong>Fiscal Year:</strong> FY{fiscal_year}</li>
                <li><strong>Document:</strong> {document_title or 'Comprehensive Annual Financial Report'}</li>
                <li><strong>Estimated Entry Time:</strong> 60-120 minutes</li>
            </ul>

            <a href="{document_url}" class="button">Download CAFR PDF</a>

            <div class="steps">
                <h4>Next Steps:</h4>
                <ol>
                    <li>Download the CAFR from the link above</li>
                    <li>Run the manual entry script: <code>python scripts/data_entry/manual_cafr_entry.py</code></li>
                    <li>Enter data from the following sections:
                        <ul>
                            <li>Statement of Activities (Government-wide)</li>
                            <li>General Fund Revenues and Expenditures</li>
                            <li>Fund Balances</li>
                        </ul>
                    </li>
                    <li>The system will automatically validate data and recalculate risk scores</li>
                </ol>
            </div>

            <p><em>Please acknowledge receipt of this notification and begin data entry when convenient.</em></p>
        </div>

        <div class="footer">
            <p>IBCo Vallejo Console - Data Refresh System<br>
            Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        return self.send_email(operator_emails, subject, body_text, body_html)

    def send_calpers_available_notification(
        self,
        operator_emails: List[str],
        city_name: str,
        fiscal_year: int,
        document_url: str,
    ) -> bool:
        """
        Notify operator that new CalPERS valuation is available.

        Args:
            operator_emails: List of operator email addresses
            city_name: Name of the city
            fiscal_year: Fiscal year of the valuation
            document_url: URL to the CalPERS valuation

        Returns:
            True if notification sent successfully
        """
        subject = f"[IBCo] New CalPERS Valuation Available - {city_name} FY{fiscal_year}"

        body_text = f"""
New CalPERS Valuation Available for Manual Entry

City: {city_name}
Fiscal Year: FY{fiscal_year}

A new CalPERS actuarial valuation has been published and is ready for manual transcription.

Document URL: {document_url}

Estimated Entry Time: 10-15 minutes

Next Steps:
1. Download the CalPERS valuation from the URL above
2. Use the CalPERS manual entry script: python scripts/data_entry/manual_calpers_entry.py
3. Enter the following data points:
   - Unfunded Actuarial Liability (UAL)
   - Funded Ratio
   - Annual Required Contribution (ARC)
   - Discount Rate
4. The system will automatically validate and update pension stress indicators

Please acknowledge receipt and begin data entry when convenient.

---
IBCo Vallejo Console - Data Refresh System
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
        """.strip()

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #e74c3c; color: white; padding: 20px; border-radius: 5px; }}
        .content {{ padding: 20px; background-color: #f9f9f9; margin-top: 20px; border-radius: 5px; }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #e74c3c;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .steps {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #e74c3c; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🏛️ New CalPERS Valuation Available</h2>
        </div>

        <div class="content">
            <h3>Document Details</h3>
            <ul>
                <li><strong>City:</strong> {city_name}</li>
                <li><strong>Fiscal Year:</strong> FY{fiscal_year}</li>
                <li><strong>Document Type:</strong> CalPERS Actuarial Valuation</li>
                <li><strong>Estimated Entry Time:</strong> 10-15 minutes</li>
            </ul>

            <a href="{document_url}" class="button">Download CalPERS Valuation</a>

            <div class="steps">
                <h4>Next Steps:</h4>
                <ol>
                    <li>Download the CalPERS valuation from the link above</li>
                    <li>Run the manual entry script: <code>python scripts/data_entry/manual_calpers_entry.py</code></li>
                    <li>Enter the following data points:
                        <ul>
                            <li>Unfunded Actuarial Liability (UAL)</li>
                            <li>Funded Ratio</li>
                            <li>Annual Required Contribution (ARC)</li>
                            <li>Discount Rate</li>
                        </ul>
                    </li>
                    <li>The system will automatically validate and update pension stress indicators</li>
                </ol>
            </div>

            <p><em>Please acknowledge receipt and begin data entry when convenient.</em></p>
        </div>

        <div class="footer">
            <p>IBCo Vallejo Console - Data Refresh System<br>
            Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        return self.send_email(operator_emails, subject, body_text, body_html)

    def send_refresh_complete_notification(
        self,
        stakeholder_emails: List[str],
        city_name: str,
        fiscal_year: int,
        report_url: Optional[str] = None,
        risk_score_change: Optional[dict] = None,
        fiscal_cliff_change: Optional[dict] = None,
    ) -> bool:
        """
        Notify stakeholders that data refresh is complete with summary report.

        Args:
            stakeholder_emails: List of stakeholder email addresses
            city_name: Name of the city
            fiscal_year: Fiscal year that was updated
            report_url: Optional URL to detailed change report
            risk_score_change: Optional dict with 'previous' and 'new' risk scores
            fiscal_cliff_change: Optional dict with 'previous' and 'new' fiscal cliff years

        Returns:
            True if notification sent successfully
        """
        subject = f"[IBCo] Data Refresh Complete - {city_name} FY{fiscal_year}"

        # Build change summary
        changes_text = []
        if risk_score_change:
            prev_score = risk_score_change.get("previous", "N/A")
            new_score = risk_score_change.get("new", "N/A")
            changes_text.append(f"Risk Score: {prev_score} → {new_score}")

        if fiscal_cliff_change:
            prev_year = fiscal_cliff_change.get("previous", "N/A")
            new_year = fiscal_cliff_change.get("new", "N/A")
            changes_text.append(f"Fiscal Cliff Year: {prev_year} → {new_year}")

        changes_summary = "\n".join(changes_text) if changes_text else "Data updated successfully"

        body_text = f"""
Data Refresh Complete

City: {city_name}
Fiscal Year: FY{fiscal_year}
Completed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

Summary of Changes:
{changes_summary}

New data has been successfully entered, validated, and analyzed. Risk scores and financial projections have been recalculated with the latest information.

{'View Detailed Change Report: ' + report_url if report_url else ''}

Dashboard: https://dashboard.ibco-ca.us/city/{city_name.lower().replace(' ', '-')}

---
IBCo Vallejo Console - Data Refresh System
        """.strip()

        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #27ae60; color: white; padding: 20px; border-radius: 5px; }}
        .content {{ padding: 20px; background-color: #f9f9f9; margin-top: 20px; border-radius: 5px; }}
        .changes {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #27ae60; }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #27ae60;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>✅ Data Refresh Complete</h2>
        </div>

        <div class="content">
            <h3>Refresh Details</h3>
            <ul>
                <li><strong>City:</strong> {city_name}</li>
                <li><strong>Fiscal Year:</strong> FY{fiscal_year}</li>
                <li><strong>Completed:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</li>
            </ul>

            <div class="changes">
                <h4>Summary of Changes:</h4>
                <ul>
                    {f'<li><strong>Risk Score:</strong> {risk_score_change.get("previous")} → {risk_score_change.get("new")}</li>' if risk_score_change else ''}
                    {f'<li><strong>Fiscal Cliff Year:</strong> {fiscal_cliff_change.get("previous")} → {fiscal_cliff_change.get("new")}</li>' if fiscal_cliff_change else ''}
                </ul>
                <p>New data has been successfully entered, validated, and analyzed. Risk scores and financial projections have been recalculated with the latest information.</p>
            </div>

            {f'<a href="{report_url}" class="button">View Detailed Change Report</a>' if report_url else ''}

            <a href="https://dashboard.ibco-ca.us/city/{city_name.lower().replace(' ', '-')}" class="button">View Dashboard</a>
        </div>

        <div class="footer">
            <p>IBCo Vallejo Console - Data Refresh System</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        return self.send_email(stakeholder_emails, subject, body_text, body_html)


# Global email service instance
email_service = EmailNotificationService()
