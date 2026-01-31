
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import json
from datetime import datetime

# Add app directories to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../spark/app')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))

# Mock psycopg2 before importing db_utils if strictly needed, 
# but we can also rely on patch in the test method.
# We need to ensure db_utils can be imported even if psycopg2 is missing on host,
# but the file does 'import psycopg2'. 
# If it's missing, we need to mock it in sys.modules.

try:
    import psycopg2
except ImportError:
    sys.modules['psycopg2'] = MagicMock()
    sys.modules['psycopg2.extras'] = MagicMock()

from db_utils import PostgreSQLConnector

# Mock kafka for producer import
try:
    import kafka
except ImportError:
    sys.modules['kafka'] = MagicMock()

from producer import DataProducer

class TestDBUtils(unittest.TestCase):
    def test_upsert_logic_composite_key(self):
        """Verify that execute_upsert generates correct SQL for composite keys."""
        connector = PostgreSQLConnector("jdbc:postgresql://localhost:5432/db", "user", "pass")
        connector.connection = MagicMock()
        cursor = connector.connection.cursor.return_value
        
        # Test Data
        table = "page_view_counts"
        columns = ["window_start", "window_end", "page_url", "view_count"]
        values = [('2023-01-01', '2023-01-02', 'url1', 10)]
        pk_columns = ["window_start", "window_end", "page_url"]
        
        # Execute
        connector.execute_upsert(table, columns, values, pk_columns)
        
        # Verify
        # We check the arguments passed to execute_batch
        # args[0] is cursor, args[1] is query, args[2] is values
        call_args = sys.modules['psycopg2.extras'].execute_batch.call_args
        self.assertIsNotNone(call_args, "execute_batch should be called")
        
        query = call_args[0][1]
        print(f"\nGenererated SQL:\n{query}")
        
        self.assertIn("INSERT INTO page_view_counts", query)
        self.assertIn("ON CONFLICT (window_start, window_end, page_url)", query)
        self.assertIn("DO UPDATE SET view_count = EXCLUDED.view_count", query)

    def test_upsert_logic_single_key(self):
        """Verify that execute_upsert works for single PK."""
        connector = PostgreSQLConnector("jdbc:postgresql://localhost:5432/db", "user", "pass")
        connector.connection = MagicMock()
        
        # Test Data
        table = "user_sessions"
        columns = ["user_id", "duration"]
        values = [('u1', 100)]
        pk_columns = ["user_id"]
        
        connector.execute_upsert(table, columns, values, pk_columns)
        
        call_args = sys.modules['psycopg2.extras'].execute_batch.call_args
        query = call_args[0][1]
        
        self.assertIn("ON CONFLICT (user_id)", query)
        self.assertIn("DO UPDATE SET duration = EXCLUDED.duration", query)


class TestProducer(unittest.TestCase):
    def test_event_schema(self):
        """Verify generated events match the requirements."""
        # Mock kafka producer in init
        with patch('producer.KafkaProducer') as mock_kafka:
            producer = DataProducer()
            event = producer.generate_event()
            
            print(f"\nGenerated Event: {json.dumps(event, indent=2)}")
            
            self.assertIn('event_time', event)
            self.assertIn('user_id', event)
            self.assertIn('page_url', event)
            self.assertIn('event_type', event)
            
            # Verify event_time format (ISO 8601)
            # It should end with 'Z' as per code
            self.assertTrue(event['event_time'].endswith('Z'))

if __name__ == '__main__':
    unittest.main()
