"""
Database connection and initialization for the Expense Tracker
"""

import sqlite3
import os
from config import DB_PATH, DB_DIR, DEFAULT_CATEGORIES


def create_connection():
    """Create a database connection to SQLite database"""
    try:
        # Create data directory if it doesn't exist
        os.makedirs(DB_DIR, exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None


def init_database():
    """Initialize database with required tables"""
    conn = create_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Create Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create Categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create Expenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                expense_date DATE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            )
        ''')
        
        # Create Budgets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                monthly_limit REAL NOT NULL,
                month_year TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (category_id) REFERENCES categories(category_id),
                UNIQUE(user_id, category_id, month_year)
            )
        ''')
        
        conn.commit()
        
        # Insert default categories if they don't exist
        for category in DEFAULT_CATEGORIES:
            cursor.execute('''
                INSERT OR IGNORE INTO categories (category_name, description)
                VALUES (?, ?)
            ''', (category, f'{category} expenses'))
        
        conn.commit()
        conn.close()
        
        print("✓ Database initialized successfully!")
        return True
    
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
        if conn:
            conn.close()
        return False


def get_user_by_username(username):
    """Get user ID by username"""
    conn = create_connection()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    except sqlite3.Error as e:
        print(f"Error retrieving user: {e}")
        conn.close()
        return None


def create_user(username, email):
    """Create a new user"""
    conn = create_connection()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, email)
            VALUES (?, ?)
        ''', (username, email))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        print("✗ User already exists!")
        return None
    except sqlite3.Error as e:
        print(f"Error creating user: {e}")
        conn.close()
        return None


def get_all_categories():
    """Get all available categories"""
    conn = create_connection()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT category_id, category_name FROM categories ORDER BY category_name')
        categories = cursor.fetchall()
        conn.close()
        return categories
    except sqlite3.Error as e:
        print(f"Error retrieving categories: {e}")
        conn.close()
        return []


def get_category_id(category_name):
    """Get category ID by name"""
    conn = create_connection()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT category_id FROM categories WHERE category_name = ?', (category_name,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    except sqlite3.Error as e:
        print(f"Error retrieving category: {e}")
        conn.close()
        return None


def execute_query(query, params=None, fetch_one=False):
    """Execute a general query"""
    conn = create_connection()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if 'SELECT' in query.upper():
            result = cursor.fetchone() if fetch_one else cursor.fetchall()
        else:
            conn.commit()
            result = cursor.lastrowid if 'INSERT' in query.upper() else cursor.rowcount
        
        conn.close()
        return result
    except sqlite3.Error as e:
        print(f"Query execution error: {e}")
        conn.close()
        return None
