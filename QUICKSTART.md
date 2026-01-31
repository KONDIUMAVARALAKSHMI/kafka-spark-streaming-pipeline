# Quick Reference Guide

## 🚀 5-Minute Quickstart

### Setup (First Time Only)

```bash
# 1. Navigate to project directory
cd pipeline

# 2. Copy environment file
cp .env.example .env

# 3. Start all services
docker-compose up -d --build

# 4. Wait for services to be healthy
docker-compose ps  # Check all "healthy" or "Up"
```

### Run Pipeline (Every Time)

```bash
# Terminal 1: Start data producer
python scripts/producer.py

# Terminal 2: Monitor Spark logs
docker-compose logs -f spark-app

# Terminal 3: Check database results
docker exec -it db psql -U user -d stream_data
SELECT * FROM page_view_counts LIMIT 10;
```

### Stop Pipeline

```bash
# Stop all containers
docker-compose down

# Optional: Remove all data
docker-compose down -v  # Remove volumes too
```

---

## 📊 Database Queries

### Check Page View Counts (1-minute windows)

```sql
SELECT
    window_start,
    window_end,
    page_url,
    view_count
FROM page_view_counts
ORDER BY window_start DESC
LIMIT 10;
```

### Check Active Users (5-minute windows)

```sql
SELECT
    window_start,
    window_end,
    active_user_count
FROM active_users
ORDER BY window_start DESC
LIMIT 10;
```

### Check User Sessions

```sql
SELECT
    user_id,
    session_start_time,
    session_end_time,
    session_duration_seconds
FROM user_sessions
ORDER BY session_start_time DESC
LIMIT 10;
```

---

## 🔍 Monitoring Commands

### Kafka Topics

```bash
# List all topics
docker exec kafka /usr/bin/kafka-topics --bootstrap-server localhost:9092 --list

# Consume from user_activity
docker exec kafka /usr/bin/kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic user_activity --from-beginning --max-messages 5

# Consume from enriched_activity
docker exec kafka /usr/bin/kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic enriched_activity --from-beginning --max-messages 5
```

### Container Logs

```bash
# Spark application
docker-compose logs spark-app

# PostgreSQL
docker-compose logs db

# Kafka
docker-compose logs kafka

# All services
docker-compose logs -f

# Last 100 lines of Spark logs
docker-compose logs --tail=100 spark-app
```

### Data Lake Files

```bash
# List Parquet files
find ./data/lake -name "*.parquet" -type f

# List by date
ls -lah ./data/lake/

# Count files
find ./data/lake -name "*.parquet" -type f | wc -l
```

---

## 🧪 Testing Checklist

- [ ] Docker containers started: `docker-compose ps`
- [ ] All services healthy: All show "healthy" or "Up"
- [ ] Producer running: `python scripts/producer.py`
- [ ] Data in Kafka: Check with consumer command
- [ ] Database filled: Query page_view_counts
- [ ] Data lake populated: Check ./data/lake directory
- [ ] Parquet files created: `find ./data/lake -name "*.parquet"`
- [ ] Enriched topic: Monitor enriched_activity

---

## 🐛 Quick Troubleshooting

### Services won't start

```bash
docker-compose down
docker-compose up -d --build
docker-compose logs  # Check for errors
```

### No data in database

```bash
# Check if producer is running
ps aux | grep producer.py

# Check Kafka has data
docker exec kafka /usr/bin/kafka-console-consumer \
  --bootstrap-server localhost:9092 --topic user_activity --max-messages 1

# Check Spark logs
docker-compose logs spark-app | tail -50
```

### Port already in use

```bash
# Kill process using port (example: 9092)
lsof -ti:9092 | xargs kill -9

# Or use different Docker network
docker-compose down
docker system prune -a  # Clean up
docker-compose up -d --build
```

### Out of memory

```bash
# Increase Docker memory in settings
# Or reduce parallelism in spark_streaming_app.py:
.config('spark.sql.shuffle.partitions', '2')
```

---

## 🔧 Configuration Quick Reference

### Environment Variables (.env)

