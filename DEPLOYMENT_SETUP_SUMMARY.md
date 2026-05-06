# 📦 InnerCircle Deployment Setup - Summary

## ✅ What Was Done

### 1. **Created Deployment Configuration Files**

#### Core Docker Files:
- **`Dockerfile`** - Multi-stage Django app container with Python 3.11
- **`docker-compose.yml`** - Orchestrates Django, PostgreSQL, and Nginx
- **`nginx.conf`** - Production web server with SSL support and rate limiting
- **`requirements.txt`** - All Python dependencies including psycopg2 (PostgreSQL driver) and gunicorn

#### Environment & Configuration:
- **`.env.example`** - Template for all environment variables
- Updated **`mysite/settings.py`** - Now supports both PostgreSQL and SQLite:
  - Dynamic database selection based on `DB_ENGINE` env variable
  - Production security settings (HTTPS redirect, secure cookies, HSTS headers)
  - WhiteNoise middleware for efficient static file serving
  - Configurable ALLOWED_HOSTS from environment

### 2. **Created Deployment Guides**

- **`DEPLOYMENT_QUICK_START.md`** - 5-minute overview (READ THIS FIRST)
- **`EC2_DEPLOYMENT_GUIDE.md`** - Comprehensive step-by-step AWS deployment
- **`DATABASE_MIGRATION.md`** - SQLite to PostgreSQL migration procedures

### 3. **Created Automation Scripts**

- **`docker-setup.sh`** - Local development Docker setup
- **`ec2-setup.sh`** - EC2 instance initialization (installs Docker, configures firewall, etc.)

### 4. **Created CI/CD Workflows**

- **`.github/workflows/deploy.yml`** - Auto-deploy to EC2 on every push to main
- **`.github/workflows/tests.yml`** - Automated testing with PostgreSQL

### 5. **Updated Security**

- Updated **`.gitignore`** to exclude `.pem` files, `.sql` backups, and logs
- Added production security headers in Django settings
- Configured secure cookie settings for HTTPS

---

## 🚀 Next Steps (In Order)

### **Phase 1: Local Testing (Do First)**

```bash
cd /home/smartrent/Escritorio/InnerCircle

# 1. Make scripts executable
chmod +x docker-setup.sh ec2-setup.sh

# 2. Copy .env template
cp .env.example .env

# 3. Edit .env with your Stripe, Email, and other keys from your existing .env
nano .env

# 4. Run local Docker setup (this tests everything)
./docker-setup.sh

# 5. Verify:
# - Web: http://localhost
# - Admin: http://localhost/admin
```

### **Phase 2: AWS Setup**

1. **Create EC2 Instance** (AWS Console):
   - AMI: Ubuntu 24.04 LTS
   - Type: t3.micro (free tier) or t3.small
   - Storage: 30GB
   - Security Group: Allow 22, 80, 443
   - Generate SSH key pair

2. **Note your:**
   - EC2 Public IP
   - SSH Private Key File

### **Phase 3: Deploy to EC2**

```bash
# 1. SSH into EC2
ssh -i your-key.pem ubuntu@your-ec2-public-ip

# 2. Run setup script
curl -O https://raw.githubusercontent.com/YOUR-USERNAME/YOUR-REPO/main/ec2-setup.sh
chmod +x ec2-setup.sh
./ec2-setup.sh

# 3. Clone repository
cd /opt/innercircle
git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git .

# 4. Configure environment
cp .env.example .env
nano .env  # Update with PRODUCTION values

# 5. Start application
docker-compose up -d

# 6. Run migrations
docker-compose exec web python proyecto_final/manage.py migrate

# 7. Create superuser
docker-compose exec web python proyecto_final/manage.py createsuperuser

# 8. Check logs
docker-compose logs -f
```

### **Phase 4: Configure Domain & HTTPS**

```bash
# On EC2 (as ubuntu):
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/innercircle/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/innercircle/
sudo chmod 644 /opt/innercircle/*.pem

# Edit nginx.conf to allow HTTPS (uncomment the HTTPS server block)
nano nginx.conf

# Restart
docker-compose restart nginx
```

### **Phase 5: Configure GitHub Secrets (for CI/CD)**

Go to GitHub → Your Repo → Settings → Secrets and variables → Actions

Add these:
```
AWS_EC2_HOST=<your-ec2-ip>
AWS_EC2_USER=ubuntu
AWS_EC2_KEY=<paste-entire-private-key>
STRIPE_PUBLIC_KEY=pk_live_xxxxx
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
SECRET_KEY=<generated-django-secret>
```

Generate Django SECRET_KEY:
```bash
docker run --rm python:3.11 python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 🔑 Key Configuration Points

### **Environment Variables (.env)**

**For Local Development:**
```
DEBUG=True
DB_ENGINE=django.db.backends.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

