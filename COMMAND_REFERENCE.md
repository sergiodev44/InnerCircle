# InnerCircle Deployment - Command Reference Card

## 📋 One-Sheet Quick Commands

### Local Development

```bash
# First time setup
cd /home/smartrent/Escritorio/InnerCircle
chmod +x docker-setup.sh
cp .env.example .env
./docker-setup.sh

# Daily usage
docker-compose up -d           # Start
docker-compose logs -f         # View logs
docker-compose down            # Stop
docker-compose ps              # Status

# Access admin
# http://localhost/admin
```

### EC2 Deployment

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# Initial setup (one time)
curl -O https://raw.githubusercontent.com/YOUR-USER/YOUR-REPO/main/ec2-setup.sh
chmod +x ec2-setup.sh
./ec2-setup.sh

# Deploy your code
cd /opt/innercircle
git clone https://github.com/YOUR-USER/YOUR-REPO.git .
cp .env.example .env
nano .env              # Fill in production values
docker-compose up -d

# Initialize database
docker-compose exec web python proyecto_final/manage.py migrate
docker-compose exec web python proyecto_final/manage.py createsuperuser

# Setup HTTPS
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/innercircle/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/innercircle/
sudo chmod 644 /opt/innercircle/*.pem
nano nginx.conf        # Uncomment HTTPS block
docker-compose restart nginx
```

### Docker-Compose Recipes

```bash
# Django Management
docker-compose exec web python proyecto_final/manage.py migrate
docker-compose exec web python proyecto_final/manage.py createsuperuser
docker-compose exec web python proyecto_final/manage.py collectstatic --noinput
docker-compose exec web python proyecto_final/manage.py shell
docker-compose exec web python proyecto_final/manage.py test

# Database
docker-compose exec db psql -U innercircle_user -d innercircle_db
docker-compose exec -T db pg_dump -U innercircle_user innercircle_db > backup.sql

# Shell Access
docker-compose exec web bash
docker-compose exec db bash

# Logs
docker-compose logs -f              # All services
docker-compose logs -f web          # Django only
docker-compose logs -f db           # Database only
docker-compose logs -f nginx        # Web server only

# Restart Services
docker-compose restart              # All
docker-compose restart web
docker-compose restart nginx
docker-compose restart db

# Debugging
docker-compose ps                   # Check status
docker-compose exec web python proyecto_final/manage.py check
docker stats                         # Resource usage
```

### PostgreSQL Troubleshooting

```bash
# Connect to database
docker-compose exec db psql -U innercircle_user -d innercircle_db

# Common queries
\dt                    # List tables
\l                     # List databases
SELECT COUNT(*) FROM inner_circle_user;  # Count users
SELECT COUNT(*) FROM inner_circle_product;  # Count products

# Reset sequences (after data import)
SELECT setval(pg_get_serial_sequence('inner_circle_user', 'id'), 
              (SELECT MAX(id) FROM inner_circle_user));
```

### File Locations Reference

```
/opt/innercircle/
├── .env                          # Production secrets (DO NOT COMMIT)
├── .env.example                  # Template (commit this)
├── docker-compose.yml            # Container orchestration
├── Dockerfile                    # Django image definition
├── nginx.conf                    # Web server config
├── requirements.txt              # Python dependencies
├── fullchain.pem                 # SSL certificate (DO NOT COMMIT)
├── privkey.pem                   # SSL key (DO NOT COMMIT)
├── proyecto_final/               # Django project
│   ├── mysite/
│   │   └── settings.py          # Updated for production
│   ├── manage.py
│   └── db.sqlite3               # (Only in local dev)
│
└── Documentation/
    ├── DEPLOYMENT_QUICK_START.md
    ├── EC2_DEPLOYMENT_GUIDE.md
    └── DATABASE_MIGRATION.md
```

### Environment Variables Checklist

**Required for Production:**
```bash
✓ DEBUG=False
✓ SECRET_KEY=<generated>
✓ ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
✓ DB_ENGINE=django.db.backends.postgresql
✓ DB_PASSWORD=<strong>
✓ STRIPE_SECRET_KEY=sk_live_xxxxx
✓ EMAIL_HOST_USER=your-email@gmail.com
✓ EMAIL_HOST_PASSWORD=<app-password>
```

### Emergency Commands

```bash
# Stop everything
docker-compose down

# Remove everything (INCLUDING DATA!)
docker-compose down -v

# Emergency restart
docker-compose restart

# View all errors
docker-compose logs web | grep -i error

# Force rebuild from scratch
docker-compose build --no-cache
docker-compose up -d

# Check what's using ports
sudo ss -tulpn | grep LISTEN
sudo lsof -i :80
sudo lsof -i :8000
```

### Deployment Pipeline (GitHub Actions)

**Triggered by:** Push to main branch

1. ✅ Checkout code
2. ✅ Run tests (PostgreSQL)
3. ✅ Build Docker images
4. ✅ SSH to EC2
5. ✅ Pull latest code
6. ✅ Rebuild containers
7. ✅ Run migrations
8. ✅ Collect static files
9. ✅ Notify on completion

To disable: Comment out `.github/workflows/deploy.yml` or delete it

### Monitoring Commands

```bash
# Real-time stats
watch docker-compose ps

# Disk usage
df -h

# Memory usage
free -h

# Docker disk usage
docker system df

# Process memory in containers
docker-compose top web
```

### Common Issues & Quick Fixes

| Issue | Command |
|-------|---------|
| Static files not loading | `docker-compose exec web python proyecto_final/manage.py collectstatic --noinput` |
| Database locked | `docker-compose restart db` |
| Port already in use | `sudo lsof -i :80 && sudo kill -9 PID` |
| Out of memory | `docker system prune -a && docker volume prune` |
| Settings errors | `docker-compose exec web python proyecto_final/manage.py check` |
| Lost database (oops!) | `docker-compose down -v` then restart (data gone, tables recreated) |

### Daily Operations

```bash
# Morning: Check everything is running
ssh ubuntu@your-ec2-ip
docker-compose ps

# View recent logs
docker-compose logs --tail=50

# Back up database (daily)
docker-compose exec -T db pg_dump -U innercircle_user innercircle_db > \
  backup-$(date +%Y-%m-%d).sql

# Check disk space
df -h

# Evening: Deploy new changes (if needed)
git pull origin main
docker-compose build
docker-compose down
docker-compose up -d
docker-compose exec web python proyecto_final/manage.py migrate
docker-compose logs -f web
```

---

**🔗 Full guides:** See `DEPLOYMENT_QUICK_START.md` and `EC2_DEPLOYMENT_GUIDE.md`
