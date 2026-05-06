# 🚀 InnerCircle Deployment Quick Start

## Overview
This guide covers deploying InnerCircle from your local machine to AWS EC2 with PostgreSQL and Docker.

---

## 🏃 Quick Start (5 minutes)

### 1. **Local Testing with Docker**

```bash
# Clone your repo (already done)
cd /home/smartrent/Escritorio/InnerCircle

# Make setup scripts executable
chmod +x docker-setup.sh ec2-setup.sh

# Run local setup
./docker-setup.sh

# Application will be available at:
# - Web: http://localhost
# - Admin: http://localhost/admin
```

### 2. **Create AWS EC2 Instance**

- Go to AWS Console → EC2 → Launch Instance
- Select: **Ubuntu 24.04 LTS** or **Debian 12**
- Instance Type: `t3.micro` (free tier) or `t3.small` (better)
- Storage: 30GB  
- Security Group: Allow ports 22, 80, 443
- Create/use SSH key pair
- Launch!

### 3. **Setup EC2 & Deploy**

```bash
# 1. Connect to your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-public-ip

# 2. Run setup (as ubuntu user)
curl -O https://raw.githubusercontent.com/your-username/your-repo/main/ec2-setup.sh
chmod +x ec2-setup.sh
./ec2-setup.sh

# 3. Clone your repo
cd /opt/innercircle
git clone https://github.com/your-username/your-repo.git .

# 4. Configure environment
cp .env.example .env
nano .env

# 5. Start application
docker-compose up -d

# 6. Run migrations
docker-compose exec web python proyecto_final/manage.py migrate

# 7. Create superuser
docker-compose exec web python proyecto_final/manage.py createsuperuser
```

### 4. **Configure Domain & HTTPS**

```bash
# On EC2 as ubuntu user
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/innercircle/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/innercircle/
sudo chmod 644 /opt/innercircle/*.pem

# Uncomment HTTPS in nginx.conf
nano nginx.conf

# Restart nginx
docker-compose restart nginx
```

---

## 📋 Configuration Files

All files have been created in your project:

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variables template |
| `Dockerfile` | Docker image definition |
| `docker-compose.yml` | Multi-container orchestration |
| `nginx.conf` | Web server configuration |
| `EC2_DEPLOYMENT_GUIDE.md` | Detailed deployment steps |
| `DATABASE_MIGRATION.md` | SQLite → PostgreSQL migration |
| `.github/workflows/deploy.yml` | CI/CD deployment pipeline |
| `.github/workflows/tests.yml` | Automated testing |

---

## 🔧 Environment Variables (.env)

Create your `.env` file by copying `.env.example` and filling in:

**Essential for Production:**
```bash
DEBUG=False
SECRET_KEY=<generate-with-command-below>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,<ec2-ip>

# Generate secret key:
docker run --rm python:3.11 python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Database:**
```bash
DB_ENGINE=django.db.backends.postgresql
DB_NAME=innercircle_db
DB_USER=innercircle_user
DB_PASSWORD=<make-this-strong>
DB_HOST=db  # Use 'db' in Docker, localhost for local dev
DB_PORT=5432
```

**Stripe (from https://dashboard.stripe.com):**
```bash
STRIPE_PUBLIC_KEY=pk_live_xxxxx
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
```

**Email:**
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=<app-password>  # Not your regular password!
EMAIL_USE_TLS=True
```

---

## 📊 Docker Commands Reference

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f              # All logs
docker-compose logs -f web         # Django logs
docker-compose logs -f db          # Database logs
docker-compose logs -f nginx       # Nginx logs

# Access container shell
docker-compose exec web bash
docker-compose exec db psql -U innercircle_user innercircle_db

# Run management commands
docker-compose exec web python proyecto_final/manage.py migrate
docker-compose exec web python proyecto_final/manage.py createsuperuser
docker-compose exec web python proyecto_final/manage.py collectstatic

# Restart services
docker-compose restart web
docker-compose restart nginx

# Stop all
docker-compose down

