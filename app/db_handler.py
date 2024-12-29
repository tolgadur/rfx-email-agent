import psycopg2
from psycopg2.extensions import connection
from typing import Optional


class DatabaseHandler:
    def __init__(self, database_url: str):
        """Initialize database handler with connection URL.

        Args:
            database_url: Database URL in format:
                postgresql://user:password@host:port/database
        """
        self.conn: Optional[connection] = None
        self.database_url = database_url

    def connect(self) -> None:
        """Establish database connection"""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(self.database_url)

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
