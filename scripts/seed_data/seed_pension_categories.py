#!/usr/bin/env python3
"""
Seed standardized pension plan categories.

Documents the standard CalPERS plan types used in California municipalities.
This helps ensure consistency when importing pension data from various sources.
"""


def seed_pension_plan_categories() -> None:
    """
    Display standardized pension plan name categories.

    These are the common plan types found in CalPERS actuarial reports.
    """

    # Standard CalPERS plan types
    plan_descriptions = {
        "Miscellaneous": "Non-safety employees (general admin, public works, clerical, etc.)",
        "Safety - Police": "Police officers and sworn public safety personnel",
        "Safety - Fire": "Firefighters and fire department personnel",
        "Safety - Other": "Other safety personnel not classified as police or fire",
        "PEPRA Miscellaneous": "Miscellaneous employees hired after 1/1/2013 (PEPRA reform)",
        "PEPRA Safety": "Safety employees hired after 1/1/2013 (PEPRA reform)",
    }

    print("=" * 70)
    print("Standard CalPERS Plan Types")
    print("=" * 70)
    print()

    for plan_name, description in plan_descriptions.items():
        print(f"  {plan_name:25} - {description}")

    print()
    print("Notes:")
    print("  - PEPRA = Public Employees' Pension Reform Act of 2013")
    print("  - Most cities have at least Miscellaneous and Safety plans")
    print("  - Post-2013, cities have both legacy and PEPRA plans")
    print("  - Safety plans typically have higher benefits = higher costs")
    print()
    print("These standardized names will be used when importing pension data")
    print("from CalPERS actuarial valuation reports.")
    print()

    # Additional context
    print("=" * 70)
    print("Typical Benefit Formulas")
    print("=" * 70)
    print()
    print("Pre-PEPRA (hired before 1/1/2013):")
    print("  - Miscellaneous: 2.5% @ 55 or 2.7% @ 55")
    print("  - Safety: 3% @ 50 or 3% @ 55")
    print()
    print("PEPRA (hired on/after 1/1/2013):")
    print("  - Miscellaneous: 2% @ 62")
    print("  - Safety: 2.7% @ 57")
    print()
    print("Formula explanation: 2.5% @ 55 means:")
    print("  - Employee gets 2.5% of final salary per year of service")
    print("  - Full retirement benefits available at age 55")
    print("  - Example: 20 years service = 50% of final salary (20 * 2.5%)")
    print()

    # Vallejo-specific context
    print("=" * 70)
    print("Vallejo Context")
    print("=" * 70)
    print()
    print("Vallejo's 2008 Chapter 9 bankruptcy was driven by:")
    print("  1. Generous pension formulas (3% @ 50 for safety)")
    print("  2. Rising CalPERS contributions")
    print("  3. Declining revenues (Great Recession)")
    print()
    print("Post-bankruptcy, Vallejo:")
    print("  - Reduced staffing significantly")
    print("  - Maintained pension obligations (CalPERS protected)")
    print("  - Still faces rising pension costs")
    print()
    print("As of FY 2022-23, Vallejo's pension costs consume ~30% of payroll")
    print("and continue to grow as CalPERS amortizes unfunded liabilities.")
    print()


def display_calpers_discount_rate_history() -> None:
    """Display CalPERS discount rate changes and their impact."""

    print("=" * 70)
    print("CalPERS Discount Rate History")
    print("=" * 70)
    print()
    print("The discount rate is THE critical assumption for pension liabilities.")
    print("When it drops, liabilities explode.")
    print()

    discount_rate_history = [
        ("2000-2012", "7.75%", "Aggressive assumption during bull market"),
        ("2012-2016", "7.50%", "First reduction amid concerns"),
        ("2016-2021", "7.00%", "Major reduction, huge liability spike"),
        ("2021-present", "6.80%", "Current rate, further liability increase"),
    ]

    print("Year Range    Rate    Impact")
    print("-" * 70)
    for period, rate, impact in discount_rate_history:
        print(f"{period:12}  {rate:6}  {impact}")

    print()
    print("Impact on Vallejo:")
    print("  - Each 0.25% reduction adds ~$10-15M to unfunded liability")
    print("  - Drop from 7.75% to 6.8% = massive increase in UAL")
    print("  - Higher UAL = higher annual contributions required")
    print()


if __name__ == "__main__":
    seed_pension_plan_categories()
    print()
    display_calpers_discount_rate_history()
