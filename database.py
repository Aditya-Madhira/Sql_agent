# database.py

import sqlite3
from sqlite3 import Error
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Database file path
DB_FILE = "employee_database.db"


def initialize_database(force_recreate=False):
    """
    Initialize the database by creating a connection and setting up tables.

    Args:
        force_recreate (bool): If True, recreate the database from scratch
    """
    # If force_recreate is True and the database exists, delete it
    if force_recreate and os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
            logger.info(f"🗑️ Deleted existing database file: {DB_FILE}")
        except OSError as e:
            logger.error(f"❌ Could not delete database file: {e}")
            return False

    conn = create_connection()
    if conn is None:
        logger.error("❌ Error: Could not establish database connection for initialization.")
        return False

    try:
        # Get the list of tables that already exist
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [table[0] for table in cursor.fetchall()]

        # Log existing tables
        if existing_tables:
            logger.info(f"📋 Found existing tables: {existing_tables}")

        # If employees table exists and force_recreate is True, drop it
        if 'employees' in existing_tables and force_recreate:
            cursor.execute("DROP TABLE employees")
            logger.info("🗑️ Dropped existing employees table")
            existing_tables.remove('employees')

        # Create the employees table with the correct schema
        create_tables(conn)

        # Verify the schema of the employees table
        cursor.execute("PRAGMA table_info(employees)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        logger.info(f"✅ Verified employees table schema: {column_names}")

        expected_columns = ['id', 'name', 'department', 'position', 'email',
                            'phone', 'address', 'hire_date', 'date_of_birth',
                            'ssn', 'username']

        # Check if all expected columns are present
        missing_columns = [col for col in expected_columns if col not in column_names]
        if missing_columns:
            logger.error(f"❌ Missing columns in employees table: {missing_columns}")
            return False

        logger.info("✅ Database initialized successfully")
        return True
    except Error as e:
        logger.error(f"❌ Error initializing database: {e}")
        return False
    finally:
        conn.close()


def create_connection():
    """Create a database connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        logger.info(f"🔌 Successfully connected to database: {DB_FILE}")
        return conn
    except Error as e:
        logger.error(f"❌ Error connecting to database: {e}")

    return conn


def create_tables(conn):
    """Create the employees table if it doesn't exist."""
    try:
        cursor = conn.cursor()

        # First drop the table if it exists with incorrect schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='employees'")
        table_def = cursor.fetchone()

        # Check if all required columns are in the table definition
        required_columns = ['email', 'phone', 'address', 'hire_date', 'date_of_birth', 'ssn', 'username']
        missing_columns = []

        if table_def:
            table_sql = table_def[0]
            for col in required_columns:
                if col not in table_sql:
                    missing_columns.append(col)

            if missing_columns:
                logger.warning(f"⚠️ Table exists but missing columns: {missing_columns}")
                cursor.execute("DROP TABLE employees")
                logger.info("🔄 Dropped and will recreate employees table with correct schema")

        # Create the table with the full schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                position TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                hire_date TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                ssn TEXT NOT NULL,
                username TEXT NOT NULL
            )
        ''')
        conn.commit()
        logger.info("✅ Table 'employees' created or already exists with correct schema")
    except Error as e:
        logger.error(f"❌ Error creating tables: {e}")


def clear_table(table_name):
    """Clear all data from a table."""
    conn = create_connection()
    if conn is None:
        logger.error("❌ Error connecting to the database.")
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name}")
        conn.commit()
        logger.info(f"🧹 All data cleared from {table_name}")
        return True
    except Error as e:
        logger.error(f"❌ Error clearing table {table_name}: {e}")
        return False
    finally:
        conn.close()


# Execute database initialization if this script is run directly
if __name__ == "__main__":
    print("Initializing database with correct schema...")
    success = initialize_database(force_recreate=True)
    if success:
        print("Database initialization successful!")
    else:
        print("Database initialization failed!")