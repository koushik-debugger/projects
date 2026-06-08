from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable


DEFAULT_CATEGORIES = ("Food", "Transport", "Utilities", "Entertainment")
DB_PATH = Path("expense_tracker.db")
REPORT_DIR = Path("outputs")


@dataclass(frozen=True)
class Expense:
    expense_date: str
    category: str
    amount: float
    description: str


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            amount REAL NOT NULL CHECK (amount > 0),
            expense_date TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            amount REAL NOT NULL CHECK (amount >= 0),
            UNIQUE (user_id, month),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )
    conn.executemany(
        "INSERT OR IGNORE INTO categories (name) VALUES (?)",
        ((name,) for name in DEFAULT_CATEGORIES),
    )
    conn.execute("INSERT OR IGNORE INTO users (name) VALUES ('Default User')")
    conn.commit()


def parse_date(value: str) -> str:
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise ValueError("Use date format YYYY-MM-DD.") from exc


def parse_month(value: str) -> str:
    try:
        parsed = datetime.strptime(value.strip(), "%Y-%m")
    except ValueError as exc:
        raise ValueError("Use month format YYYY-MM.") from exc
    return parsed.strftime("%Y-%m")


def get_default_user_id(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT id FROM users WHERE name = 'Default User'").fetchone()
    if row is None:
        cur = conn.execute("INSERT INTO users (name) VALUES ('Default User')")
        conn.commit()
        return int(cur.lastrowid)
    return int(row["id"])


def list_categories(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT id, name FROM categories ORDER BY name").fetchall()


def get_category_id(conn: sqlite3.Connection, category_name: str) -> int:
    row = conn.execute(
        "SELECT id FROM categories WHERE lower(name) = lower(?)", (category_name.strip(),)
    ).fetchone()
    if row is None:
        raise ValueError(f"Unknown category: {category_name}")
    return int(row["id"])


def add_expense(conn: sqlite3.Connection, expense: Expense, user_id: int | None = None) -> int:
    if expense.amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    user_id = user_id or get_default_user_id(conn)
    category_id = get_category_id(conn, expense.category)
    expense_date = parse_date(expense.expense_date)
    cur = conn.execute(
        """
        INSERT INTO expenses (user_id, category_id, amount, expense_date, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, category_id, expense.amount, expense_date, expense.description.strip()),
    )
    conn.commit()
    return int(cur.lastrowid)


def set_budget(conn: sqlite3.Connection, month: str, amount: float, user_id: int | None = None) -> None:
    if amount < 0:
        raise ValueError("Budget cannot be negative.")
    user_id = user_id or get_default_user_id(conn)
    month = parse_month(month)
    conn.execute(
        """
        INSERT INTO budgets (user_id, month, amount)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, month) DO UPDATE SET amount = excluded.amount
        """,
        (user_id, month, amount),
    )
    conn.commit()


def monthly_summary(conn: sqlite3.Connection, month: str, user_id: int | None = None) -> dict:
    user_id = user_id or get_default_user_id(conn)
    month = parse_month(month)
    total_row = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total, COALESCE(AVG(amount), 0) AS average
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?
        """,
        (user_id, month),
    ).fetchone()
    by_category = conn.execute(
        """
        SELECT c.name AS category, SUM(e.amount) AS total, AVG(e.amount) AS average
        FROM expenses e
        JOIN categories c ON c.id = e.category_id
        WHERE e.user_id = ? AND strftime('%Y-%m', e.expense_date) = ?
        GROUP BY c.name
        ORDER BY total DESC
        """,
        (user_id, month),
    ).fetchall()
    daily = conn.execute(
        """
        SELECT expense_date, SUM(amount) AS total
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?
        GROUP BY expense_date
        ORDER BY expense_date
        """,
        (user_id, month),
    ).fetchall()
    budget_row = conn.execute(
        "SELECT amount FROM budgets WHERE user_id = ? AND month = ?", (user_id, month)
    ).fetchone()
    total = float(total_row["total"])
    budget = float(budget_row["amount"]) if budget_row else None
    return {
        "month": month,
        "total": total,
        "average": float(total_row["average"]),
        "budget": budget,
        "remaining": None if budget is None else budget - total,
        "top_category": by_category[0]["category"] if by_category else None,
        "by_category": by_category,
        "daily": daily,
    }


def search_by_date_range(
    conn: sqlite3.Connection, start_date: str, end_date: str, user_id: int | None = None
) -> list[sqlite3.Row]:
    user_id = user_id or get_default_user_id(conn)
    start_date = parse_date(start_date)
    end_date = parse_date(end_date)
    return conn.execute(
        """
        SELECT e.expense_date, c.name AS category, e.amount, e.description
        FROM expenses e
        JOIN categories c ON c.id = e.category_id
        WHERE e.user_id = ? AND e.expense_date BETWEEN ? AND ?
        ORDER BY e.expense_date, e.id
        """,
        (user_id, start_date, end_date),
    ).fetchall()


def search_by_category(
    conn: sqlite3.Connection, category: str, user_id: int | None = None
) -> list[sqlite3.Row]:
    user_id = user_id or get_default_user_id(conn)
    category_id = get_category_id(conn, category)
    return conn.execute(
        """
        SELECT e.expense_date, c.name AS category, e.amount, e.description
        FROM expenses e
        JOIN categories c ON c.id = e.category_id
        WHERE e.user_id = ? AND e.category_id = ?
        ORDER BY e.expense_date DESC, e.id DESC
        """,
        (user_id, category_id),
    ).fetchall()


def export_report(conn: sqlite3.Connection, month: str, report_dir: Path = REPORT_DIR) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    summary = monthly_summary(conn, month)
    report_path = report_dir / f"expense_report_{summary['month']}.csv"
    with report_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Month", summary["month"]])
        writer.writerow(["Total monthly expenses", f"{summary['total']:.2f}"])
        writer.writerow(["Average expense", f"{summary['average']:.2f}"])
        writer.writerow(["Budget", "" if summary["budget"] is None else f"{summary['budget']:.2f}"])
        writer.writerow(["Remaining", "" if summary["remaining"] is None else f"{summary['remaining']:.2f}"])
        writer.writerow(["Top spending category", summary["top_category"] or "None"])
        writer.writerow([])
        writer.writerow(["Category", "Total", "Average"])
        for row in summary["by_category"]:
            writer.writerow([row["category"], f"{row['total']:.2f}", f"{row['average']:.2f}"])
        writer.writerow([])
        writer.writerow(["Date", "Daily Total"])
        for row in summary["daily"]:
            writer.writerow([row["expense_date"], f"{row['total']:.2f}"])
    return report_path


def generate_chart(conn: sqlite3.Connection, month: str, report_dir: Path = REPORT_DIR) -> Path:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Install matplotlib to generate charts: pip install matplotlib") from exc

    report_dir.mkdir(parents=True, exist_ok=True)
    summary = monthly_summary(conn, month)
    chart_path = report_dir / f"daily_spending_{summary['month']}.png"
    dates = [row["expense_date"] for row in summary["daily"]]
    totals = [row["total"] for row in summary["daily"]]

    plt.figure(figsize=(9, 4.8))
    plt.plot(dates, totals, marker="o", color="#1f77b4")
    plt.title(f"Daily Spending Trends - {summary['month']}")
    plt.xlabel("Date")
    plt.ylabel("Amount")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()
    return chart_path


def format_rows(rows: Iterable[sqlite3.Row]) -> str:
    rows = list(rows)
    if not rows:
        return "No matching expenses found."
    lines = ["Date        | Category      | Amount    | Description", "-" * 58]
    for row in rows:
        lines.append(
            f"{row['expense_date']:<10} | {row['category']:<13} | {row['amount']:>8.2f} | {row['description'] or ''}"
        )
    return "\n".join(lines)


def print_summary(summary: dict) -> None:
    print(f"\nMonthly summary for {summary['month']}")
    print(f"Total monthly expenses: {summary['total']:.2f}")
    print(f"Average expense: {summary['average']:.2f}")
    print(f"Top spending category: {summary['top_category'] or 'None'}")
    if summary["budget"] is None:
        print("Budget: not set")
    else:
        status = "under budget" if summary["remaining"] >= 0 else "over budget"
        print(f"Budget: {summary['budget']:.2f}")
        print(f"Remaining: {summary['remaining']:.2f} ({status})")

    print("\nSpending by category")
    if not summary["by_category"]:
        print("No expenses for this month.")
    for row in summary["by_category"]:
        print(f"- {row['category']}: {row['total']:.2f} (avg {row['average']:.2f})")


def prompt_float(label: str) -> float:
    while True:
        try:
            return float(input(label).strip())
        except ValueError:
            print("Enter a valid number.")


def prompt_date(label: str) -> str:
    while True:
        try:
            return parse_date(input(label))
        except ValueError as exc:
            print(exc)


def prompt_month(label: str) -> str:
    while True:
        try:
            return parse_month(input(label))
        except ValueError as exc:
            print(exc)


def choose_category(conn: sqlite3.Connection) -> str:
    categories = list_categories(conn)
    print("\nCategories")
    for index, row in enumerate(categories, start=1):
        print(f"{index}. {row['name']}")
    while True:
        choice = input("Choose category number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(categories):
            return str(categories[int(choice) - 1]["name"])
        print("Choose a category from the list.")


def seed_demo_data(conn: sqlite3.Connection) -> None:
    user_id = get_default_user_id(conn)
    existing = conn.execute("SELECT COUNT(*) AS count FROM expenses WHERE user_id = ?", (user_id,)).fetchone()
    if existing["count"]:
        return
    today_month = date.today().strftime("%Y-%m")
    set_budget(conn, today_month, 1200.00, user_id)
    for item in (
        Expense(f"{today_month}-02", "Food", 42.50, "Groceries"),
        Expense(f"{today_month}-03", "Transport", 18.00, "Metro card"),
        Expense(f"{today_month}-05", "Utilities", 96.75, "Electricity bill"),
        Expense(f"{today_month}-07", "Entertainment", 35.00, "Movie night"),
        Expense(f"{today_month}-07", "Food", 16.20, "Lunch"),
    ):
        add_expense(conn, item, user_id)


def main() -> None:
    conn = connect()
    initialize_database(conn)

    actions = {
        "1": "Record expense",
        "2": "Set monthly budget",
        "3": "Monthly spending summary",
        "4": "Search by date range",
        "5": "Search by category",
        "6": "Export monthly report",
        "7": "Generate daily spending chart",
        "8": "Add demo data",
        "0": "Exit",
    }

    while True:
        print("\nPersonal Expense Tracker")
        for key, label in actions.items():
            print(f"{key}. {label}")
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                expense_date = prompt_date("Date (YYYY-MM-DD): ")
                category = choose_category(conn)
                amount = prompt_float("Amount: ")
                description = input("Description: ")
                expense_id = add_expense(conn, Expense(expense_date, category, amount, description))
                print(f"Expense #{expense_id} recorded.")
            elif choice == "2":
                month = prompt_month("Month (YYYY-MM): ")
                amount = prompt_float("Budget amount: ")
                set_budget(conn, month, amount)
                print("Budget saved.")
            elif choice == "3":
                print_summary(monthly_summary(conn, prompt_month("Month (YYYY-MM): ")))
            elif choice == "4":
                rows = search_by_date_range(
                    conn,
                    prompt_date("Start date (YYYY-MM-DD): "),
                    prompt_date("End date (YYYY-MM-DD): "),
                )
                print("\n" + format_rows(rows))
            elif choice == "5":
                rows = search_by_category(conn, choose_category(conn))
                print("\n" + format_rows(rows))
            elif choice == "6":
                report_path = export_report(conn, prompt_month("Month (YYYY-MM): "))
                print(f"Report exported to {report_path}")
            elif choice == "7":
                chart_path = generate_chart(conn, prompt_month("Month (YYYY-MM): "))
                print(f"Chart saved to {chart_path}")
            elif choice == "8":
                seed_demo_data(conn)
                print("Demo data is ready.")
            elif choice == "0":
                print("Goodbye.")
                break
            else:
                print("Choose a valid option.")
        except (RuntimeError, ValueError, sqlite3.Error) as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    main()
