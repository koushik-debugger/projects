"""
Report generation and analytics
"""

import sqlite3
from datetime import datetime, timedelta
from database import create_connection
from config import CURRENCY_SYMBOL, DATE_FORMAT


class ReportGenerator:
    """Generates various expense reports and analytics"""
    
    @staticmethod
    def get_top_spending_categories(user_id, limit=5):
        """Get top spending categories"""
        conn = create_connection()
        if conn is None:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.category_name, SUM(e.amount) as total, COUNT(e.expense_id) as count
                FROM expenses e
                JOIN categories c ON e.category_id = c.category_id
                WHERE e.user_id = ?
                GROUP BY e.category_id
                ORDER BY total DESC
                LIMIT ?
            ''', (user_id, limit))
            
            results = cursor.fetchall()
            conn.close()
            return results
        except sqlite3.Error as e:
            print(f"✗ Error generating report: {e}")
            conn.close()
            return []
    
    @staticmethod
    def get_monthly_comparison(user_id, months=12):
        """Get monthly spending comparison for the last N months"""
        conn = create_connection()
        if conn is None:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT strftime('%Y-%m', expense_date) as month, 
                       SUM(amount) as total,
                       COUNT(*) as expense_count
                FROM expenses
                WHERE user_id = ?
                GROUP BY strftime('%Y-%m', expense_date)
                ORDER BY month DESC
                LIMIT ?
            ''', (user_id, months))
            
            results = cursor.fetchall()
            conn.close()
            return results
        except sqlite3.Error as e:
            print(f"✗ Error generating report: {e}")
            conn.close()
            return []
    
    @staticmethod
    def get_category_wise_monthly_breakdown(user_id, month_year):
        """Get category-wise breakdown for a specific month"""
        conn = create_connection()
        if conn is None:
            return []
        
        try:
            cursor = conn.cursor()
            
            # Get total for the month
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) as total
                FROM expenses
                WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?
            ''', (user_id, month_year))
            
            total = cursor.fetchone()[0]
            
            # Get category breakdown
            cursor.execute('''
                SELECT c.category_name, 
                       COALESCE(SUM(e.amount), 0) as amount,
                       COUNT(e.expense_id) as count,
                       ROUND(COALESCE(SUM(e.amount), 0) * 100.0 / NULLIF(?, 0), 2) as percentage
                FROM categories c
                LEFT JOIN expenses e ON c.category_id = e.category_id 
                       AND e.user_id = ? AND strftime('%Y-%m', e.expense_date) = ?
                GROUP BY c.category_id
                HAVING amount > 0
                ORDER BY amount DESC
            ''', (total, user_id, month_year))
            
            results = cursor.fetchall()
            conn.close()
            return results, total
        except sqlite3.Error as e:
            print(f"✗ Error generating report: {e}")
            conn.close()
            return [], 0
    
    @staticmethod
    def get_weekly_spending(user_id, month_year):
        """Get weekly spending summary"""
        conn = create_connection()
        if conn is None:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    strftime('%Y-W%W', expense_date) as week,
                    SUM(amount) as weekly_total,
                    COUNT(*) as expense_count,
                    MIN(expense_date) as week_start,
                    MAX(expense_date) as week_end
                FROM expenses
                WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?
                GROUP BY strftime('%Y-W%W', expense_date)
                ORDER BY week
            ''', (user_id, month_year))
            
            results = cursor.fetchall()
            conn.close()
            return results
        except sqlite3.Error as e:
            print(f"✗ Error generating report: {e}")
            conn.close()
            return []
    
    @staticmethod
    def get_spending_statistics(user_id):
        """Get comprehensive spending statistics"""
        conn = create_connection()
        if conn is None:
            return None
        
        try:
            cursor = conn.cursor()
            
            # Total spending
            cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?', (user_id,))
            total_spending = cursor.fetchone()[0]
            
            # Number of transactions
            cursor.execute('SELECT COUNT(*) FROM expenses WHERE user_id = ?', (user_id,))
            total_transactions = cursor.fetchone()[0]
            
            # Average spending
            cursor.execute('SELECT COALESCE(AVG(amount), 0) FROM expenses WHERE user_id = ?', (user_id,))
            average_spending = cursor.fetchone()[0]
            
            # Highest expense
            cursor.execute('SELECT COALESCE(MAX(amount), 0) FROM expenses WHERE user_id = ?', (user_id,))
            highest_expense = cursor.fetchone()[0]
            
            # Lowest expense
            cursor.execute('SELECT COALESCE(MIN(amount), 0) FROM expenses WHERE user_id = ? AND amount > 0', (user_id,))
            lowest_expense = cursor.fetchone()[0]
            
            # Number of categories used
            cursor.execute('''
                SELECT COUNT(DISTINCT category_id) FROM expenses WHERE user_id = ?
            ''', (user_id,))
            categories_used = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_spending': total_spending,
                'total_transactions': total_transactions,
                'average_spending': average_spending,
                'highest_expense': highest_expense,
                'lowest_expense': lowest_expense,
                'categories_used': categories_used
            }
        except sqlite3.Error as e:
            print(f"✗ Error generating statistics: {e}")
            conn.close()
            return None
    
    @staticmethod
    def get_daily_average(user_id, month_year):
        """Get daily average spending for a month"""
        conn = create_connection()
        if conn is None:
            return 0
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COALESCE(AVG(daily_total), 0) as daily_average
                FROM (
                    SELECT SUM(amount) as daily_total
                    FROM expenses
                    WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?
                    GROUP BY expense_date
                )
            ''', (user_id, month_year))
            
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else 0
        except sqlite3.Error as e:
            print(f"✗ Error calculating daily average: {e}")
            conn.close()
            return 0
    
    @staticmethod
    def get_expense_distribution(user_id):
        """Get expense amount distribution (histogram data)"""
        conn = create_connection()
        if conn is None:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    CASE 
                        WHEN amount < 10 THEN '0-10'
                        WHEN amount < 25 THEN '10-25'
                        WHEN amount < 50 THEN '25-50'
                        WHEN amount < 100 THEN '50-100'
                        WHEN amount < 250 THEN '100-250'
                        ELSE '250+'
                    END as amount_range,
                    COUNT(*) as count,
                    SUM(amount) as total
                FROM expenses
                WHERE user_id = ?
                GROUP BY amount_range
                ORDER BY amount_range
            ''', (user_id,))
            
            results = cursor.fetchall()
            conn.close()
            return results
        except sqlite3.Error as e:
            print(f"✗ Error generating distribution: {e}")
            conn.close()
            return []
