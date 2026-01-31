"""
My Spark Streaming Application - User Activity Project
-------------------------------------------------------
This is the main logic for my pipeline. It reads data from Kafka, 
does some transformations (like windowing), and sends the results
to PostgreSQL and my data lake.
"""

import os
import json
import logging
from typing import Optional
from datetime import datetime

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    from_json, col, to_timestamp, window, count, approx_count_distinct,
    to_json, struct, lit, current_timestamp, when, min as spark_min,
    max as spark_max, unix_timestamp
)
from pyspark.sql.types import (
    StructType, StructField, StringType, TimestampType
)
try:
    from pyspark.sql.functions import session_window
except ImportError:
    # Fallback or manual definition if older pyspark, but 3.3.2 has it.
    pass

from db_utils import PostgreSQLConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SparkStreamingPipeline:
    # This class wraps all my Spark logic together.

    def __init__(self):
        # Setting up the basics: Spark session, Kafka, and DB credentials.
        self.spark = self._create_spark_session()
        self.kafka_bootstrap_servers = os.getenv(
            'KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'
        )
        self.db_url = os.getenv('DB_URL', 'jdbc:postgresql://db:5432/stream_data')
        self.db_user = os.getenv('DB_USER', 'user')
        self.db_password = os.getenv('DB_PASSWORD', 'password')
        self.data_lake_path = '/opt/spark/data/lake'

    def _create_spark_session(self) -> SparkSession:
        # Here I build the Spark Session. I added some JVM flags 
        # to fix some errors I was seeing with Java 11/17.
        jvm_flags = (
            "--add-opens=java.base/java.lang=ALL-UNNAMED "
            "--add-opens=java.base/java.lang.invoke=ALL-UNNAMED "
            "--add-opens=java.base/java.lang.reflect=ALL-UNNAMED "
            "--add-opens=java.base/java.io=ALL-UNNAMED "
            "--add-opens=java.base/java.net=ALL-UNNAMED "
            "--add-opens=java.base/java.nio=ALL-UNNAMED "
            "--add-opens=java.base/java.util=ALL-UNNAMED "
            "--add-opens=java.base/java.util.concurrent=ALL-UNNAMED "
            "--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED "
            "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED "
            "--add-opens=java.base/sun.nio.cs=ALL-UNNAMED "
            "--add-opens=java.base/sun.security.action=ALL-UNNAMED "
            "--add-opens=java.base/sun.util.calendar=ALL-UNNAMED "
            "--add-opens=java.security.jgss/sun.security.krb5=ALL-UNNAMED"
        )

        return SparkSession.builder \
            .appName('StreamingDataPipeline') \
            .config('spark.sql.streaming.schemaInference', 'true') \
            .config('spark.sql.shuffle.partitions', '4') \
            .config('spark.default.parallelism', '4') \
            .config('spark.sql.streaming.checkpointLocation', '/tmp/spark-checkpoint') \
            .config('spark.driver.extraJavaOptions', jvm_flags) \
            .config('spark.executor.extraJavaOptions', jvm_flags) \
            .getOrCreate()
        # Note: I set shuffle.partitions to 4 because I'm running this on a single machine (Docker),
        # so I don't need a high number of partitions.

    def _get_event_schema(self) -> StructType:
        # Defining the JSON schema manually so Spark knows 
        # what to expect from the Kafka events.
        return StructType([
            StructField('event_time', StringType(), True),
            StructField('user_id', StringType(), True),
            StructField('page_url', StringType(), True),
            StructField('event_type', StringType(), True)
        ])

    def read_from_kafka(self) -> DataFrame:
        """
        Read streaming data from Kafka user_activity topic.

        Returns:
            DataFrame with raw Kafka data
        """
        logger.info(f"Connecting to Kafka at {self.kafka_bootstrap_servers}")

        df = self.spark \
            .readStream \
            .format('kafka') \
            .option('kafka.bootstrap.servers', self.kafka_bootstrap_servers) \
            .option('subscribe', 'user_activity') \
            .option('startingOffsets', 'latest') \
            .load()
        # We use readStream because this is a real-time data flow.

        return df

    def parse_events(self, df: DataFrame) -> DataFrame:
        """
        Parse JSON events and apply schema transformation.

        Args:
            df: Raw DataFrame from Kafka

        Returns:
            DataFrame with parsed and typed columns
        """
        schema = self._get_event_schema()

        parsed_df = df.select(
            from_json(col('value').cast('string'), schema).alias('data')
        ).select('data.*')

        # Convert event_time string to timestamp
        parsed_df = parsed_df.withColumn(
            'event_time',
            to_timestamp(col('event_time'), "yyyy-MM-dd'T'HH:mm:ss'Z'")
        )

        logger.info("Events parsed and schema applied")
        return parsed_df

    def write_to_data_lake(self, df: DataFrame) -> None:
        """
        Write all transformed events to data lake in Parquet format.

        Args:
            df: DataFrame to write
        """
        logger.info(f"Configuring data lake sink at {self.data_lake_path}")

        query = df \
            .select(
                col('event_time'),
                col('user_id'),
                col('page_url'),
                col('event_type'),
                col('event_date')
            ) \
            .writeStream \
            .format('parquet') \
            .option('path', self.data_lake_path) \
            .option('checkpointLocation', '/tmp/checkpoint-data-lake') \
            .partitionBy('event_date') \
            .option('mergeSchema', 'true') \
            .start()

        logger.info("Data lake sink started")
        return query

    def add_processing_time(self, df: DataFrame) -> DataFrame:
        """
        Add processing_time field to enrich events.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with added processing_time field
        """
        return df.withColumn(
            'processing_time',
            current_timestamp()
        )

    def write_to_enriched_kafka(self, df: DataFrame) -> None:
        """
        Write enriched events to enriched_activity Kafka topic.

        Args:
            df: DataFrame to write
        """
        enriched_df = self.add_processing_time(df)

        enriched_json = enriched_df.select(
            to_json(
                struct(
                    col('event_time'),
                    col('user_id'),
                    col('page_url'),
                    col('event_type'),
                    col('processing_time')
                )
            ).alias('value')
        )

        query = enriched_json \
            .writeStream \
            .format('kafka') \
            .option('kafka.bootstrap.servers', self.kafka_bootstrap_servers) \
            .option('topic', 'enriched_activity') \
            .option('checkpointLocation', '/tmp/checkpoint-enriched-kafka') \
            .start()

        logger.info("Enriched Kafka sink started")
        return query

    def write_page_view_counts(self, df: DataFrame) -> None:
        # Requirement: Calculate page views in 1-minute tumbling windows.
        # This only looks at 'page_view' event types.
        page_views = df.filter(col('event_type') == 'page_view') \
            .withWatermark('event_time', '2 minutes') \
            .groupBy(
                window(col('event_time'), '1 minute').alias('window'),
                col('page_url')
            ) \
            .agg(count('*').alias('view_count'))

        # Format output for database
        page_view_output = page_views.select(
            col('window.start').cast('timestamp').alias('window_start'),
            col('window.end').cast('timestamp').alias('window_end'),
            col('page_url'),
            col('view_count')
        )

        def write_page_views(batch_df, batch_id):
            """Write batch to PostgreSQL with upsert logic."""
            if batch_df.count() == 0:
                return
            
            # Collect data to driver (safe for aggregated counts)
            # For larger datasets, use mapPartitions
            rows = batch_df.collect()
            data = []
            for row in rows:
                data.append((
                    row['window_start'],
                    row['window_end'],
                    row['page_url'],
                    row['view_count']
                ))
            
            connector = PostgreSQLConnector(self.db_url, self.db_user, self.db_password)
            if connector.connect():
                connector.execute_upsert(
                    'page_view_counts',
                    ['window_start', 'window_end', 'page_url', 'view_count'],
                    data,
                    pk_columns=['window_start', 'window_end', 'page_url']
                )
                connector.close()

        query = page_view_output \
            .writeStream \
            .foreachBatch(write_page_views) \
            .option('checkpointLocation', '/tmp/checkpoint-page-views') \
            .outputMode('update') \
            .start()

        logger.info("Page view counts sink started")
        return query

    def write_active_user_counts(self, df: DataFrame) -> None:
        # Requirement: Count distinct active users in a 5-minute window that slides every 1 minute.
        # I used approx_count_distinct for better performance on streams.
        active_users = df \
            .withWatermark('event_time', '2 minutes') \
            .groupBy(
                window(col('event_time'), '5 minutes', '1 minute').alias('window')
            ) \
            .agg(approx_count_distinct('user_id').alias('active_user_count'))

        # Format output for database
        active_user_output = active_users.select(
            col('window.start').cast('timestamp').alias('window_start'),
            col('window.end').cast('timestamp').alias('window_end'),
            col('active_user_count')
        )

        def write_active_users(batch_df, batch_id):
            """Write batch to PostgreSQL with upsert logic."""
            if batch_df.count() == 0:
                return

            rows = batch_df.collect()
            data = []
            for row in rows:
                data.append((
                    row['window_start'],
                    row['window_end'],
                    row['active_user_count']
                ))

            connector = PostgreSQLConnector(self.db_url, self.db_user, self.db_password)
            if connector.connect():
                connector.execute_upsert(
                    'active_users',
                    ['window_start', 'window_end', 'active_user_count'],
                    data,
                    pk_columns=['window_start', 'window_end']
                )
                connector.close()

        query = active_user_output \
            .writeStream \
            .foreachBatch(write_active_users) \
            .option('checkpointLocation', '/tmp/checkpoint-active-users') \
            .outputMode('update') \
            .start()

        logger.info("Active user counts sink started")
        return query

    def write_user_sessions(self, df: DataFrame) -> None:
        # This tracks how long a user stays on the site.
        # It starts a timer on 'session_start' and ends it on 'session_end'.
        session_events = df.filter(
            (col('event_type') == 'session_start') | (col('event_type') == 'session_end')
        )

        # I'm using Spark 3.2's session_window here because it's much easier
        # to manage than manual state. It times out after 15 minutes of silence.
        from pyspark.sql.functions import session_window
        
        session_data = session_events \
            .withWatermark("event_time", "15 minutes") \
            .groupBy(
                session_window(col("event_time"), "15 minutes"),
                col("user_id")
            ) \
            .agg(
                spark_min(when(col('event_type') == 'session_start', col('event_time'))).alias('session_start'),
                spark_max(when(col('event_type') == 'session_end', col('event_time'))).alias('session_end')
            ) \
            .filter(col('session_start').isNotNull() & col('session_end').isNotNull()) \
            .select(
                col('user_id'),
                col('session_start').alias('session_start_time'),
                col('session_end').alias('session_end_time'),
                (unix_timestamp(col('session_end')) - unix_timestamp(col('session_start'))).alias('session_duration_seconds')
            )

        def write_sessions(batch_df, batch_id):
            """Write batch to PostgreSQL with upsert logic."""
            if batch_df.count() == 0:
                return

            rows = batch_df.collect()
            data = []
            for row in rows:
                data.append((
                    row['user_id'],
                    row['session_start_time'],
                    row['session_end_time'],
                    row['session_duration_seconds']
                ))

            connector = PostgreSQLConnector(self.db_url, self.db_user, self.db_password)
            if connector.connect():
                # Upsert based on user_id as per schema
                connector.execute_upsert(
                    'user_sessions',
                    ['user_id', 'session_start_time', 'session_end_time', 'session_duration_seconds'],
                    data,
                    pk_columns=['user_id']
                )
                connector.close()

        query = session_data \
            .writeStream \
            .foreachBatch(write_sessions) \
            .option('checkpointLocation', '/tmp/checkpoint-sessions') \
            .outputMode('append') \
            .start()

        logger.info("User sessions sink started")
        return query

    def run(self) -> None:
        """
        Run the complete streaming pipeline.
        """
        try:
            logger.info("Starting Spark Streaming Pipeline")

            # Read from Kafka
            raw_df = self.read_from_kafka()

            # Parse and transform events
            parsed_df = self.parse_events(raw_df)

            # Add event_date for partitioning
            parsed_df = parsed_df.withColumn(
                'event_date',
                col('event_time').cast('date')
            )

            # Start all sinks
            queries = []

            # Data lake sink
            queries.append(self.write_to_data_lake(parsed_df))

            # Enriched Kafka sink
            queries.append(self.write_to_enriched_kafka(parsed_df))

            # Page view counts (tumbling window)
            queries.append(self.write_page_view_counts(parsed_df))

            # Active user counts (sliding window)
            queries.append(self.write_active_user_counts(parsed_df))

            # User sessions (stateful)
            queries.append(self.write_user_sessions(parsed_df))

            logger.info("All streaming queries started successfully")

            # Wait for any query to terminate
            for query in queries:
                query.awaitTermination()

        except KeyboardInterrupt:
            logger.info("Pipeline interrupted by user")
        except Exception as e:
            logger.error(f"Error in pipeline: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            logger.info("Stopping Spark Session")
            if hasattr(self, 'spark'):
                self.spark.stop()


def main():
    """Main entry point."""
    try:
        pipeline = SparkStreamingPipeline()
        pipeline.run()
    except Exception:
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