```
DB_USER=user                    # PostgreSQL username
DB_PASSWORD=password            # PostgreSQL password
DB_NAME=stream_data            # Database name
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
SPARK_MEMORY_EXECUTOR=1g       # Spark executor memory
SPARK_MEMORY_DRIVER=1g         # Spark driver memory
```

### Producer Options

```bash
# Slow rate (2s between events)
python scripts/producer.py --interval 2.0

# Fast rate (0.1s between events)
python scripts/producer.py --interval 0.1

# Finite events (100 total)
python scripts/producer.py --num-events 100

# Without late data simulation
python scripts/producer.py --no-late-data

# Custom Kafka server
python scripts/producer.py --bootstrap-servers <server:port>
```

---

## 📈 Expected Behavior

### Timeline (After starting producer)

**0-1 minute**:

- Events arriving in Kafka
- Spark buffering data
- No aggregations yet

**1-2 minutes**:

- First tumbling window completes
- page_view_counts table populated
- sliding_window aggregations start

**2-3 minutes**:

- Multiple window results visible
- active_users table populated
- Parquet files created

**5+ minutes**:

- All features working
- Session data appearing
- Regular updates visible

---

## 📊 Sample Queries to Verify Pipeline

### Check if events are being processed

```sql
-- In PostgreSQL
SELECT COUNT(*) FROM page_view_counts;

-- Should return > 0 after 2-3 minutes
```

### Verify window intervals

```sql
SELECT DISTINCT
    EXTRACT(MINUTE FROM window_start) as minute,
    COUNT(*) as records
FROM page_view_counts
GROUP BY minute
ORDER BY minute;

-- Should see records with 1-minute intervals
```

### Check data lake partitions

```bash
# Check dates in data lake
ls -1 ./data/lake/ | grep event_date

# Count files per date
for dir in ./data/lake/event_date=*/; do
    echo "$dir: $(ls -1 "$dir"/*.parquet 2>/dev/null | wc -l) files"
done
```

---

## 🎯 Core Concepts Reference

| Concept             | Description                   | Implementation            |
| ------------------- | ----------------------------- | ------------------------- |
| **Tumbling Window** | Non-overlapping 1-min windows | page_view_counts table    |
| **Sliding Window**  | 5-min window, 1-min slide     | active_users table        |
| **Watermark**       | 2-min late data threshold     | Drop old events           |
| **State**           | Track session data            | user_sessions table       |
| **Idempotent**      | Safe to retry writes          | INSERT ON CONFLICT        |
| **Data Lake**       | Historical archive            | Parquet partitioned files |
| **Enrichment**      | Add processing_time           | enriched_activity topic   |

---

## 🔗 Important Directories

| Path           | Purpose                              |
| -------------- | ------------------------------------ |
| `./spark/app/` | Spark application code               |
| `./scripts/`   | Producer and utility scripts         |
| `./data/lake/` | Output Parquet files (data lake)     |
| `/tmp/`        | Spark checkpoints (inside container) |

---

## 💡 Pro Tips

1. **Monitor multiple things at once**:
   - Use VS Code terminal groups
   - Or use tmux/screen for multiple terminals

2. **Save database outputs**:

   ```bash
   docker exec db psql -U user -d stream_data -c "SELECT * FROM page_view_counts;" > output.csv
   ```

3. **Tail logs efficiently**:

   ```bash
   docker-compose logs -f spark-app | grep -i "processed\|error\|watermark"
   ```

4. **Clean up Docker**:

   ```bash
   docker-compose down -v  # Remove containers and volumes
   docker system prune -a  # Remove unused images
   ```

5. **Reset the pipeline**:
   ```bash
   docker-compose down -v
   rm -rf ./data/lake/*
   docker-compose up -d --build
   ```

---

## 📚 Documentation Links (Local)

- **Full Guide**: README.md
- **Implementation Details**: IMPLEMENTATION_SUMMARY.md
- **System Requirements**: REQUIREMENTS.md
- **All Deliverables**: DELIVERABLES.md

---

## 🆘 Getting Help

1. Check if all containers are running: `docker-compose ps`
2. View error logs: `docker-compose logs`
3. Run verification script: `python scripts/verify.py`
4. Check README.md troubleshooting section
5. Review IMPLEMENTATION_SUMMARY.md technical details

---

**Version**: 1.0
**Last Updated**: January 2026
