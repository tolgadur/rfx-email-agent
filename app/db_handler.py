import os
import psycopg2
from psycopg2.extensions import connection
from typing import Optional


class DatabaseHandler:
    def __init__(self):
        self.conn: Optional[connection] = None
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable is not set")

    def connect(self) -> None:
        """Establish database connection"""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(self.db_url)

    def close(self) -> None:
        """Close database connection"""
        if self.conn and not self.conn.closed:
            self.conn.close()

    def execute_sql_file(self, file_path: str) -> None:
        """Execute SQL commands from a file"""
        try:
            self.connect()
            with open(file_path, "r") as file:
                sql = file.read()
                with self.conn.cursor() as cursor:
                    cursor.execute(sql)
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def setup_database(self) -> None:
        """Initialize database with schema and seed data"""
        try:
            # Execute schema first
            self.execute_sql_file("db/schema.sql")
            # Then seeds
            self.execute_sql_file("db/seeds.sql")
            print("Database setup completed successfully")
        except Exception as e:
            print(f"Error setting up database: {e}")
            raise
