# Real-Time Streaming Data Pipeline - Startup Script for Windows

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Real-Time Streaming Data Pipeline" -ForegroundColor Cyan
Write-Host "Apache Kafka + Spark Streaming" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "ERROR: Docker is not installed or not running" -ForegroundColor Red
    exit 1
}

# Check for .env file
if (!(Test-Path .env)) {
    Write-Host "Creating .env file from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✓ .env file created. Update it with your values if needed." -ForegroundColor Green
}

Write-Host ""
Write-Host "Step 1: Building and starting Docker containers..." -ForegroundColor Cyan
Write-Host "This may take a few minutes on first run..." -ForegroundColor Yellow
Write-Host ""

docker-compose up -d --build

Write-Host ""
Write-Host "Step 2: Waiting for services to become healthy..." -ForegroundColor Cyan
Write-Host ""

# Function to check service health
function Check-ServiceHealth {
    param($Service)
    $maxAttempts = 30
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        $status = docker-compose ps $Service 2>$null
        if ($status -match "healthy|running") {
            Write-Host "✓ $Service is healthy" -ForegroundColor Green
            return $true
        }
        
        Write-Host "⋯ Waiting for $Service... ($($attempt+1)/$maxAttempts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
        $attempt++
    }
    
    Write-Host "✗ $Service failed to become healthy" -ForegroundColor Red
    return $false
}

Check-ServiceHealth "zookeeper"
Check-ServiceHealth "kafka"
Check-ServiceHealth "db"

Write-Host ""
Write-Host "Step 3: Pipeline is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. In another terminal, start the data producer:" -ForegroundColor Cyan
Write-Host "   python scripts\producer.py" -ForegroundColor White
Write-Host ""
Write-Host "2. Monitor the Spark application:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f spark-app" -ForegroundColor White
Write-Host ""
Write-Host "3. Check results in PostgreSQL:" -ForegroundColor Cyan
Write-Host "   docker exec -it db psql -U user -d stream_data" -ForegroundColor White
Write-Host "   SELECT * FROM page_view_counts LIMIT 10;" -ForegroundColor White
Write-Host ""
Write-Host "4. View Parquet files in the data lake:" -ForegroundColor Cyan
Write-Host "   Get-ChildItem -Path ./data/lake -Recurse -Filter '*.parquet'" -ForegroundColor White
Write-Host ""
Write-Host "5. Monitor enriched events in Kafka:" -ForegroundColor Cyan
Write-Host "   docker exec kafka /usr/bin/kafka-console-consumer --bootstrap-server localhost:9092 --topic enriched_activity" -ForegroundColor White
Write-Host ""
Write-Host "To stop the pipeline:" -ForegroundColor Cyan
Write-Host "   docker-compose down" -ForegroundColor White
Write-Host ""
Write-Host "For more information, see README.md" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
