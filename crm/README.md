# CRM Celery & Beat Setup

## Prerequisites

- Install Redis and ensure it is running on localhost:6379
- Install Python dependencies:
  ```
  pip install -r requirements.txt
  ```
- Run Django migrations:
  ```
  python manage.py migrate
  ```

## Running Celery Worker

```
celery -A crm worker -l info
```

## Running Celery Beat

```
celery -A crm beat -l info
```

## Verify

- Check `/tmp/crm_report_log.txt` for weekly reports.