# Clean up (removes volumes!)
docker-compose down -v
```

---

## 🔐 GitHub Secrets Setup

Add these to your GitHub repo (Settings → Secrets and variables → Actions):

```
AWS_EC2_HOST=<your-ec2-public-ip>
AWS_EC2_USER=ubuntu
AWS_EC2_KEY=<paste-your-private-ssh-key>

STRIPE_PUBLIC_KEY=<your-key>
STRIPE_SECRET_KEY=<your-key>
STRIPE_WEBHOOK_SECRET=<your-key>

EMAIL_HOST_USER=<your-email>
EMAIL_HOST_PASSWORD=<your-app-password>

SECRET_KEY=<your-django-secret-key>

SLACK_WEBHOOK=<optional-for-notifications>
```

---

## 🔄 Database Migration (SQLite → PostgreSQL)

```bash
# Local with Docker
./docker-setup.sh  # Automatically runs migrations

# Or manually:
docker-compose exec web python proyecto_final/manage.py migrate

# For EC2 (if migrating existing data):
docker-compose exec web python proyecto_final/manage.py dumpdata > backup.json
# Switch to PostgreSQL in .env
# Restart: docker-compose restart web
# Load: docker-compose exec web python proyecto_final/manage.py loaddata backup.json
```

See `DATABASE_MIGRATION.md` for detailed steps.

---

## 📝 Deployment Workflow

### **Option 1: Manual Deployment (Recommended for starting)**

```bash
# SSH into EC2
ssh ubuntu@your-ec2-ip

# Pull latest changes
cd /opt/innercircle
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d

# Run migrations
docker-compose exec web python proyecto_final/manage.py migrate

# Check logs
docker-compose logs -f web
```

### **Option 2: Automated with GitHub Actions (Advanced)**

Once configured, every push to `main` automatically:
1. ✅ Runs tests
2. ✅ Builds Docker image
3. ✅ Deploys to EC2
4. ✅ Runs migrations
5. ✅ Notifies you

Workflows are in `.github/workflows/`

---

## 🐛 Troubleshooting

### Application won't start
```bash
docker-compose logs -f web
docker-compose exec web python proyecto_final/manage.py check
```

### Database connection issues
```bash
docker-compose exec web python proyecto_final/manage.py dbshell
docker-compose logs -f db
```

### Static files not loading
```bash
docker-compose exec web python proyecto_final/manage.py collectstatic --noinput --clear
docker-compose restart nginx
```

### Port already in use
```bash
lsof -i :80       # Find what's using port 80
sudo kill -9 <PID>
```

---

## 📋 Pre-Deployment Checklist

- [ ] Created AWS EC2 instance
- [ ] Generated secure SECRET_KEY
- [ ] Filled in `.env` with all values
- [ ] Added GitHub Secrets
- [ ] Domain DNS configured (A record → EC2 IP)
- [ ] Stripe keys updated to production values
- [ ] Email credentials saved (Gmail app password, not regular password)
- [ ] SSH key saved locally (`chmod 600 your-key.pem`)
- [ ] Tested locally with Docker first
- [ ] Reviewed `EC2_DEPLOYMENT_GUIDE.md`

---

## 🔗 Useful Links

- [Django Deployment Guide](https://docs.djangoproject.com/en/6.0/howto/deployment/)
- [Docker Documentation](https://docs.docker.com/)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [Let's Encrypt](https://letsencrypt.org/)
- [Stripe API Documentation](https://stripe.com/docs/api)
- [Nginx Documentation](https://nginx.org/en/docs/)

---

## 💡 Next Steps

1. **Update GitHub** with all these deployment files:
   ```bash
   git add .
   git commit -m "Add deployment configuration (Docker, EC2, CI/CD)"
   git push origin main
   ```

2. **Test locally first** with `docker-compose up -d`

3. **Launch EC2 instance** and run `ec2-setup.sh`

4. **Verify everything works** before configuring CI/CD

---

**Questions? Check `EC2_DEPLOYMENT_GUIDE.md` for comprehensive details!**
