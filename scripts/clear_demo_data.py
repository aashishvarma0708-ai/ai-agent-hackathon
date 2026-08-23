#!/usr/bin/env python3
"""
CivicResolve AI - Database Reset Utility (Optional Manual Tool)

Usage:
    python scripts/clear_demo_data.py

This script clears all records from the SQLite database tables:
  - complaints
  - status_history
  - escalations
  - evidence
  - supporting_reports
It preserves table schemas and indexes so you have a completely fresh, empty system.
"""

import sys
import os

# Add workspace root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.db import _conn, init_db


def clear_all_data():
    init_db()
    with _conn() as conn:
        conn.execute("DELETE FROM status_history")
        conn.execute("DELETE FROM escalations")
        conn.execute("DELETE FROM evidence")
        conn.execute("DELETE FROM supporting_reports")
        conn.execute("DELETE FROM complaints")
        conn.commit()
        print("✓ Successfully cleared all records from CivicResolve SQLite database.")
        print("✓ All tables and schema migrations are intact and ready for fresh real inputs.")


if __name__ == "__main__":
    confirm = input("Are you sure you want to clear all grievance records from SQLite? [y/N]: ")
    if confirm.strip().lower() == "y":
        clear_all_data()
    else:
        print("Operation cancelled. Database untouched.")
