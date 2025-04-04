# etl.py

import logging
import time
import random
from datetime import datetime
import sqlite3
from faker import Faker
import schedule

# Import database functions
from database import create_connection, create_tables, clear_table

# Configure enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize Faker
fake = Faker()


def extract_data(num_records=50):
    """
    Extract phase: Generate data from Faker

    Args:
        num_records: Number of records to generate

    Returns:
        List of raw data dictionaries
    """
    start_time = time.time()
    logger.info(f"[EXTRACT] ⏳ Starting extraction of {num_records} records from Faker")

    raw_data = []

    for i in range(1, num_records + 1):
        # Generate all data using Faker methods only
        data = {
            "id": i,
            "name": fake.name(),
            "department": fake.job().split()[0],  # Using job word as department
            "position": fake.job(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "address": fake.address(),
            "hire_date": fake.date_this_decade().strftime('%Y-%m-%d'),
            "date_of_birth": fake.date_of_birth(minimum_age=22, maximum_age=65).strftime('%Y-%m-%d'),
            "ssn": fake.ssn(),
            "username": fake.user_name()
        }

        raw_data.append(data)

    end_time = time.time()
    duration = round(end_time - start_time, 2)
    logger.info(f"[EXTRACT] ✅ Successfully extracted {len(raw_data)} records in {duration} seconds")

    # Log a sample record (with sensitive data masked)
    if raw_data:
        sample = raw_data[0].copy()
        sample["ssn"] = "XXX-XX-XXXX"  # Mask sensitive data
        logger.info(f"[EXTRACT] 📋 Sample record: {sample}")

    return raw_data


def transform_data(raw_data):
    """
    Transform phase: Clean and prepare the data

    Args:
        raw_data: List of raw data dictionaries

    Returns:
        Transformed list of data dictionaries
    """
    start_time = time.time()
    logger.info(f"[TRANSFORM] ⏳ Starting transformation of {len(raw_data)} records")

    transformed_data = []
    departments_count = {}

    for record in raw_data:
        # Clean up the data - no hardcoded values, just transformations
        transformed_record = record.copy()

        # Clean up address (replace newlines with commas)
        transformed_record["address"] = record["address"].replace('\n', ', ')

        # Ensure consistent department naming
        transformed_record["department"] = record["department"].title()

        # Track department distribution
        dept = transformed_record["department"]
        if dept in departments_count:
            departments_count[dept] += 1
        else:
            departments_count[dept] = 1

        # Ensure consistent name formatting
        transformed_record["name"] = record["name"].title()

        transformed_data.append(transformed_record)

    end_time = time.time()
    duration = round(end_time - start_time, 2)
    logger.info(f"[TRANSFORM] ✅ Successfully transformed {len(transformed_data)} records in {duration} seconds")
    logger.info(f"[TRANSFORM] 📊 Department distribution: {departments_count}")

    return transformed_data


def load_data(transformed_data):
    """
    Load phase: Insert the data into the database

    Args:
        transformed_data: List of transformed data dictionaries
    """
    start_time = time.time()
    logger.info(f"[LOAD] ⏳ Starting database load of {len(transformed_data)} records")

    conn = create_connection()
    if conn is None:
        logger.error("[LOAD] ❌ Error: Could not establish database connection.")
        return False

    try:
        # Create tables if they don't exist
        create_tables(conn)

        # Get current record count
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees")
        previous_count = cursor.fetchone()[0]
        logger.info(f"[LOAD] 🗄️ Current record count before clearing: {previous_count}")

        # Clear existing data
        clear_table("employees")
        logger.info("[LOAD] 🧹 Cleared existing records from employees table")

        # Insert new data
        insert_start = time.time()
        for record in transformed_data:
            cursor.execute('''
                INSERT INTO employees (
                    id, name, department, position, email, phone,
                    address, hire_date, date_of_birth, ssn, username
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record["id"],
                record["name"],
                record["department"],
                record["position"],
                record["email"],
                record["phone"],
                record["address"],
                record["hire_date"],
                record["date_of_birth"],
                record["ssn"],
                record["username"]
            ))

        conn.commit()
        insert_end = time.time()
        insert_duration = round(insert_end - insert_start, 2)

        # Verify record count after insert
        cursor.execute("SELECT COUNT(*) FROM employees")
        new_count = cursor.fetchone()[0]

        end_time = time.time()
        total_duration = round(end_time - start_time, 2)
        logger.info(f"[LOAD] ✅ Successfully loaded {len(transformed_data)} records in {total_duration} seconds")
        logger.info(f"[LOAD] ⚡ Insert operation took {insert_duration} seconds")
        logger.info(f"[LOAD] 🗄️ New record count: {new_count}")

        return True
    except sqlite3.Error as e:
        logger.error(f"[LOAD] ❌ Database error: {e}")
        return False
    finally:
        conn.close()
        logger.info("[LOAD] 🔌 Database connection closed")


def run_etl_job():
    """Run the complete ETL process"""
    job_id = datetime.now().strftime("%Y%m%d%H%M%S")
    start_time = time.time()
    logger.info(f"[ETL-{job_id}] 🚀 Starting ETL job at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Generate random number of records between 10 and 100
        num_records = random.randint(10, 100)
        logger.info(f"[ETL-{job_id}] 🎲 Randomly selected to generate {num_records} records")

        # Extract data from Faker
        raw_data = extract_data(num_records)

        # Transform the data
        transformed_data = transform_data(raw_data)

        # Load data into the database
        success = load_data(transformed_data)

        end_time = time.time()
        duration = round(end_time - start_time, 2)

        if success:
            logger.info(f"[ETL-{job_id}] ✅ ETL job completed successfully in {duration} seconds")
        else:
            logger.warning(f"[ETL-{job_id}] ⚠️ ETL job completed with issues after {duration} seconds")
    except Exception as e:
        logger.error(f"[ETL-{job_id}] ❌ Error in ETL job: {e}", exc_info=True)


def schedule_etl_jobs():
    """Schedule ETL jobs to run every 5 minutes"""
    logger.info("🕒 Scheduling ETL jobs to run every 5 minutes")

    # Run immediately on startup
    logger.info("▶️ Running initial ETL job on startup")
    run_etl_job()

    # Schedule to run every 5 minutes (changed from 10)
    schedule.every(5).minutes.do(run_etl_job)
    logger.info("📅 ETL job scheduled to run every 5 minutes")

    # Keep the script running
    logger.info("⏱️ Scheduler is now running...")
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    logger.info("🔄 ETL service starting up")
    schedule_etl_jobs()