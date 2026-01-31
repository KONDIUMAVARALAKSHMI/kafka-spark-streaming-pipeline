"""
Database utility functions for the Spark Streaming application.
"""

import logging
from typing import Optional
import psycopg2
from psycopg2.extras import execute_batch

logger = logging.getLogger(__name__)


class PostgreSQLConnector:
    """Handles PostgreSQL connections and operations."""

    def __init__(self, db_url: str, db_user: str, db_password: str):
        """
        Initialize PostgreSQL connector.

        Args:
            db_url: JDBC connection URL
            db_user: Database user
            db_password: Database password
        """
        # Parse JDBC URL
        # Format: jdbc:postgresql://host:port/database
        self.db_url = db_url
        self.db_user = db_user
        self.db_password = db_password
        self.connection = None

    def connect(self) -> Optional[object]:
        """
        Establish connection to PostgreSQL.

        Returns:
            Connection object or None if failed
        """
        try:
            # Parse the JDBC URL to extract PostgreSQL parameters
            url_parts = self.db_url.replace('jdbc:postgresql://', '').split('/')
            host_port = url_parts[0]
            database = url_parts[1] if len(url_parts) > 1 else 'stream_data'

            host, port = host_port.split(':') if ':' in host_port else (host_port, '5432')

            self.connection = psycopg2.connect(
                host=host,
                port=int(port),
                database=database,
                user=self.db_user,
                password=self.db_password
            )
            logger.info(f"Connected to PostgreSQL: {host}:{port}/{database}")
            return self.connection

        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            return None

    def close(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            logger.info("PostgreSQL connection closed")

    def execute_upsert(self, table: str, columns: list, values: list, pk_columns: list) -> bool:
        """
        Execute an upsert (INSERT ... ON CONFLICT DO UPDATE) operation.

        Args:
            table: Table name
            columns: List of column names
            values: List of tuples containing row data
            pk_columns: List of column names that form the Primary Key
        
        Returns:
            True if successful, False otherwise
        """
        if not self.connection:
            logger.error("No database connection")
            return False

        if not values:
            return True

        try:
            cursor = self.connection.cursor()

            # Build the upsert query
            columns_str = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(columns))
            
            # Identify columns that are NOT in the primary key (these are the ones to update)
            update_columns = [col for col in columns if col not in pk_columns]
            
            if update_columns:
                update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_columns])
                pk_str = ', '.join(pk_columns)
                
                query = f"""
                INSERT INTO {table} ({columns_str})
                VALUES ({placeholders})
                ON CONFLICT ({pk_str}) DO UPDATE SET {update_set}
                """
            else:
                # If all columns are PK, just do nothing on conflict
                pk_str = ', '.join(pk_columns)
                query = f"""
                INSERT INTO {table} ({columns_str})
                VALUES ({placeholders})
                ON CONFLICT ({pk_str}) DO NOTHING
                """

            execute_batch(cursor, query, values, page_size=100)
            self.connection.commit()
            logger.info(f"Upserted {len(values)} records into {table}")
            cursor.close()
            return True

        except Exception as e:
            logger.error(f"Upsert error: {e}")
            if self.connection:
                self.connection.rollback()
            return False
