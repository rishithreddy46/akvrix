#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Seed products if DB is fresh
python manage.py seed_data

# Create/reset single superuser — Akhil / Akhil@123
python manage.py shell -c "
from django.contrib.auth.models import User
# Delete ALL users except Akhil
User.objects.exclude(username='Akhil').delete()
if not User.objects.filter(username='Akhil').exists():
    User.objects.create_superuser('Akhil', 'akhil@akvrix.com', 'Akhil@123', first_name='Akhil')
    print('Superuser created: Akhil')
else:
    u = User.objects.get(username='Akhil')
    u.set_password('Akhil@123')
    u.is_superuser = True
    u.is_staff = True
    u.email = 'akhil@akvrix.com'
    u.first_name = 'Akhil'
    u.save()
    print('Superuser Akhil reset with password Akhil@123')
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
