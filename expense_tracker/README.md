# Personal Expense Tracker

A comprehensive Python-based expense tracking application with SQLite backend. Track your spending, manage budgets, generate reports, and visualize your financial habits.

## 🎯 Features

- **Record Expenses**: Log expenses with date, amount, category, and description
- **Expense Categories**: Food, Transport, Utilities, Entertainment, and more
- **Monthly Spending Summary**: View total expenses by month
- **Budget Tracking**: Set and monitor monthly budgets per category
- **Search Capabilities**: 
  - Search by date range
  - Search by category
  - Search by amount range
- **Reports & Analytics**:
  - Total monthly expenses
  - Top spending categories
  - Daily spending trends
  - Category-wise breakdown
- **Data Visualization**: Generate charts using matplotlib
- **Export Reports**: Export data to CSV files
- **User Management**: Support for multiple users with separate expense tracking

## 🛠️ Tech Stack

- **Language**: Python 3.8+
- **Database**: SQLite3
- **Data Analysis**: pandas, numpy
- **Visualization**: matplotlib
- **CLI**: Menu-driven interface

## 📋 Project Structure

```
expense_tracker/
├── README.md
├── requirements.txt
├── config.py              # Configuration settings
├── database.py            # Database connection and setup
├── models.py              # Data models and classes
├── expense_manager.py     # Expense operations
├── budget_manager.py      # Budget operations
├── report_generator.py    # Reports and analytics
├── visualizer.py          # Chart generation
├── csv_exporter.py        # CSV export functionality
├── main.py                # CLI menu interface
└── data/
    └── expenses.db        # SQLite database (auto-created)
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/koushik-debugger/my-projects.git
   cd my-projects/expense_tracker
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Categories Table
```sql
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Expenses Table
```sql
CREATE TABLE expenses (
    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    expense_date DATE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);
```

### Budgets Table
```sql
CREATE TABLE budgets (
    budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    monthly_limit REAL NOT NULL,
    month_year TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);
```

## 📝 Usage Examples

### Main Menu
```
===== PERSONAL EXPENSE TRACKER =====
1.  Add New Expense
2.  View All Expenses
3.  View Monthly Summary
4.  Search Expenses (By Date Range)
5.  Search Expenses (By Category)
6.  Set Monthly Budget
7.  View Budget Status
8.  Generate Reports
9.  Visualize Data
10. Export to CSV
11. Delete Expense
12. Exit

Enter your choice: 
```

### Adding an Expense
```
Enter expense amount: 250
Select category:
1. Food
2. Transport
3. Utilities
4. Entertainment
5. Other
Enter category (1-5): 1
Enter description: Grocery shopping
✓ Expense recorded successfully! (ID: 1)
```

### Viewing Monthly Summary
```
===== MONTHLY SUMMARY (2026-06) =====
Category          | Amount
------------------+--------
Food              | $450.00
Transport         | $120.00
Utilities         | $85.00
Entertainment     | $200.00
------------------+--------
Total             | $855.00
```

## 🧮 SQL Concepts Used

- **SUM()**: Calculate total expenses
- **AVG()**: Calculate average spending
- **GROUP BY**: Group expenses by category/date
- **ORDER BY**: Sort results
- **DATE FILTERING**: Filter by date ranges using strftime()
- **JOINs**: Combine data from multiple tables
- **FOREIGN KEYS**: Maintain referential integrity
- **AGGREGATE FUNCTIONS**: COUNT(), MIN(), MAX()

## 📈 Key Queries

### Total Monthly Expenses
```sql
SELECT SUM(amount) FROM expenses 
WHERE strftime('%Y-%m', expense_date) = '2026-06';
```

### Top Spending Category
```sql
SELECT categories.category_name, SUM(expenses.amount) as total
FROM expenses
JOIN categories ON expenses.category_id = categories.category_id
GROUP BY expenses.category_id
ORDER BY total DESC NOLIMIT 1;
```

### Daily Spending Trends
```sql
SELECT expense_date, SUM(amount) as daily_total
FROM expenses
GROUP BY expense_date
ORDER BY expense_date;
```

### Budget vs Actual
```sql
SELECT c.category_name, 
       b.monthly_limit as budget,
       SUM(e.amount) as spent,
       b.monthly_limit - SUM(e.amount) as remaining
FROM budgets b
JOIN categories c ON b.category_id = c.category_id
LEFT JOIN expenses e ON b.category_id = e.category_id
WHERE b.user_id = ? AND b.month_year = ?
GROUP BY b.budget_id;
```

## 📊 Visualization Examples

- **Pie Chart**: Category-wise expense distribution
- **Bar Chart**: Monthly spending trends
- **Line Chart**: Daily spending patterns
- **Horizontal Bar Chart**: Top spending categories
- **Histogram**: Expense amount distribution
- **Dashboard**: Multi-panel summary view

## 💾 Export Functionality

Export expense data to CSV with:
- ✅ All expenses
- ✅ Monthly summaries
- ✅ Category breakdowns
- ✅ Budget comparisons

## 🔒 Security Features

- User-specific expense tracking (separate data per user)
- Data validation for amounts and dates
- Input sanitization
- SQL injection prevention through parameterized queries

## 🎓 Learning Outcomes

Through this project, you'll learn:
- ✅ Database design and normalization
- ✅ SQL queries and aggregations
- ✅ Python OOP principles
- ✅ Data analysis with pandas
- ✅ Data visualization with matplotlib
- ✅ File I/O operations (CSV export)
- ✅ CLI application development
- ✅ Error handling and validation
- ✅ Configuration management
- ✅ Module organization

## 🚀 Future Enhancements

- [ ] Recurring expenses
- [ ] Multi-currency support
- [ ] Email expense reminders
- [ ] Mobile app version
- [ ] Cloud synchronization
- [ ] Advanced analytics (forecasting)
- [ ] Receipt image storage
- [ ] Expense sharing with family members
- [ ] Budget alerts
- [ ] Spending goals

## 📄 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

**Koushik Debugger**

---

Happy tracking! 💰📊
