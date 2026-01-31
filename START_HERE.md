# 🚀 START HERE - Getting Started Guide

## Real-Time Streaming Data Pipeline

Welcome! This guide will help you get the pipeline running in 5 minutes.

---

## 📝 What You Need

- Docker and Docker Compose installed
- Python 3.8+ (for producer script)
- 4GB RAM available
- 2GB free disk space

**Check if you have them**:

```powershell
docker --version
docker-compose --version
python --version
```

---

## ⚡ Quick Start (3 Steps)

### Step 1: Setup (1 minute)

```powershell
cd d:\Desktop\pipeline
cp .env.example .env
```

### Step 2: Start Services (2 minutes)

```powershell
docker-compose up -d --build
docker-compose ps  # Wait until all show "healthy" or "Up"
```

### Step 3: Run Producer (in another terminal)

```powershell
python scripts/producer.py
```

**That's it!** The pipeline is now running.

---

## 📊 Verify It's Working

### Check Database Results

```powershell
docker exec -it db psql -U user -d stream_data
```

Then run these queries:

```sql
-- See page view counts
SELECT * FROM page_view_counts ORDER BY window_start DESC LIMIT 5;

-- See active users
SELECT * FROM active_users ORDER BY window_start DESC LIMIT 5;

-- See user sessions
SELECT * FROM user_sessions LIMIT 5;
```

### Check Spark Logs

```powershell
docker-compose logs -f spark-app
```

### Check Data Lake Files

```powershell
Get-ChildItem -Path "./data/lake" -Recurse -Filter "*.parquet"
```

---

## 📚 What's in the Project

| Folder     | Contains                          |
| ---------- | --------------------------------- |
| `spark/`   | Spark streaming application       |
| `scripts/` | Data producer and testing scripts |
| `data/`    | Output data lake                  |
| Root       | Docker setup and documentation    |

---

## 📖 Documentation

Read in this order:

1. **This file** (what you're reading) - 5 min
2. **[QUICKSTART.md](QUICKSTART.md)** - 10 min quick reference
3. **[README.md](README.md)** - 30 min complete guide
4. **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - 15 min technical details

---

## 🔍 Understanding the Pipeline

```
User Activity Events
        ↓
   Apache Kafka (input topic: user_activity)
        ↓
   Apache Spark Streaming
        ├─→ Tumbling Windows (1 min)   → PostgreSQL
        ├─→ Sliding Windows (5 min)    → PostgreSQL
        ├─→ Stateful Sessions         → PostgreSQL
        └─→ Late Data Handling        → Watermarking
        ↓
   Multiple Outputs:
   ├─→ PostgreSQL (real-time aggregations)
   ├─→ Parquet Files (data lake)
   └─→ Kafka (enriched events)
```

---

## 🎯 Key Features

✅ **Real-time Processing**: Events processed in < 1 second
✅ **Windowed Aggregations**: Tumbling and sliding windows
✅ **State Management**: Track user sessions with timeout
✅ **Late Data Handling**: 2-minute watermark threshold
✅ **Multiple Sinks**: Database, data lake, and message queue
✅ **Exactly-Once**: Idempotent writes prevent duplicates

---

## ❌ If Something Goes Wrong

### Services won't start

```powershell
# Check what went wrong
docker-compose logs

# Try again
docker-compose down
docker-compose up -d --build
```

### No data in database

```powershell
# Check if producer is running
Get-Process python | Where-Object {$_.Name -match "producer"}

# Check Kafka has data
docker exec kafka /usr/bin/kafka-console-consumer `
  --bootstrap-server localhost:9092 `
  --topic user_activity `
  --max-messages 1
```

### Port conflicts

```powershell
# Find what's using the port
netstat -ano | findstr :9092  # for Kafka

# Stop using that port and try again
docker-compose down
docker-compose up -d --build
```

---

## ⚙️ Configuration

The `.env` file controls:

```
DB_USER=user                      # Username for database
DB_PASSWORD=password              # Password for database
DB_NAME=stream_data              # Database name
KAFKA_BOOTSTRAP_SERVERS=kafka:9092 # Kafka connection
```

Change these values before running if needed.

---

## 📊 Monitoring

### Watch Logs Live

```powershell
docker-compose logs -f spark-app
```

### Query Database

```powershell
# Connect to database
docker exec -it db psql -U user -d stream_data

# Then use SQL to check results
SELECT COUNT(*) FROM page_view_counts;
SELECT COUNT(*) FROM active_users;
SELECT COUNT(*) FROM user_sessions;
```

### Check Data Lake

```powershell
# List Parquet files
Get-ChildItem -Path "./data/lake" -Recurse -Filter "*.parquet"

# Count files
(Get-ChildItem -Path "./data/lake" -Recurse -Filter "*.parquet" | Measure-Object).Count
```

---

## 🛑 When You're Done

Stop the pipeline:

```powershell
docker-compose down
```

Remove all data and start fresh:

```powershell
docker-compose down -v
Remove-Item -Path "data/lake/*" -Recurse -Force
docker-compose up -d --build
```

---

## 💡 What Each Component Does

### Zookeeper

Coordinates Kafka brokers. Automatic.

### Kafka

Receives events and distributes them. Automatic.

### PostgreSQL

Stores real-time aggregations. Automatic.

### Spark App

Processes events and writes to all sinks. Automatic.

### Producer Script

Generates test events. You run this: `python scripts/producer.py`

---

## 🎓 What You'll Learn

- How real-time data pipelines work
- How to process streaming data with Spark
- How windowed aggregations work
- How to handle late-arriving data
- How to build multi-sink architectures
- Docker and containerization

---

## 🔗 Key Commands

| Command                                          | What it does            |
| ------------------------------------------------ | ----------------------- |
| `docker-compose up -d --build`                   | Start all services      |
| `docker-compose ps`                              | Check service status    |
| `docker-compose logs -f spark-app`               | Watch Spark logs        |
| `docker-compose down`                            | Stop all services       |
| `python scripts/producer.py`                     | Start generating events |
| `docker exec -it db psql -U user -d stream_data` | Connect to database     |
| `python scripts/verify.py`                       | Verify all components   |

---

## 📞 Getting More Help

1. **Quick answers**: See [QUICKSTART.md](QUICKSTART.md)
2. **Full guide**: See [README.md](README.md)
3. **Technical details**: See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
4. **System setup**: See [REQUIREMENTS.md](REQUIREMENTS.md)
5. **File guide**: See [INDEX.md](INDEX.md)

---

## ✅ Checklist: Everything Working?

- [ ] All containers running: `docker-compose ps`
- [ ] Producer running: See events in producer output
- [ ] Spark processing: Check logs show "processed"
- [ ] Database filled: Query returns results
- [ ] Data lake created: Files in `./data/lake/`
- [ ] Enriched topic: Monitor enriched_activity topic

If all above are checked ✅, **your pipeline is working!**

---

## 🎉 What's Next

1. **Read the README** for deep understanding
2. **Experiment** with the producer (try different event rates)
3. **Query** the database to see results
4. **Monitor** the logs to understand the flow
5. **Read** IMPLEMENTATION_SUMMARY for technical details

---

## 🚀 You're Ready!

You now have a production-quality real-time data pipeline running on your computer.

**Start exploring!**

```powershell
cd d:\Desktop\pipeline
cp .env.example .env
docker-compose up -d --build
python scripts/producer.py
```

---

**Questions?** Check [README.md](README.md) or [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

**Happy streaming! 🎉**
