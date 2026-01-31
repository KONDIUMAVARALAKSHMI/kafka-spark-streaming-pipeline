#!/usr/bin/env python
"""
Data Producer for Kafka
Generates simulated user activity events and publishes them to the 'user_activity' topic.
"""

import json
import time
import random
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

try:
    from kafka import KafkaProducer
except ImportError:
    print("Error: kafka-python is not installed. Install it using: pip install kafka-python")
    exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataProducer:
    """Produces simulated user activity events to Kafka."""

    def __init__(self, bootstrap_servers: str = 'localhost:29092', topic: str = 'user_activity'):
        """
        Initialize the Kafka producer.

        Args:
            bootstrap_servers: Kafka bootstrap servers (default: localhost:29092)
            topic: Kafka topic name (default: user_activity)
        """
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            logger.info(f"Connected to Kafka at {bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise

    def generate_event(self, event_time: datetime = None, is_late: bool = False) -> Dict[str, Any]:
        """
        Generate a random user activity event.

        Args:
            event_time: Optional timestamp for the event (default: current time)
            is_late: If True, generate an event with old timestamp (for testing watermarking)

        Returns:
            Dictionary containing the event data
        """
        if event_time is None:
            if is_late:
                # Generate an event from 5 minutes ago (to test watermarking)
                event_time = datetime.utcnow() - timedelta(minutes=5)
            else:
                event_time = datetime.utcnow()

        pages = [
            'https://example.com/home',
            'https://example.com/products',
            'https://example.com/cart',
            'https://example.com/checkout',
            'https://example.com/about',
            'https://example.com/contact'
        ]

        event_types = ['page_view', 'click', 'session_start', 'session_end']
        user_ids = [f'user_{i}' for i in range(1, 21)]  # 20 different users

        event = {
            'event_time': event_time.isoformat() + 'Z',
            'user_id': random.choice(user_ids),
            'page_url': random.choice(pages),
            'event_type': random.choice(event_types)
        }

        return event

    def send_event(self, event: Dict[str, Any]) -> None:
        """
        Send an event to Kafka.

        Args:
            event: The event dictionary to send
        """
        try:
            future = self.producer.send(self.topic, value=event)
            record_metadata = future.get(timeout=10)
            logger.info(
                f"Event sent to topic '{record_metadata.topic}' "
                f"partition {record_metadata.partition} "
                f"at offset {record_metadata.offset}"
            )
        except Exception as e:
            logger.error(f"Failed to send event: {e}")

    def run(self, num_events: int = 100, interval: float = 0.5, 
            include_late_data: bool = True) -> None:
        """
        Continuously generate and send events.

        Args:
            num_events: Number of events to generate (0 for infinite)
            interval: Time interval between events in seconds
            include_late_data: Whether to occasionally send late-arriving data
        """
        try:
            count = 0
            while count < num_events or num_events == 0:
                # Occasionally send a late event (every 50 events) if enabled
                is_late = include_late_data and (count > 0 and count % 50 == 0)
                
                event = self.generate_event(is_late=is_late)
                self.send_event(event)
                
                if is_late:
                    logger.warning(f"Sent late-arriving event (simulating watermarking test)")
                
                count += 1
                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Producer interrupted by user")
        finally:
            self.producer.flush()
            self.producer.close()
            logger.info("Producer closed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Kafka Data Producer for User Activity Events'
    )
    parser.add_argument(
        '--bootstrap-servers',
        default='localhost:29092',
        help='Kafka bootstrap servers (default: localhost:29092)'
    )
    parser.add_argument(
        '--topic',
        default='user_activity',
        help='Kafka topic name (default: user_activity)'
    )
    parser.add_argument(
        '--num-events',
        type=int,
        default=0,
        help='Number of events to generate (0 for infinite, default: 0)'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=0.5,
        help='Time interval between events in seconds (default: 0.5)'
    )
    parser.add_argument(
        '--no-late-data',
        action='store_true',
        help='Disable sending late-arriving data for watermarking tests'
    )

    args = parser.parse_args()

    producer = DataProducer(
        bootstrap_servers=args.bootstrap_servers,
        topic=args.topic
    )

    logger.info(f"Starting to produce events to topic '{args.topic}'")
    logger.info(f"Bootstrap servers: {args.bootstrap_servers}")
    logger.info(f"Number of events: {'infinite' if args.num_events == 0 else args.num_events}")
    logger.info(f"Interval: {args.interval} seconds")

    producer.run(
        num_events=args.num_events,
        interval=args.interval,
        include_late_data=not args.no_late_data
    )


if __name__ == '__main__':
    main()
