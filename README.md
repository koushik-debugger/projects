# Personal Expense Tracker

A menu-driven Python and SQLite app for recording expenses, tracking monthly budgets, searching spending, and exporting reports.

## Features

- Record expenses with date, amount, category, and description
- Default categories: Food, Transport, Utilities, Entertainment
- SQLite tables for `users`, `categories`, `expenses`, and `budgets`
- Monthly spending summary using `SUM()`, `AVG()`, `GROUP BY`, `ORDER BY`, and date filtering
- Budget tracking with remaining/over-budget status
- Search by date range
- Search by category
- Export monthly CSV reports to `outputs/`
- Optional daily spending chart generation with `matplotlib`

## Run

```bash
python expense_tracker.py
```

Choose option `8` to add demo data for the current month, then use the summary, export, or chart options.

## Optional Charts

Charts use `matplotlib`. If it is not installed, the rest of the app still works.

```bash
pip install matplotlib
```

## Test

```bash
python -m unittest test_expense_tracker.py
```

## Example Reports

- Total monthly expenses
- Top spending category
- Spending by category
- Daily spending trends

