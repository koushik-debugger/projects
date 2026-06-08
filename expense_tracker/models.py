"""
Data models for Expense Tracker
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    """User model"""
    username: str
    email: str
    user_id: int = None
    created_at: str = None
    
    def __repr__(self):
        return f"User(id={self.user_id}, username={self.username}, email={self.email})"


@dataclass
class Category:
    """Category model"""
    category_name: str
    category_id: int = None
    description: str = None
    created_at: str = None
    
    def __repr__(self):
        return f"Category(id={self.category_id}, name={self.category_name})"


@dataclass
class Expense:
    """Expense model"""
    amount: float
    expense_date: str
    category_id: int
    user_id: int
    expense_id: int = None
    description: str = None
    created_at: str = None
    
    def __repr__(self):
        return f"Expense(id={self.expense_id}, amount=${self.amount}, date={self.expense_date}, category_id={self.category_id})"
    
    def __str__(self):
        return f"${self.amount:.2f} - {self.expense_date} (Category ID: {self.category_id})"


@dataclass
class Budget:
    """Budget model"""
    monthly_limit: float
    month_year: str
    category_id: int
    user_id: int
    budget_id: int = None
    created_at: str = None
    
    def __repr__(self):
        return f"Budget(id={self.budget_id}, limit=${self.monthly_limit}, period={self.month_year})"


class ExpenseSummary:
    """Summary statistics for expenses"""
    
    def __init__(self, total: float, count: int, average: float, min_amount: float, max_amount: float):
        self.total = total
        self.count = count
        self.average = average
        self.min_amount = min_amount
        self.max_amount = max_amount
    
    def __repr__(self):
        return f"""
        ===== EXPENSE SUMMARY =====
        Total Expenses: ${self.total:.2f}
        Number of Expenses: {self.count}
        Average Expense: ${self.average:.2f}
        Minimum Expense: ${self.min_amount:.2f}
        Maximum Expense: ${self.max_amount:.2f}
        """


class CategorySummary:
    """Summary statistics for a category"""
    
    def __init__(self, category_name: str, total: float, count: int, percentage: float):
        self.category_name = category_name
        self.total = total
        self.count = count
        self.percentage = percentage
    
    def __repr__(self):
        return f"{self.category_name}: ${self.total:.2f} ({self.count} expenses - {self.percentage:.1f}%)"
