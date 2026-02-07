# CRM Celery Setup Guide

This guide explains how to set up and run Celery tasks for automated CRM report generation.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation Steps](#installation-steps)
  - [Install Redis](#install-redis)
  - [Install Dependencies](#install-dependencies)
  - [Run Migrations](#run-migrations)
- [Running the Application](#running-the-application)
  - [Start Django Server](#start-django-server)
  - [Start Celery Worker](#start-celery-worker)
  - [Start Celery Beat](#start-celery-beat)
- [Testing](#testing)
- [Verify Logs](#verify-logs)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)
- [Monitoring](#monitoring)

## Overview

The CRM application uses Celery for asynchronous task processing, including:
- Weekly CRM reports (customers, orders, revenue)
- Background job processing
- Scheduled task execution with Celery Beat

Celery uses Redis as a message broker and result backend, providing reliable task queuing and execution.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10 or higher**
- **Django 4.2 or higher**
- **Redis server** (message broker)
- **pip** (Python package manager)
- **virtualenv** (recommended for isolated environments)

## Installation Steps

Follow these steps in order to set up the Celery task system.

### Install Redis

Redis is required as the message broker for Celery.

#### On Ubuntu/Debian/WSL:
```bash
# Update package list
sudo apt-get update

# Install Redis server
sudo apt-get install -y redis-server

# Start Redis service
sudo service redis-server start

# Enable Redis to start on boot
sudo systemctl enable redis-server
```

#### On macOS:
```bash
# Using Homebrew
brew install redis

# Start Redis
brew services start redis
```

#### Using Docker:
```bash
# Run Redis in a Docker container
docker run -d --name redis -p 6379:6379 redis:latest

# Verify container is running
docker ps | grep redis
```

#### Verify Redis Installation:
```bash
# Test Redis connection
redis-cli ping

# Expected output: PONG
```

If Redis is not responding:
```bash
# Check Redis status
sudo service redis-server status

# Restart Redis if needed
sudo service redis-server restart

# Check Redis is listening on port 6379
sudo netstat -tlnp | grep 6379
```

### Install Dependencies

Install all required Python packages for Celery and the CRM application.

#### Using pip:
```bash
# Navigate to project directory
cd /path/to/alx-backend-graphql_crm

# Install from requirements.txt
pip install -r requirements.txt
```

#### Install Individual Packages:

If you prefer to install packages individually:
```bash
# Core Celery packages
pip install celery==5.3.4
pip install redis==5.0.1
pip install django-celery-beat==2.5.0

# HTTP and GraphQL clients
pip install requests
pip install gql[all]

# Django and GraphQL
pip install django==4.2.7
pip install graphene-django==3.1.5
pip install django-filter==23.3
```

#### Verify Installation:
```bash
# Check Celery version
celery --version

# Check installed packages
pip list | grep -E "(celery|redis|django)"
```

Expected packages:
- `celery (5.3.4)`
- `redis (5.0.1)`
- `django-celery-beat (2.5.0)`
- `requests (2.31.0)`
- `gql (3.4.1)`

### Run Migrations

Run Django migrations to create necessary database tables for Celery Beat.
```bash
# Navigate to project root
cd /path/to/alx-backend-graphql_crm

# Apply all migrations
python manage.py migrate

# Specifically migrate django-celery-beat
python manage.py migrate django_celery_beat
```

**Expected output:**
```
Running migrations:
  Applying django_celery_beat.0001_initial... OK
  Applying django_celery_beat.0002_auto_20161118_0346... OK
  Applying django_celery_beat.0003_auto_20161209_0049... OK
  ...
```

These migrations create tables for:
- Periodic tasks
- Interval schedules
- Crontab schedules
- Solar schedules

## Running the Application

You need to run three separate processes for the complete system.

### Start Django Server

In **Terminal 1**, start the Django development server:
```bash
# Navigate to project directory
cd /path/to/alx-backend-graphql_crm

# Start Django server
python manage.py runserver

# Or specify host and port
python manage.py runserver 0.0.0.0:8000
```

**Expected output:**
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
January 11, 2025 - 10:00:00
Django version 4.2.7, using settings 'graphql_crm.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

**Keep this terminal running.**

### Start Celery Worker

In **Terminal 2**, start the Celery worker to process tasks:
```bash
# Navigate to project directory
cd /path/to/alx-backend-graphql_crm

# Start Celery worker
celery -A crm worker -l info

# Alternative: with more verbose logging
celery -A crm worker -l debug
```

**Expected output:**
```
 -------------- celery@hostname v5.3.4 (emerald-rush)
--- ***** ----- 
-- ******* ---- Linux-5.15.0-91-generic-x86_64-with-glibc2.35 2025-01-11 10:00:00
- *** --- * --- 
- ** ---------- [config]
- ** ---------- .> app:         crm:0x7f8b3c0a4d90
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 4 (prefork)
-- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
--- ***** ----- 
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery

[tasks]
  . crm.tasks.generate_crm_report
  . crm.tasks.manual_report
  . crm.tasks.test_celery

[2025-01-11 10:00:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
[2025-01-11 10:00:00,000: INFO/MainProcess] mingle: searching for neighbors
[2025-01-11 10:00:01,000: INFO/MainProcess] mingle: all alone
[2025-01-11 10:00:01,000: INFO/MainProcess] celery@hostname ready.
```

**Keep this terminal running.**

### Start Celery Beat

In **Terminal 3**, start Celery Beat to schedule periodic tasks:
```bash
# Navigate to project directory
cd /path/to/alx-backend-graphql_crm

# Start Celery Beat
celery -A crm beat -l info

# Alternative: with database scheduler
celery -A crm beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

**Expected output:**
```
celery beat v5.3.4 (emerald-rush) is starting.
__    -    ... __   -        _
LocalTime -> 2025-01-11 10:00:00
Configuration ->
    . broker -> redis://localhost:6379/0
    . loader -> celery.loaders.app.AppLoader
    . scheduler -> celery.beat.PersistentScheduler
    . db -> celerybeat-schedule
    . logfile -> [stderr]@%INFO
    . maxinterval -> 5.00 minutes (300s)

[2025-01-11 10:00:00,000: INFO/MainProcess] beat: Starting...
[2025-01-11 10:00:00,000: INFO/MainProcess] Scheduler: Sending due task generate-crm-report (crm.tasks.generate_crm_report)
```

**Keep this terminal running.**

### Summary of Running Processes

You should now have **three terminals** running simultaneously:

| Terminal | Process | Command | Port |
|----------|---------|---------|------|
| Terminal 1 | Django Server | `python manage.py runserver` | 8000 |
| Terminal 2 | Celery Worker | `celery -A crm worker -l info` | - |
| Terminal 3 | Celery Beat | `celery -A crm beat -l info` | - |

## Testing

### Test 1: Verify Redis Connection
```bash
# Open a new terminal (Terminal 4)
redis-cli ping
```

**Expected:** `PONG`

### Test 2: Test Basic Celery Task
```bash
# Open Django shell
python manage.py shell
```
```python
from crm.tasks import test_celery

# Execute test task
result = test_celery.delay()

# Wait for result (timeout after 10 seconds)
print("Task result:", result.get(timeout=10))

# Expected output: "[2025-01-11 10:05:00] Celery test task executed successfully!"

exit()
```

### Test 3: Test CRM Report Generation
```bash
# In Django shell
python manage.py shell
```
```python
from crm.tasks import generate_crm_report

# Trigger report generation manually
result = generate_crm_report.delay()

# Get result
success = result.get(timeout=10)
print(f"Report generated: {success}")

# Expected output: True

exit()
```

### Test 4: Check Celery Worker Logs

In **Terminal 2** (Celery Worker), you should see:
```
[2025-01-11 10:05:00,000: INFO/MainProcess] Task crm.tasks.test_celery[abc-123-def] received
[2025-01-11 10:05:00,001: INFO/ForkPoolWorker-1] [2025-01-11 10:05:00] Celery test task executed successfully!
[2025-01-11 10:05:00,002: INFO/ForkPoolWorker-1] Task crm.tasks.test_celery[abc-123-def] succeeded in 0.001s: '[2025-01-11 10:05:00] Celery test task executed successfully!'

[2025-01-11 10:05:05,000: INFO/MainProcess] Task crm.tasks.generate_crm_report[def-456-ghi] received
[2025-01-11 10:05:05,500: INFO/ForkPoolWorker-2] [CRM REPORT] 2025-01-11 10:05:05 - Report: 15 customers, 42 orders, $12345.67 revenue.
[2025-01-11 10:05:05,501: INFO/ForkPoolWorker-2] Task crm.tasks.generate_crm_report[def-456-ghi] succeeded in 0.5s: True
```

## Verify Logs

Check the CRM report log file to ensure reports are being generated.

### View Complete Log:
```bash
# View entire log file
cat /tmp/crm_report_log.txt
```

### View Recent Entries:
```bash
# Show last 20 lines
tail -20 /tmp/crm_report_log.txt

# Monitor in real-time
tail -f /tmp/crm_report_log.txt
```

### Expected Log Format:
```
================================================================================
[2025-01-13 06:00:00] Weekly CRM Report
================================================================================
Total Customers: 150
Total Orders: 320
Total Revenue: $45678.90
================================================================================

2025-01-13 06:00:00 - Report: 150 customers, 320 orders, $45678.90 revenue.
```

### Log File Details:

- **Location:** `/tmp/crm_report_log.txt`
- **Format:** `YYYY-MM-DD HH:MM:SS - Report: X customers, Y orders, $Z revenue.`
- **Updated:** Every Monday at 6:00 AM UTC
- **Permissions:** Readable and writable by the user running Celery

### Check Log Permissions:
```bash
# Check if log file exists and is writable
ls -la /tmp/crm_report_log.txt

# Create if doesn't exist
touch /tmp/crm_report_log.txt

# Set permissions
chmod 666 /tmp/crm_report_log.txt
```

## Scheduled Tasks

The following tasks are scheduled to run automatically:

### Task Schedule:

| Task Name | Schedule | Description | Log File |
|-----------|----------|-------------|----------|
| `generate_crm_report` | Every Monday 6:00 AM UTC | Weekly CRM statistics | `/tmp/crm_report_log.txt` |

### Schedule Configuration:

The schedule is defined in `crm/settings.py`:
```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0),
    },
}
```

### Crontab Schedule Syntax:
```python
crontab(day_of_week='mon', hour=6, minute=0)
#       └─ Monday      └─ 6 AM  └─ 0 minutes
```

## Troubleshooting

### Problem 1: Redis Connection Refused

**Error:**
```
Error 111 connecting to localhost:6379. Connection refused.
```

**Solutions:**
```bash
# Check if Redis is running
sudo service redis-server status

# Start Redis
sudo service redis-server start

# Verify connection
redis-cli ping

# Check Redis port
sudo netstat -tlnp | grep 6379

# Check Redis logs
sudo tail -f /var/log/redis/redis-server.log
```

### Problem 2: Celery Worker Not Starting

**Error:**
```
ModuleNotFoundError: No module named 'celery'
```

**Solutions:**
```bash
# Ensure Celery is installed
pip install celery redis

# Verify installation
python -c "import celery; print(celery.__version__)"

# Check Python path
which python
which celery

# Reinstall if needed
pip uninstall celery
pip install celery==5.3.4
```

### Problem 3: Tasks Not Executing

**Symptoms:** Tasks queued but never execute.

**Checks:**
```bash
# 1. Check Celery worker is running
ps aux | grep "celery worker"

# 2. Check Celery Beat is running
ps aux | grep "celery beat"

# 3. Inspect active tasks
celery -A crm inspect active

# 4. Check registered tasks
celery -A crm inspect registered

# 5. View worker stats
celery -A crm inspect stats
```

### Problem 4: GraphQL Query Failing

**Error:**
```
TransportQueryError: 404 Client Error
```

**Solutions:**
```bash
# Ensure Django server is running
python manage.py runserver

# Test GraphQL endpoint
curl http://localhost:8000/graphql

# Test in browser
# Open: http://localhost:8000/graphql

# Check if queries work
# Run this query:
query {
  totalCustomers
  totalOrders
  totalRevenue
}
```

### Problem 5: Log File Not Created

**Solutions:**
```bash
# Check /tmp directory permissions
ls -ld /tmp

# Create log file manually
touch /tmp/crm_report_log.txt

# Set write permissions
chmod 666 /tmp/crm_report_log.txt

# Test write access
echo "test" >> /tmp/crm_report_log.txt
cat /tmp/crm_report_log.txt
```

### Problem 6: Import Errors

**Error:**
```
ImportError: cannot import name 'celery_app' from 'crm'
```

**Solution:**

Ensure `crm/__init__.py` contains:
```python
from __future__ import absolute_import, unicode_literals
from .celery import app as celery_app

__all__ = ('celery_app',)
```

## Production Deployment

### Using Systemd (Linux)

Create service files for Celery worker and beat.

#### Create Celery Worker Service:

Create `/etc/systemd/system/celery.service`:
```ini
[Unit]
Description=Celery Worker Service
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/var/www/alx-backend-graphql_crm
Environment="PATH=/var/www/alx-backend-graphql_crm/venv/bin"
ExecStart=/var/www/alx-backend-graphql_crm/venv/bin/celery -A crm worker -l info --detach --pidfile=/var/run/celery/worker.pid --logfile=/var/log/celery/worker.log
ExecStop=/var/www/alx-backend-graphql_crm/venv/bin/celery -A crm control shutdown
PIDFile=/var/run/celery/worker.pid
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

#### Create Celery Beat Service:

Create `/etc/systemd/system/celerybeat.service`:
```ini
[Unit]
Description=Celery Beat Service
After=network.target redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/alx-backend-graphql_crm
Environment="PATH=/var/www/alx-backend-graphql_crm/venv/bin"
ExecStart=/var/www/alx-backend-graphql_crm/venv/bin/celery -A crm beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler --pidfile=/var/run/celery/beat.pid --logfile=/var/log/celery/beat.log
PIDFile=/var/run/celery/beat.pid
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

#### Enable and Start Services:
```bash
# Create log directories
sudo mkdir -p /var/log/celery
sudo mkdir -p /var/run/celery
sudo chown www-data:www-data /var/log/celery /var/run/celery

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable celery celerybeat

# Start services
sudo systemctl start celery celerybeat

# Check status
sudo systemctl status celery
sudo systemctl status celerybeat

# View logs
sudo journalctl -u celery -f
sudo journalctl -u celerybeat -f
```

## Monitoring

### Celery Inspect Commands
```bash
# View active tasks
celery -A crm inspect active

# View registered tasks
celery -A crm inspect registered

# View scheduled tasks
celery -A crm inspect scheduled

# View worker statistics
celery -A crm inspect stats

# Ping workers
celery -A crm inspect ping
```

### Using Flower (Web Interface)

Flower provides a web-based monitoring tool for Celery.

#### Install Flower:
```bash
pip install flower
```

#### Start Flower:
```bash
celery -A crm flower --port=5555
```

#### Access Flower:

Open browser: http://localhost:5555

Features:
- Real-time task monitoring
- Worker statistics
- Task history
- Task rate graphs

## Additional Resources

- [Celery Documentation](https://docs.celeryproject.org/en/stable/)
- [Django-Celery-Beat Documentation](https://django-celery-beat.readthedocs.io/)
- [Redis Documentation](https://redis.io/documentation)
- [GraphQL Python (gql) Documentation](https://gql.readthedocs.io/)

## Support

For issues or questions:
- Review the troubleshooting section
- Check Celery worker and beat logs
- Verify all services are running
- Ensure GraphQL endpoint is accessible
- Check /tmp/crm_report_log.txt for task execution logs
README
