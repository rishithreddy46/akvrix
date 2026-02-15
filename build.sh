#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Seed products if DB is fresh
python manage.py seed_data

# Create superuser (idempotent) — Akhil / Akhil@123
python manage.py shell -c "
from django.contrib.auth.models import User
# Remove any other superusers
User.objects.filter(is_superuser=True).exclude(username='Akhil').update(is_superuser=False, is_staff=False)
if not User.objects.filter(username='Akhil').exists():
    User.objects.create_superuser('Akhil', 'akhil@akvrix.com', 'Akhil@123', first_name='Akhil')
    print('Superuser created: Akhil')
else:
    u = User.objects.get(username='Akhil')
    u.is_superuser = True
    u.is_staff = True
    u.save()
    print('Superuser Akhil verified')
"

# Ensure django.contrib.sites has a Site with SITE_ID=1
python manage.py shell -c "
from django.contrib.sites.models import Site
site, created = Site.objects.get_or_create(id=1, defaults={'domain': 'akvrix.onrender.com', 'name': 'AKVRIX'})
if not created:
    site.domain = 'akvrix.onrender.com'
    site.name = 'AKVRIX'
    site.save()
print(f'Site: {site.domain}')
"
