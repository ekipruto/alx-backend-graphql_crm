#!/bin/bash

python manage.py shell <<EOF
from crm.models import Customer
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

cutoff_date = timezone.now() - timedelta(days=365)

# Get IDs only (safe with distinct)
inactive_ids = Customer.objects.filter(
    Q(orders__isnull=True) | Q(updated_at__lt=cutoff_date)
).values_list('id', flat=True).distinct()

# Delete using IDs
deleted_count, _ = Customer.objects.filter(id__in=inactive_ids).delete()

print(f"Deleted {deleted_count} inactive customers")
EOF

