"""
Configuration settings for the Expense Tracker application
"""

import os

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'expenses.db')
DB_DIR = os.path.join(os.path.dirname(__file__), 'data')

# Default categories
DEFAULT_CATEGORIES = [
    'Food',
    'Transport',
    'Utilities',
    'Entertainment',
    'Healthcare',
    'Shopping',
    'Education',
    'Other'
]

# Date format
DATE_FORMAT = '%Y-%m-%d'
DISPLAY_DATE_FORMAT = '%d-%m-%Y'

# Currency symbol
CURRENCY_SYMBOL = '$'

# CSV export settings
CSV_EXPORT_DIR = os.path.join(os.path.dirname(__file__), 'exports')

# Chart settings
CHART_STYLE = 'default'
CHART_DPI = 100
CHART_FORMAT = 'png'

# Application settings
APP_NAME = 'Personal Expense Tracker'
APP_VERSION = '1.0.0'
