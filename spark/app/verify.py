#!/usr/bin/env python
"""
Verification Script for the Real-Time Streaming Data Pipeline
Tests that all components are working correctly.
"""

import os
import time
import json
import argparse
import logging
from typing import Tuple, Dict, Any
import subprocess
import sys

try:
    from kafka import KafkaProducer, KafkaConsumer
    import psycopg2
except ImportError as e:
    print(f"ERROR: Missing required package: {e}")
    print("Install with: pip install kafka-python psycopg2-binary")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PipelineVerifier:
    """Verify all components of the streaming pipeline."""

    def __init__(self, kafka_servers: str = 'localhost:29092',
                 db_user: str = 'user', db_password: str = 'password',
                 db_name: str = 'stream_data', db_host: str = 'localhost'):
        self.kafka_servers = kafka_servers
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name
        self.db_host = db_host
        self.passed = 0
        self.failed = 0

    def test_kafka_connection(self) -> bool:
        """Test connection to Kafka."""
        logger.info("Testing Kafka connection...")
        try:
            producer = KafkaProducer(
                bootstrap_servers=self.kafka_servers,
                request_timeout_ms=5000
            )
            producer.close()
            logger.info("✓ Kafka connection successful")
            self.passed += 1
            return True
        except Exception as e:
            logger.error(f"✗ Kafka connection failed: {e}")
            self.failed += 1
            return False

    def test_kafka_topic_exists(self, topic: str = 'user_activity') -> bool:
        """Test if the required topic exists."""
        logger.info(f"Testing Kafka topic '{topic}'...")
        try:
            consumer = KafkaConsumer(
                bootstrap_servers=self.kafka_servers,
                request_timeout_ms=5000
            )
            topics = consumer.topics()
            consumer.close()

            if topic in topics:
                logger.info(f"✓ Topic '{topic}' exists")
                self.passed += 1
                return True
            else:
                logger.error(f"✗ Topic '{topic}' does not exist")
                logger.info(f"Available topics: {topics}")
                self.failed += 1
                return False
        except Exception as e:
            logger.error(f"✗ Failed to check Kafka topics: {e}")
            self.failed += 1
            return False

    def test_database_connection(self) -> bool:
        """Test connection to PostgreSQL database."""
        logger.info("Testing PostgreSQL connection...")
        try:
            conn = psycopg2.connect(
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                connect_timeout=5
            )
            conn.close()
            logger.info("✓ PostgreSQL connection successful")
            self.passed += 1
            return True
        except Exception as e:
            logger.error(f"✗ PostgreSQL connection failed: {e}")
            self.failed += 1
            return False

    def test_database_tables(self) -> bool:
        """Test if required tables exist."""
        logger.info("Testing database tables...")
        required_tables = ['page_view_counts', 'active_users', 'user_sessions']
        
        try:
            conn = psycopg2.connect(
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            cursor = conn.cursor()

            all_exist = True
            for table in required_tables:
                cursor.execute(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                    "WHERE table_name = %s);",
                    (table,)
                )
                exists = cursor.fetchone()[0]

                if exists:
                    logger.info(f"  ✓ Table '{table}' exists")
                else:
                    logger.error(f"  ✗ Table '{table}' does not exist")
                    all_exist = False

            cursor.close()
            conn.close()

            if all_exist:
                self.passed += 1
                return True
            else:
                self.failed += 1
                return False

        except Exception as e:
            logger.error(f"✗ Failed to check database tables: {e}")
            self.failed += 1
            return False

    def test_event_producer(self, num_events: int = 5) -> bool:
        """Test sending events to Kafka."""
        logger.info(f"Testing event producer ({num_events} events)...")
        try:
            producer = KafkaProducer(
                bootstrap_servers=self.kafka_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                request_timeout_ms=5000
            )

            for i in range(num_events):
                event = {
                    'event_time': '2024-01-28T12:00:00Z',
                    'user_id': f'test_user_{i}',
                    'page_url': 'https://example.com/test',
                    'event_type': 'page_view'
                }
                future = producer.send('user_activity', event)
                record_metadata = future.get(timeout=5)

            producer.close()
            logger.info(f"✓ Successfully sent {num_events} events to Kafka")
            self.passed += 1
            return True

        except Exception as e:
            logger.error(f"✗ Failed to produce events: {e}")
            self.failed += 1
            return False

    def test_data_lake_directory(self, lake_path: str = './data/lake') -> bool:
        """Test if data lake directory exists and is writable."""
        logger.info(f"Testing data lake directory at {lake_path}...")
        try:
            if os.path.exists(lake_path):
                if os.access(lake_path, os.W_OK):
                    logger.info(f"✓ Data lake directory exists and is writable: {lake_path}")
                    self.passed += 1
                    return True
                else:
                    logger.error(f"✗ Data lake directory is not writable: {lake_path}")
                    self.failed += 1
                    return False
            else:
                logger.error(f"✗ Data lake directory does not exist: {lake_path}")
                self.failed += 1
                return False

        except Exception as e:
            logger.error(f"✗ Failed to check data lake directory: {e}")
            self.failed += 1
            return False

    def test_docker_services(self) -> bool:
        """Test that all Docker services are running."""
        logger.info("Testing Docker services...")
        required_services = ['zookeeper', 'kafka', 'db', 'spark-app']

        try:
            result = subprocess.run(
                ['docker-compose', 'ps', '--format=json'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                logger.error("✗ docker-compose command failed")
                self.failed += 1
                return False

            # Parse output (simple check)
            output = result.stdout
            all_running = all(service in output for service in required_services)

            if all_running:
                logger.info("✓ All required Docker services are running")
                self.passed += 1
                return True
            else:
                logger.error("✗ Some Docker services are not running")
                logger.info(output)
                self.failed += 1
                return False

        except FileNotFoundError:
            logger.warning("⚠ docker-compose not found, skipping Docker service check")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to check Docker services: {e}")
            self.failed += 1
            return False

    def run_all_tests(self, data_lake_path: str = './data/lake') -> bool:
        """Run all verification tests."""
        logger.info("=" * 60)
        logger.info("Real-Time Streaming Pipeline Verification")
        logger.info("=" * 60)
        logger.info("")

        # Run tests
        self.test_docker_services()
        time.sleep(1)
        
        self.test_kafka_connection()
        self.test_kafka_topic_exists()
        
        self.test_database_connection()
        self.test_database_tables()
        
        self.test_data_lake_directory(data_lake_path)
        
        self.test_event_producer()

        # Summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("Test Summary")
        logger.info("=" * 60)
        logger.info(f"Passed: {self.passed}")
        logger.info(f"Failed: {self.failed}")
        logger.info("=" * 60)
        logger.info("")

        if self.failed == 0:
            logger.info("✓ All tests passed! Pipeline is ready to use.")
            return True
        else:
            logger.warning(f"✗ {self.failed} test(s) failed. Check logs above.")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Verify Real-Time Streaming Data Pipeline'
    )
    parser.add_argument(
        '--kafka-servers',
        default='localhost:29092',
        help='Kafka bootstrap servers (default: localhost:29092)'
    )
    parser.add_argument(
        '--db-host',
        default='localhost',
        help='Database host (default: localhost)'
    )
    parser.add_argument(
        '--db-user',
        default='user',
        help='Database user (default: user)'
    )
    parser.add_argument(
        '--db-password',
        default='password',
        help='Database password (default: password)'
    )
    parser.add_argument(
        '--db-name',
        default='stream_data',
        help='Database name (default: stream_data)'
    )

    parser.add_argument(
        '--data-lake-path',
        default='./data/lake',
        help='Path to the data lake directory (default: ./data/lake)'
    )

    args = parser.parse_args()

    verifier = PipelineVerifier(
        kafka_servers=args.kafka_servers,
        db_user=args.db_user,
        db_password=args.db_password,
        db_name=args.db_name,
        db_host=args.db_host
    )

    success = verifier.run_all_tests(data_lake_path=args.data_lake_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