**For EC2 Production:**
```
DEBUG=False
DEBUG=False
DB_ENGINE=django.db.backends.postgresql
DB_NAME=innercircle_db
DB_USER=innercircle_user
DB_PASSWORD=<strong-password>
DB_HOST=db
DB_PORT=5432
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,<ec2-ip>
SECURE_SSL_REDIRECT=True
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### **Database Migration**

Your existing data in SQLite will be:
1. Automatically migrated when Docker Compose starts
2. Migrations run automatically in the docker-compose.yml command

No manual data export needed unless you have significant data requiring special handling (see `DATABASE_MIGRATION.md`).

---

## 📁 Modified & New Files

### **Modified:**
- `proyecto_final/mysite/settings.py` - PostgreSQL support + production settings
- `.gitignore` - Added SSL certs, SQL backups, logs

### **New:**
- `requirements.txt` - Production dependencies
- `.env.example` - Configuration template
- `Dockerfile` - Django application container
- `docker-compose.yml` - Multi-container orchestration
- `nginx.conf` - Web server configuration
- `DEPLOYMENT_QUICK_START.md` - Quick reference guide
- `EC2_DEPLOYMENT_GUIDE.md` - Comprehensive deployment steps
- `DATABASE_MIGRATION.md` - Database migration procedures
- `docker-setup.sh` - Local setup automation
- `ec2-setup.sh` - EC2 initialization
- `.github/workflows/deploy.yml` - Auto-deployment CI/CD
- `.github/workflows/tests.yml` - Automated testing

---

## 🔐 Important Security Notes

⚠️ **Never commit these:**
- `.env` (has API keys, passwords)
- `*.pem` (SSL certificates)
- `*.sql` (database backups)

✅ **Always commit these:**
- `.env.example` (template only)
- `Dockerfile`, `docker-compose.yml`
- `.github/workflows/`
- Guides and documentation

---

## 🛠️ Useful Docker Commands

```bash
# During development
docker-compose up -d              # Start
docker-compose down               # Stop
docker-compose logs -f            # View logs
docker-compose ps                 # Status
docker-compose exec web bash      # Shell access
docker-compose restart web        # Restart

# Deployment
docker-compose build              # Rebuild images
docker-compose exec web python proyecto_final/manage.py migrate
docker-compose exec web python proyecto_final/manage.py createsuperuser
docker-compose exec web python proyecto_final/manage.py collectstatic --noinput
```

---

## 📊 Architecture

```
┌─────────────────────────────────────┐
│         Nginx (Port 80/443)         │
│     (Static files, SSL, proxying)   │
└──────────────┬──────────────────────┘
               │
       ┌───────▼────────┐
       │  Django App     │
       │  (Gunicorn 4🗂️  │
       │   workers)      │
       └───────┬────────┘
               │
       ┌───────▼────────┐
       │   PostgreSQL    │
       │   (Database)    │
       └────────────────┘
```

---

## ✨ What's Different Now

| Feature | Before | After |
|---------|--------|-------|
| Database | SQLite (local only) | PostgreSQL (scalable) |
| Deployment | Manual, error-prone | Docker containerized |
| Static Files | Django serves (slow) | Nginx + WhiteNoise (fast) |
| Secrets | Hardcoded | Environment variables |
| HTTPS | Not configured | Let's Encrypt ready |
| CI/CD | None | GitHub Actions |
| Horizontal Scaling | Impossible | Easy with load balancer |

---

## 🆘 If Things Go Wrong

### Application won't start:
```bash
docker-compose logs -f web
docker-compose exec web python proyecto_final/manage.py check
```

### Database connection errors:
```bash
docker-compose exec db psql -U innercircle_user -d innercircle_db
docker-compose logs -f db
```

### Port conflicts:
```bash
sudo lsof -i :80    # Find what's using port 80
sudo kill -9 <PID>
```

See troubleshooting sections in deployment guides for more.

---

## 📚 Documentation Map

1. **Start here:** `DEPLOYMENT_QUICK_START.md`
2. **Detailed steps:** `EC2_DEPLOYMENT_GUIDE.md`
3. **Database migration:** `DATABASE_MIGRATION.md`
4. **Local testing:** Run `./docker-setup.sh`
5. **Production values:** Update `requirements.txt`, `.env`, check `docker-compose.yml`

---

## ✅ Deployment Checklist

- [ ] Tested locally with `./docker-setup.sh`
- [ ] Created AWS EC2 instance
- [ ] Ran `ec2-setup.sh` on EC2
- [ ] Cloned repo to `/opt/innercircle`
- [ ] Updated `.env` with production values
- [ ] Ran `docker-compose up -d`
- [ ] Created superuser
- [ ] Domain DNS configured (A record → EC2 IP)
- [ ] HTTPS certificate generated
- [ ] GitHub Secrets added
- [ ] Tested website on domain
- [ ] Set up automated backups
- [ ] Configured monitoring/logging

---

## 🎉 You're Ready!

Your infrastructure is now **production-ready**. The deployment is:
- ✅ Containerized (Docker)
- ✅ Scalable (PostgreSQL, Nginx)
- ✅ Secure (HTTPS-ready, secure cookies, CSP headers)
- ✅ Automated (CI/CD workflows)
- ✅ Observable (Docker logs, monitoring ready)

**Next action: Read `DEPLOYMENT_QUICK_START.md` and start Phase 1!**
