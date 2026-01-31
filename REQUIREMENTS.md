# Requirements for Real-Time Streaming Data Pipeline

## System Requirements

- **OS**: Linux, macOS, or Windows with WSL2
- **Docker**: 20.10.0+
- **Docker Compose**: 1.29.0+
- **Python**: 3.8+ (for running producer and verification scripts)
- **RAM**: At least 4GB available for Docker containers
- **Disk Space**: At least 2GB for Docker images and data

## Docker Images

The following images are automatically downloaded and used:

```
confluentinc/cp-zookeeper:7.3.0
confluentinc/cp-kafka:7.3.0
postgres:14-alpine
python:3.9-slim (base for spark-app)
```

## Python Dependencies

### For Data Producer (scripts/producer.py)

```
kafka-python==2.0.2
python-dotenv==1.0.0
```

### For Verification Script (scripts/verify.py)

```
kafka-python==2.0.2
psycopg2-binary==2.9.7
```

### Install all Python dependencies:

```bash
pip install -r scripts/requirements.txt
```

## Software Stack

### Data Ingestion & Streaming

- **Apache Kafka 7.3.0**: Distributed event streaming platform
- **Zookeeper**: Kafka coordination service

### Stream Processing

- **Apache Spark 3.3.2**: Stream processing engine
- **PySpark**: Python API for Spark
- **Structured Streaming**: Modern Spark streaming API

### Data Storage

- **PostgreSQL 14**: Relational database for aggregations
- **Parquet**: Columnar storage format for data lake

### Supporting Libraries

- **psycopg2-binary**: PostgreSQL Python driver
- **kafka-python**: Python Kafka client
- **pyarrow**: Parquet file support
- **python-dotenv**: Environment variable management

## Ports Used

| Service    | Port  | Purpose                       |
| ---------- | ----- | ----------------------------- |
| Zookeeper  | 2181  | Kafka coordination            |
| Kafka      | 9092  | Internal broker communication |
| Kafka      | 29092 | External/localhost access     |
| PostgreSQL | 5432  | Database access               |
| Spark UI   | 4040  | (Optional) Spark monitoring   |

## Network Requirements

- All containers communicate on the same Docker network
- Localhost access required for testing and verification
- Ports 2181, 9092, 29092, 5432 should not be in use

## Optional Tools (for testing/monitoring)

For better debugging and testing experience:

```bash
# Install Kafka command-line tools (optional)
# Kafka tools are already available in the kafka container

# For reading Parquet files locally (optional)
pip install pandas pyarrow

# For database exploration (optional)
pip install psycopg2  # PostgreSQL client
```

## Network Bandwidth

For typical usage:

- With 1 event/second: ~1 KB/s per producer
- With default producer settings: ~0.5 KB/s
- Database writes: Minimal bandwidth required

## Disk Space Breakdown

- Docker images: ~2GB (one-time download)
- PostgreSQL data: ~10MB-100MB (depending on retention)
- Data lake (Parquet): Depends on event volume
  - 1 hour at 1 event/sec: ~100KB
  - 1 day at 1 event/sec: ~2.4MB

## Installation Steps

### 1. Install Docker and Docker Compose

**macOS/Linux**:

```bash
# Install Docker Desktop which includes Docker Compose
# https://www.docker.com/products/docker-desktop
```

**Windows**:

```powershell
# Use Docker Desktop for Windows (includes Docker Compose)
# https://www.docker.com/products/docker-desktop
# Or use WSL2 with Docker Engine
```

### 2. Verify Installation

```bash
docker --version
docker-compose --version
python --version
```

### 3. Install Python Dependencies

```bash
pip install kafka-python==2.0.2 \
            python-dotenv==1.0.0 \
            psycopg2-binary==2.9.7 \
            pyarrow==13.0.0
```

### 4. Clone Repository and Setup

```bash
git clone <repository-url>
cd pipeline
cp .env.example .env
docker-compose up -d --build
```

## Troubleshooting Installation

### Docker not found

```bash
# Ensure Docker is in PATH
echo $PATH | grep -i docker
```

### Port already in use

```bash
# Find what's using the port
lsof -i :2181  # For Zookeeper
lsof -i :9092  # For Kafka
lsof -i :5432  # For PostgreSQL

# Or stop the conflicting service and restart
docker-compose down
docker-compose up
```

### Python package installation fails

```bash
# Upgrade pip
pip install --upgrade pip

# Install packages with verbose output
pip install -v kafka-python==2.0.2
```

### Docker memory issues

- Increase Docker Desktop memory allocation
- Or reduce Spark parallelism in the application

## Verification

Run the verification script to ensure all requirements are met:

```bash
python scripts/verify.py
```

Expected output:

- Kafka connection: OK
- PostgreSQL connection: OK
- Docker services: Running
- All tests: Passed

---

**Last Updated**: January 2026
