import psycopg2
from psycopg2.extensions import connection
from typing import Optional, List, Union


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

    def setup_database(self) -> None:
        """Initialize database with schema and seed data"""
        try:
            # Execute schema first
            self._execute_sql_file("db/schema.sql")
            # Then seeds
            self._execute_sql_file("db/seeds.sql")
            print("Database setup completed successfully")
        except Exception as e:
            print(f"Error setting up database: {e}")
            raise

    def insert_returning_id(self, query: str, params: tuple) -> int:
        """Execute INSERT query and return the ID"""
        result = self._execute(query, params, fetch="one")
        return result[0] if result else None

    def select_all(self, query: str, params: tuple = None) -> List[tuple]:
        """Execute SELECT query and return all results"""
        return self._execute(query, params, fetch="all") or []

    def execute_write(self, query: str, params: tuple = None) -> None:
        """Execute write operation (INSERT/UPDATE/DELETE)"""
        self._execute(query, params, fetch=None)
    
    def _execute_sql_file(self, file_path: str) -> None:
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

    def _execute(
        self, query: str, params: tuple = None, fetch: str = "all"
    ) -> Union[List[tuple], tuple, None]:
        """Execute a query and return results based on fetch mode."""
        try:
            self.connect()
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                if cursor.description:  # If it's a SELECT query
                    if fetch == "all":
                        return cursor.fetchall()
                    elif fetch == "one":
                        return cursor.fetchone()
                self.conn.commit()
                return None
        except Exception as e:
            self.conn.rollback()
            raise e
