# InnerCircle Database Migration Guide

## Migrating from SQLite to PostgreSQL

### Local Development (Docker)

```bash
# 1. Ensure .env is properly configured
cp .env.example .env
# Edit .env with your PostgreSQL settings

# 2. Backup your SQLite database first
cp proyecto_final/db.sqlite3 proyecto_final/db.sqlite3.backup

# 3. Start PostgreSQL container
docker-compose up -d db

# 4. Wait for database to be ready (10-20 seconds)
docker-compose exec db psql -U innercircle_user -d innercircle_db -c "SELECT 1;"

# 5. Run migrations
docker-compose exec web python proyecto_final/manage.py migrate

# 6. If you have existing data, use Django data migration
# Export data from SQLite
docker run --rm -v $(pwd):/app python:3.11 bash -c "cd /app && pip install -q Django python-dotenv psycopg2-binary && python proyecto_final/manage.py dumpdata --exclude auth.permission --exclude contenttypes > /tmp/data.json"

# 7. Import data to PostgreSQL
docker-compose exec web python proyecto_final/manage.py loaddata /tmp/data.json

# 8. Verify data
docker-compose exec web python proyecto_final/manage.py shell
# >>> from inner_circle.models import User
# >>> User.objects.count()  # Should show your user count
```

### Production (EC2)

```bash
# 1. SSH into your EC2 instance
ssh ubuntu@your-ec2-ip

# 2. Stop the application
cd /opt/innercircle
docker-compose down

# 3. Update .env to use PostgreSQL
nano .env
# Make sure DB_ENGINE=django.db.backends.postgresql

# 4. Start containers
docker-compose up -d

# 5. Wait for database to be ready
sleep 20

# 6. Run migrations
docker-compose exec -T web python proyecto_final/manage.py migrate

# 7. Create superuser
docker-compose exec web python proyecto_final/manage.py createsuperuser

# 8. Verify Application
docker-compose logs -f web
# Check for any errors
```

### Handling Large Databases

If you have significant data in SQLite:

```bash
# 1. Export from SQLite
python proyecto_final/manage.py dumpdata --exclude auth.permission --exclude contenttypes > dump.json

# 2. Switch to PostgreSQL in settings
# Update settings.py to use PostgreSQL

# 3. Run migrations
python proyecto_final/manage.py migrate

# 4. Load data
python proyecto_final/manage.py loaddata dump.json

# 5. Fix sequences (important!)
docker-compose exec web python proyecto_final/manage.py shell << 'EOF'
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT setval(pg_get_serial_sequence('inner_circle_user', 'id'), (SELECT MAX(id) FROM inner_circle_user));")
cursor.execute("SELECT setval(pg_get_serial_sequence('inner_circle_product', 'id'), (SELECT MAX(id) FROM inner_circle_product));")
# Add for all tables with auto-incrementing IDs
EOF
```

### Rollback Plan

If things go wrong:

```bash
# Keep your SQLite backup safe
cp proyecto_final/db.sqlite3.backup proyecto_final/db.sqlite3

# Switch back to SQLite in .env
nano .env
# Set: DB_ENGINE=django.db.backends.sqlite3

# Restart application
docker-compose restart web
```
