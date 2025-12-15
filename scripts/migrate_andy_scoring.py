#!/usr/bin/env python3
"""
Migration script for Andy's Methodology scoring updates.

Adds new columns to the prospects table:
- competition_score (0-100, higher = less competition)
- market_saturation (low/medium/high/saturated)
- franchise_competition (bool)
- ads_in_market (int)
- industry_category (commoditised/standard/niche/specialist)
- industry_multiplier (0.4-1.6)
- gbp_has_website (bool)
- gbp_website_missing_opportunity (bool)

Also creates the search_metrics table for caching competition analysis.

Usage:
    python scripts/migrate_andy_scoring.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError

# Database path
DB_PATH = os.environ.get(
    "PROSPECT_DB_PATH",
    str(project_root / "prospects.db")
)


def get_existing_columns(engine, table_name: str) -> set:
    """Get set of existing column names for a table."""
    inspector = inspect(engine)
    try:
        columns = inspector.get_columns(table_name)
        return {col['name'] for col in columns}
    except Exception:
        return set()


def table_exists(engine, table_name: str) -> bool:
    """Check if a table exists."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def migrate_prospects_table(engine):
    """Add new columns to prospects table."""
    existing = get_existing_columns(engine, 'prospects')

    # New columns to add with their SQL definitions
    new_columns = [
        ("competition_score", "INTEGER DEFAULT 50"),
        ("market_saturation", "VARCHAR(20) DEFAULT 'medium'"),
        ("franchise_competition", "BOOLEAN DEFAULT 0"),
        ("ads_in_market", "INTEGER DEFAULT 0"),
        ("industry_category", "VARCHAR(20) DEFAULT 'standard'"),
        ("industry_multiplier", "FLOAT DEFAULT 1.0"),
        ("gbp_has_website", "BOOLEAN DEFAULT NULL"),
        ("gbp_website_missing_opportunity", "BOOLEAN DEFAULT 0"),
    ]

    with engine.connect() as conn:
        for col_name, col_def in new_columns:
            if col_name not in existing:
                try:
                    conn.execute(text(
                        f"ALTER TABLE prospects ADD COLUMN {col_name} {col_def}"
                    ))
                    conn.commit()
                    print(f"  + Added column: {col_name}")
                except OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"  ~ Column exists: {col_name}")
                    else:
                        raise
            else:
                print(f"  ~ Column exists: {col_name}")


def create_search_metrics_table(engine):
    """Create search_metrics table for caching competition analysis."""
    if table_exists(engine, 'search_metrics'):
        print("  ~ Table exists: search_metrics")
        return

    create_sql = """
    CREATE TABLE search_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query VARCHAR(255) NOT NULL,
        location VARCHAR(255) NOT NULL,
        ads_count INTEGER DEFAULT 0,
        organic_count INTEGER DEFAULT 0,
        maps_count INTEGER DEFAULT 0,
        franchise_count INTEGER DEFAULT 0,
        franchise_names TEXT,
        competition_score INTEGER DEFAULT 50,
        market_saturation VARCHAR(20) DEFAULT 'medium',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(query, location)
    )
    """

    with engine.connect() as conn:
        conn.execute(text(create_sql))
        conn.commit()
        print("  + Created table: search_metrics")


def recalculate_priority_scores(engine):
    """
    Optionally recalculate priority scores using new formula.

    New formula: Priority = (Fit x 0.3 + Opp x 0.5 + Comp x 0.2) x Industry Multiplier

    For existing data without competition analysis, we use default competition_score=50
    and industry_multiplier=1.0, which gives:
    Priority = (Fit x 0.3 + Opp x 0.5 + 50 x 0.2) x 1.0
             = Fit x 0.3 + Opp x 0.5 + 10
    """
    print("\n  Recalculating priority scores with new formula...")

    update_sql = """
    UPDATE prospects
    SET priority_score = (
        COALESCE(fit_score, 50) * 0.3 +
        COALESCE(opportunity_score, 50) * 0.5 +
        COALESCE(competition_score, 50) * 0.2
    ) * COALESCE(industry_multiplier, 1.0)
    """

    with engine.connect() as conn:
        result = conn.execute(text(update_sql))
        conn.commit()
        print(f"  + Updated {result.rowcount} prospect priority scores")


def main():
    """Run the migration."""
    print(f"Andy's Methodology Migration")
    print(f"=" * 50)
    print(f"Database: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print(f"\nDatabase not found at {DB_PATH}")
        print("No migration needed - columns will be created on first run.")
        return 0

    engine = create_engine(f"sqlite:///{DB_PATH}")

    print("\n1. Migrating prospects table...")
    migrate_prospects_table(engine)

    print("\n2. Creating search_metrics table...")
    create_search_metrics_table(engine)

    print("\n3. Recalculating priority scores...")
    recalculate_priority_scores(engine)

    print("\n" + "=" * 50)
    print("Migration complete!")
    print("\nNew features enabled:")
    print("  - Competition Score (market analysis)")
    print("  - Industry Multiplier (value weighting)")
    print("  - GBP Website Detection (easy win flagging)")
    print("\nRun a new search to see the updated scoring in action.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
