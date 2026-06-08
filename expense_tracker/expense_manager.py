"""
Expense management operations
"""

import sqlite3
from datetime import datetime, timedelta
from database import create_connection, get_all_categories
from models import Expense, ExpenseSummary
from config import DATE_FORMAT, CURRENCY_SYMBOL


class ExpenseManager:
    """Manages expense operations"""
    
    @staticmethod
    def add_expense(user_id, amount, category_id, expense_date, description=''):
        """Add a new expense"""
        if amount <= 0:
            print("✗ Amount must be greater than 0")
            return None
        
        try:
            # Validate date format
            datetime.strptime(expense_date, DATE_FORMAT)
        except ValueError:
            print(f"✗ Invalid date format. Use {DATE_FORMAT}")
            return None
        
        conn = create_connection()
        if conn is None:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO expenses (user_id, category_id, amount, expense_date, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, category_id, amount, expense_date, description))
            conn.commit()
            expense_id = cursor.lastrowid
            conn.close()
            print(f"✓ Expense recorded successfully! (ID: {expense_id})")
            return expense_id
        except sqlite3.Error as e:
            print(f"✗ Error adding expense: {e}")
            conn.close()
            return None
    
    @staticmethod
    def get_all_expenses(user_id):
        """Get all expenses for a user"""
        conn = create_connection()
        if conn is None:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.expense_id, e.user_id, e.category_id, e.amount, 
                       e.expense_date, e.description, c.category_name
                FROM expenses e
                JOIN categories c ON e.category_id = c.category_id
                WHERE e.user_id = ?
                ORDER BY e.expense_date DESC
            ''', (user_id,))
            expenses = cursor.fetchall()
            conn.close()
            return expenses
        except sqlite3.Error as e:
            print(f"✗ Error retrieving expenses: {e}")
            conn.close()
            return []
    
    @staticmethod
    def get_expenses_by_date_range(user_id, start_date, end_date):
        """Get expenses within a date range"""
        conn = create_connection()
        if conn is None:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.expense_id, e.user_id, e.category_id, e.amount, 
                       e.expense_date, e.description, c.category_name
                FROM expenses e
                JOIN categories c ON e.category_id = c.category_id
                WHERE e.user_id = ? AND e.expense_date BETWEEN ? AND ?
                ORDER BY e.expense_date DESC
            ''', (user_id, start_date, end_date))
            expenses = cursor.fetchall()
            conn.close()
            return expenses
        except sqlite3.Error as e:
            print(f"✗ Error retrieving expenses: {e}")
            conn.close()
            return []
    
    @staticmethod
    def get_expenses_by_category(user_id, category_id):
        """Get expenses for a specific category"""
        conn = create_connection()
        if conn is None:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.expense_id, e.user_id, e.category_id, e.amount, 
                       e.expense_date, e.description, c.category_name
                FROM expenses e
                JOIN categories c ON e.category_id = c.category_id
                WHERE e.user_id = ? AND e.category_id = ?
                ORDER BY e.expense_date DESC
            ''', (user_id, category_id))
            expenses = cursor.fetchall()
            conn.close()
            return expenses
        except sqlite3.Error as e:
            print(f"✗ Error retrieving expenses: {e}")
            conn.close()
            return []
    
    @staticmethod
    def get_expenses_by_month(user_id, month, year):
        """Get expenses for a specific month"""
        conn = create_connection()
        if conn is None:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.expense_id, e.user_id, e.category_id, e.amount, 
                       e.expense_date, e.description, c.category_name
                FROM expenses e
                JOIN categories c ON e.category_id = c.category_id
                WHERE e.user_id = ? AND strftime('%m', e.expense_date) = ? 
                      AND strftime('%Y', e.expense_date) = ?
                ORDER BY e.expense_date DESC
            ''', (user_id, f'{month:02d}', str(year)))
            expenses = cursor.fetchall()
            conn.close()
            return expenses
        except sqlite3.Error as e:
            print(f"✗ Error retrieving expenses: {e}")
            conn.close()
            return []
    
    @staticmethod
    def get_expense_summary(user_id):
        """Get summary statistics for all expenses"""
        conn = create_connection()
        if conn is None:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) as total,
                       COUNT(*) as count,
                       COALESCE(AVG(amount), 0) as average,
                       COALESCE(MIN(amount), 0) as min_amount,
                       COALESCE(MAX(amount), 0) as max_amount
                FROM expenses
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return ExpenseSummary(
                    total=row[0],
                    count=row[1],
                    average=row[2],
                    min_amount=row[3],
                    max_amount=row[4]
                )
            return None
        except sqlite3.Error as e:
            print(f"✗ Error retrieving summary: {e}")
            conn.close()
            return None
    
    @staticmethod
    def get_monthly_summary(user_id, month, year):
        """Get category-wise summary for a specific month"""
        conn = create_connection()
        if conn is None:
            return []
        
        try:
            # Get total for the month
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) as total
                FROM expenses
                WHERE user_id = ? AND strftime('%m', expense_date) = ? 
                      AND strftime('%Y', expense_date) = ?
            ''', (user_id, f'{month:02d}', str(year)))
            
            total_result = cursor.fetchone()
            total_amount = total_result[0] if total_result else 0
            
            # Get category-wise breakdown
            cursor.execute('''
                SELECT c.category_name, COALESCE(SUM(e.amount), 0) as category_total, COUNT(e.expense_id) as count
                FROM categories c
                LEFT JOIN expenses e ON c.category_id = e.category_id 
                       AND e.user_id = ? AND strftime('%m', e.expense_date) = ? 
                       AND strftime('%Y', e.expense_date) = ?
                GROUP BY c.category_id, c.category_name
                HAVING category_total > 0
                ORDER BY category_total DESC
            ''', (user_id, f'{month:02d}', str(year)))
            
            categories = cursor.fetchall()
            conn.close()
            
            return {
                'total': total_amount,
                'categories': categories
            }
        except sqlite3.Error as e:
            print(f"✗ Error retrieving monthly summary: {e}")
            conn.close()
            return {'total': 0, 'categories': []}
    
    @staticmethod
    def get_daily_spending_trends(user_id, month, year):
        """Get daily spending trends for a month"""
        conn = create_connection()
        if conn is None:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT expense_date, SUM(amount) as daily_total, COUNT(*) as count
                FROM expenses
                WHERE user_id = ? AND strftime('%m', expense_date) = ? 
                      AND strftime('%Y', expense_date) = ?
                GROUP BY expense_date
                ORDER BY expense_date ASC
            ''', (user_id, f'{month:02d}', str(year)))
            
            trends = cursor.fetchall()
            conn.close()
            return trends
        except sqlite3.Error as e:
            print(f"✗ Error retrieving trends: {e}")
            conn.close()
            return []
    
    @staticmethod
    def delete_expense(expense_id, user_id):
        """Delete an expense"""
        conn = create_connection()
        if conn is None:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM expenses WHERE expense_id = ? AND user_id = ?', 
                          (expense_id, user_id))
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            
            if affected > 0:
                print(f"✓ Expense deleted successfully!")
                return True
            else:
                print("✗ Expense not found")
                return False
        except sqlite3.Error as e:
            print(f"✗ Error deleting expense: {e}")
            conn.close()
            return False
    
    @staticmethod
    def update_expense(expense_id, user_id, amount=None, category_id=None, 
                      expense_date=None, description=None):
        """Update an expense"""
        conn = create_connection()
        if conn is None:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Build dynamic update query
            updates = []
            params = []
            
            if amount is not None:
                if amount <= 0:
                    print("✗ Amount must be greater than 0")
                    return False
                updates.append("amount = ?")
                params.append(amount)
            
            if category_id is not None:
                updates.append("category_id = ?")
                params.append(category_id)
            
            if expense_date is not None:
                try:
                    datetime.strptime(expense_date, DATE_FORMAT)
                    updates.append("expense_date = ?")
                    params.append(expense_date)
                except ValueError:
                    print(f"✗ Invalid date format. Use {DATE_FORMAT}")
                    return False
            
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            
            if not updates:
                print("✗ No updates provided")
                return False
            
            params.append(expense_id)
            params.append(user_id)
            
            query = f"UPDATE expenses SET {', '.join(updates)} WHERE expense_id = ? AND user_id = ?"
            cursor.execute(query, params)
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            
            if affected > 0:
                print(f"✓ Expense updated successfully!")
                return True
            else:
                print("✗ Expense not found")
                return False
        except sqlite3.Error as e:
            print(f"✗ Error updating expense: {e}")
            conn.close()
            return False
