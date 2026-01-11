#!/bin/bash

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MANAGE_PY="$PROJECT_DIR/manage.py"

# Run the Django command to delete inactive customers
OUTPUT=$(python "$MANAGE_PY" shell -c "
from crm.models import Customer
from django.utils import timezone
from datetime import timedelta
cutoff = timezone.now() - timedelta(days=365)
inactive = Customer.objects.exclude(orders__order_date__gte=cutoff)
count = inactive.count()
inactive.delete()
print(f'Deleted {count} inactive customers')
")

# Log with timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$TIMESTAMP] $OUTPUT" >> /tmp/customer_cleanup_log.txt