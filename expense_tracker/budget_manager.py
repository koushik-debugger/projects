"""
Budget management operations
"""

import sqlite3
from datetime import datetime
from database import create_connection, get_all_categories
from models import Budget
from config import CURRENCY_SYMBOL


class BudgetManager:
    """Manages budget operations"""
    
    @staticmethod
    def set_budget(user_id, category_id, monthly_limit, month_year):
        """Set or update a budget for a category"""
        if monthly_limit <= 0:
            print("✗ Budget limit must be greater than 0")
            return None
        
        conn = create_connection()
        if conn is None:
            return None
        
        try:
            cursor = conn.cursor()
            
            # Try to update existing budget
            cursor.execute('''
                UPDATE budgets 
                SET monthly_limit = ?
                WHERE user_id = ? AND category_id = ? AND month_year = ?
            ''', (monthly_limit, user_id, category_id, month_year))
            
            if cursor.rowcount == 0:
                # Insert new budget
                cursor.execute('''
                    INSERT INTO budgets (user_id, category_id, monthly_limit, month_year)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, category_id, monthly_limit, month_year))
            
            conn.commit()
            budget_id = cursor.lastrowid
            conn.close()
            print(f"✓ Budget set successfully! (ID: {budget_id})")
            return budget_id
        except sqlite3.Error as e:
            print(f"✗ Error setting budget: {e}")
            conn.close()
            return None
    
    @staticmethod
    def get_budgets(user_id, month_year=None):
        """Get all budgets for a user"""
        conn = create_connection()
        if conn is None:
            return []
        
        try:
            cursor = conn.cursor()
            
            if month_year:
                cursor.execute('''
                    SELECT b.budget_id, b.user_id, b.category_id, b.monthly_limit, 
                           b.month_year, c.category_name
                    FROM budgets b
                    JOIN categories c ON b.category_id = c.category_id
                    WHERE b.user_id = ? AND b.month_year = ?
                    ORDER BY c.category_name
                ''', (user_id, month_year))
            else:
                cursor.execute('''
                    SELECT b.budget_id, b.user_id, b.category_id, b.monthly_limit, 
                           b.month_year, c.category_name
                    FROM budgets b
                    JOIN categories c ON b.category_id = c.category_id
                    WHERE b.user_id = ?
                    ORDER BY b.month_year DESC, c.category_name
                ''', (user_id,))
            
            budgets = cursor.fetchall()
            conn.close()
            return budgets
        except sqlite3.Error as e:
            print(f"✗ Error retrieving budgets: {e}")
            conn.close()
            return []
    
    @staticmethod
    def get_budget_status(user_id, month_year):
        """Get budget status for a specific month (including expenses)"""
        conn = create_connection()
        if conn is None:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.category_id, c.category_name, 
                       COALESCE(b.monthly_limit, 0) as budget_limit,
                       COALESCE(SUM(e.amount), 0) as spent_amount,
                       COALESCE(COUNT(e.expense_id), 0) as expense_count
                FROM categories c
                LEFT JOIN budgets b ON c.category_id = b.category_id 
                       AND b.user_id = ? AND b.month_year = ?
                LEFT JOIN expenses e ON c.category_id = e.category_id 
                       AND e.user_id = ? AND strftime('%Y-%m', e.expense_date) = ?
                GROUP BY c.category_id, c.category_name
                HAVING budget_limit > 0 OR spent_amount > 0
                ORDER BY c.category_name
            ''', (user_id, month_year, user_id, month_year))
            
            status = cursor.fetchall()
            conn.close()
            return status
        except sqlite3.Error as e:
            print(f"✗ Error retrieving budget status: {e}")
            conn.close()
            return []
    
    @staticmethod
    def check_budget_exceeded(user_id, month_year):
        """Check which budgets have been exceeded"""
        conn = create_connection()
        if conn is None:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.category_name, b.monthly_limit, 
                       COALESCE(SUM(e.amount), 0) as spent_amount,
                       COALESCE(SUM(e.amount), 0) - b.monthly_limit as exceeded_by
                FROM budgets b
                JOIN categories c ON b.category_id = c.category_id
                LEFT JOIN expenses e ON b.category_id = e.category_id 
                       AND e.user_id = b.user_id AND strftime('%Y-%m', e.expense_date) = b.month_year
                WHERE b.user_id = ? AND b.month_year = ?
                GROUP BY b.budget_id
                HAVING spent_amount > b.monthly_limit
                ORDER BY exceeded_by DESC
            ''', (user_id, month_year))
            
            exceeded = cursor.fetchall()
            conn.close()
            return exceeded
        except sqlite3.Error as e:
            print(f"✗ Error checking budget: {e}")
            conn.close()
            return []
    
    @staticmethod
    def get_remaining_budget(user_id, category_id, month_year):
        """Get remaining budget for a category in a month"""
        conn = create_connection()
        if conn is None:
            return None
        
        try:
            cursor = conn.cursor()
            
            # Get budget limit
            cursor.execute('''
                SELECT monthly_limit FROM budgets
                WHERE user_id = ? AND category_id = ? AND month_year = ?
            ''', (user_id, category_id, month_year))
            
            budget = cursor.fetchone()
            if not budget:
                conn.close()
                return None
            
            limit = budget[0]
            
            # Get spent amount
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) as spent
                FROM expenses
                WHERE user_id = ? AND category_id = ? AND strftime('%Y-%m', expense_date) = ?
            ''', (user_id, category_id, month_year))
            
            spent = cursor.fetchone()[0]
            conn.close()
            
            return limit - spent
        except sqlite3.Error as e:
            print(f"✗ Error calculating remaining budget: {e}")
            conn.close()
            return None
    
    @staticmethod
    def delete_budget(budget_id, user_id):
        """Delete a budget"""
        conn = create_connection()
        if conn is None:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM budgets WHERE budget_id = ? AND user_id = ?', 
                          (budget_id, user_id))
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            
            if affected > 0:
                print(f"✓ Budget deleted successfully!")
                return True
            else:
                print("✗ Budget not found")
                return False
        except sqlite3.Error as e:
            print(f"✗ Error deleting budget: {e}")
            conn.close()
            return False
