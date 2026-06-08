import sqlite3
import tempfile
import unittest
from pathlib import Path

from expense_tracker import (
    Expense,
    add_expense,
    connect,
    export_report,
    initialize_database,
    monthly_summary,
    search_by_category,
    search_by_date_range,
    set_budget,
)


class ExpenseTrackerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.conn = connect(self.db_path)
        initialize_database(self.conn)

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def test_records_and_summarizes_expenses(self):
        set_budget(self.conn, "2026-06", 500)
        add_expense(self.conn, Expense("2026-06-01", "Food", 25.5, "Groceries"))
        add_expense(self.conn, Expense("2026-06-02", "Transport", 10, "Bus"))
        add_expense(self.conn, Expense("2026-06-03", "Food", 14.5, "Lunch"))

        summary = monthly_summary(self.conn, "2026-06")

        self.assertEqual(summary["total"], 50)
        self.assertEqual(summary["top_category"], "Food")
        self.assertEqual(summary["remaining"], 450)
        self.assertEqual(len(summary["daily"]), 3)

    def test_search_by_date_range_and_category(self):
        add_expense(self.conn, Expense("2026-06-01", "Food", 20, "Breakfast"))
        add_expense(self.conn, Expense("2026-06-10", "Utilities", 100, "Power"))
        add_expense(self.conn, Expense("2026-07-01", "Food", 30, "Dinner"))

        june_rows = search_by_date_range(self.conn, "2026-06-01", "2026-06-30")
        food_rows = search_by_category(self.conn, "Food")

        self.assertEqual(len(june_rows), 2)
        self.assertEqual(len(food_rows), 2)

    def test_export_report_creates_csv(self):
        add_expense(self.conn, Expense("2026-06-01", "Entertainment", 45, "Concert"))
        output_dir = Path(self.temp_dir.name) / "reports"

        report_path = export_report(self.conn, "2026-06", output_dir)

        self.assertTrue(report_path.exists())
        self.assertIn("Top spending category,Entertainment", report_path.read_text(encoding="utf-8"))

    def test_rejects_invalid_amount(self):
        with self.assertRaises(ValueError):
            add_expense(self.conn, Expense("2026-06-01", "Food", 0, "Invalid"))

    def test_foreign_keys_are_enabled(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                """
                INSERT INTO expenses (user_id, category_id, amount, expense_date, description)
                VALUES (999, 999, 1, '2026-06-01', 'bad row')
                """
            )


if __name__ == "__main__":
    unittest.main()
