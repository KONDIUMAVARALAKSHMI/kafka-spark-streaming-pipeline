FROM python:3.9-bullseye

# Install Java and system tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-11-jre-headless \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Environment Variables
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV SPARK_VERSION=3.3.2
ENV SPARK_HOME=/opt/spark
ENV PATH=$SPARK_HOME/bin:$PATH
ENV SPARK_LOCAL_IP=0.0.0.0
ENV SPARK_DRIVER_BINDADDRESS=0.0.0.0

# Create directories
WORKDIR /app
RUN mkdir -p /opt/spark/jars

# Copy and extract Spark (Expects the tarball to be in the build context)
COPY spark-3.3.2-bin-hadoop3.tgz /tmp/spark.tgz
RUN tar -xzf /tmp/spark.tgz -C /opt/ && \
    rm -rf /opt/spark && \
    mv /opt/spark-3.3.2-bin-hadoop3 /opt/spark && \
    rm /tmp/spark.tgz

# Copy Postgres and Kafka Drivers
COPY postgresql-42.5.1.jar /opt/spark/jars/
COPY spark-sql-kafka-0-10_2.12-3.3.2.jar /opt/spark/jars/
COPY spark-token-provider-kafka-0-10_2.12-3.3.2.jar /opt/spark/jars/
COPY kafka-clients-2.8.1.jar /opt/spark/jars/
COPY commons-pool2-2.11.1.jar /opt/spark/jars/

# Set PYTHONPATH to include Spark's Python lib
ENV PYTHONPATH=$SPARK_HOME/python:$SPARK_HOME/python/lib/py4j-0.10.9.5-src.zip:$PYTHONPATH

# Install Python dependencies
RUN pip install --no-cache-dir \
    pyspark==3.3.2 \
    kafka-python==2.0.2 \
    psycopg2-binary==2.9.7 \
    python-dotenv==1.0.0 \
    pyarrow==13.0.0

# Copy application
COPY ./app /app

# Default command
CMD ["python", "/app/spark_streaming_app.py"]
