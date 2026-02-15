#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Seed products if DB is fresh
python manage.py seed_data

# Create superuser for admin dashboard (idempotent)
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@akvrix.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"
