#!/bin/bash

# Real-Time Streaming Data Pipeline - Startup Script

set -e

echo "=========================================="
echo "Real-Time Streaming Data Pipeline"
echo "Apache Kafka + Spark Streaming"
echo "=========================================="
echo ""

# Check if Docker is running
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not in PATH"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "ERROR: Docker daemon is not running"
    exit 1
fi

# Check for .env file
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ .env file created. Update it with your values if needed."
fi

echo ""
echo "Step 1: Building and starting Docker containers..."
echo "This may take a few minutes on first run..."
echo ""

docker-compose up -d --build

echo ""
echo "Step 2: Waiting for services to become healthy..."
echo ""

# Function to check service health
check_health() {
    local service=$1
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose ps $service | grep -q "healthy\|running"; then
            echo "✓ $service is healthy"
            return 0
        fi
        
        echo "⋯ Waiting for $service... ($((attempt+1))/$max_attempts)"
        sleep 2
        attempt=$((attempt+1))
    done
    
    echo "✗ $service failed to become healthy"
    return 1
}

check_health "zookeeper"
check_health "kafka"
check_health "db"

echo ""
echo "Step 3: Pipeline is ready!"
echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. In another terminal, start the data producer:"
echo "   python scripts/producer.py"
echo ""
echo "   Or with Docker:"
echo "   docker-compose exec spark-app python /app/..//..//scripts/producer.py"
echo ""
echo "2. Monitor the Spark application:"
echo "   docker-compose logs -f spark-app"
echo ""
echo "3. Check results in PostgreSQL:"
echo "   docker exec -it db psql -U user -d stream_data"
echo "   SELECT * FROM page_view_counts LIMIT 10;"
echo ""
echo "4. View Parquet files in the data lake:"
echo "   find ./data/lake -name '*.parquet'"
echo ""
echo "5. Monitor enriched events in Kafka:"
echo "   docker exec kafka /usr/bin/kafka-console-consumer \\
     --bootstrap-server localhost:9092 \\
     --topic enriched_activity"
echo ""
echo "To stop the pipeline:"
echo "   docker-compose down"
echo ""
echo "For more information, see README.md"
echo "=========================================="
