# InnerCircle AWS EC2 Deployment Guide

## Prerequisites
- AWS Account with EC2 access
- GitHub repository with your code
- Domain name (optional for production)
- SSL Certificate (can use Let's Encrypt/certbot)

## Step 1: Launch EC2 Instance

### Instance Configuration:
- **AMI**: Ubuntu 24.04 LTS (or Debian 12)
- **Instance Type**: t3.micro (free tier) or t3.small for better performance
- **Storage**: 30GB EBS (gp3)
- **Security Group**: 
  - Allow SSH (22) from your IP
  - Allow HTTP (80) from anywhere
  - Allow HTTPS (443) from anywhere
  - Allow PostgreSQL (5432) from EC2 security group (internal only)

### Network Configuration:
- Enable public IP
- Use VPC default or create custom
- Configure elastic IP (optional but recommended)

## Step 2: Connect to EC2

```bash
# SSH into your instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Or if you have the key file path configured:
ssh ubuntu@your-ec2-ip
```

## Step 3: Initial Setup

```bash
# Download and run setup script
cd /tmp
wget https://raw.githubusercontent.com/your-repo/main/ec2-setup.sh
chmod +x ec2-setup.sh
./ec2-setup.sh

# Or do it manually:
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y docker.io docker-compose curl git
sudo usermod -aG docker $USER
newgrp docker
```

## Step 4: Clone and Configure

```bash
cd /opt
sudo mkdir innercircle
sudo chown $USER:$USER innercircle
cd innercircle

# Clone your repository
git clone https://github.com/your-username/your-repo.git .

# Copy and edit environment file
cp .env.example .env
nano .env
```

### Required .env Variables:
```
# Production settings
DEBUG=False
SECRET_KEY=generate-a-secure-key-using-django
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your-ec2-ip

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=innercircle_db
DB_USER=innercircle_user
DB_PASSWORD=your-strong-password-here
DB_HOST=db
DB_PORT=5432

# Stripe API Keys
STRIPE_PUBLIC_KEY=pk_live_xxxxx
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@innercircle.com

# Optional: HTTPS/SSL
SECURE_SSL_REDIRECT=True
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Step 5: Generate Secure Django Secret Key

```bash
docker run --rm python:3.11 python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Step 6: Start Application

```bash
# Build and start containers
docker-compose up -d

# View logs
docker-compose logs -f

# Run migrations
docker-compose exec web python proyecto_final/manage.py migrate

# Create superuser
docker-compose exec web python proyecto_final/manage.py createsuperuser

# Collect static files (should happen automatically)
docker-compose exec web python proyecto_final/manage.py collectstatic --noinput
```

## Step 7: Configure Domain & DNS

1. Go to your domain registrar
2. Update DNS A record to point to your EC2 public IP
3. Test DNS resolution: `nslookup yourdomain.com`

## Step 8: Setup SSL Certificate (HTTPS)

### Using Let's Encrypt with Certbot (recommended):

```bash
# SSH into EC2
ssh ubuntu@your-ec2-ip

# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates to your app volume
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/innercircle/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/innercircle/
sudo chown $USER:$USER /opt/innercircle/*.pem
```

### Update nginx.conf with SSL:

Uncomment the HTTPS server block in `nginx.conf` and update paths:
```nginx
ssl_certificate /etc/nginx/ssl/fullchain.pem;
ssl_certificate_key /etc/nginx/ssl/privkey.pem;
```

Restart nginx:
```bash
docker-compose restart nginx
```

### Auto-renew SSL Certificate:

```bash
# Create renewal script
cat > /home/ubuntu/renew-ssl.sh << 'EOF'
#!/bin/bash
sudo certbot renew --quiet
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/innercircle/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/innercircle/
sudo chown ubuntu:ubuntu /opt/innercircle/*.pem
docker-compose -C /opt/innercircle restart nginx
EOF

chmod +x /home/ubuntu/renew-ssl.sh

# Add to crontab (runs every 60 days)
crontab -e
# Add: 0 3 * * 0 /home/ubuntu/renew-ssl.sh
```

## Step 9: GitHub Secrets Setup (for CI/CD)

Add these secrets to your GitHub repository settings (Settings → Secrets):

```
AWS_EC2_HOST=your-ec2-ip
AWS_EC2_USER=ubuntu
AWS_EC2_KEY=<your-private-ssh-key>
AWS_REGION=us-east-1

DB_NAME=innercircle_db
DB_USER=innercircle_user
DB_PASSWORD=<your-strong-password>

STRIPE_PUBLIC_KEY=pk_live_xxxxx
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=<your-app-password>

SECRET_KEY=<your-django-secret-key>
```

## Step 10: Backup Database

```bash
# Manual backup
docker-compose exec -T db pg_dump -U innercircle_user innercircle_db > backup.sql

# Restore from backup
cat backup.sql | docker-compose exec -T db psql -U innercircle_user innercircle_db

# Scheduled daily backup (crontab)
# 2 0 * * * docker-compose -C /opt/innercircle exec -T db pg_dump -U innercircle_user innercircle_db > /backup/innercircle-$(date +\%Y-\%m-\%d).sql
```

## Step 11: Monitoring & Maintenance

### View Logs:
```bash
docker-compose logs -f                 # All services
docker-compose logs -f web            # Django app only
docker-compose logs -f db             # Database only
docker-compose logs -f nginx          # Nginx only
```

### Check Container Status:
```bash
docker-compose ps
```

### Update Application (new deployment):
```bash
cd /opt/innercircle
git pull origin main
docker-compose build
docker-compose up -d
docker-compose exec web python proyecto_final/manage.py migrate
```

### Monitor Resources:
```bash
# Check disk usage
df -h

# Check memory usage
free -h

# Docker stats
docker stats
```

## Troubleshooting

### Application won't start:
```bash
docker-compose logs -f web
docker-compose exec web python proyecto_final/manage.py check
```

### Database connection issues:
```bash
docker-compose exec web python proyecto_final/manage.py dbshell
docker-compose logs -f db
```

### Static files not loading:
```bash
docker-compose exec web python proyecto_final/manage.py collectstatic --noinput --clear
docker-compose exec web python proyecto_final/manage.py compress
```

### Out of memory:
```bash
# Increase EC2 instance size from AWS console
# Or clean up Docker:
docker system prune -a
docker volume prune
```

## Production Checklist

- [ ] DEBUG = False in .env
- [ ] SECRET_KEY is securely generated
- [ ] ALLOWED_HOSTS configured correctly
- [ ] HTTPS/SSL configured and working
- [ ] Database backups configured
- [ ] Email configuration verified
- [ ] Stripe keys updated to production
- [ ] Rate limiting configured in nginx
- [ ] Logs being monitored
- [ ] Domain pointing to EC2 IP
- [ ] UFW firewall configured
- [ ] Elastic IP attached (recommended)

## Additional Resources

- Django Deployment: https://docs.djangoproject.com/en/6.0/howto/deployment/
- Docker Docs: https://docs.docker.com/
- Let's Encrypt: https://letsencrypt.org/
- AWS EC2 Docs: https://docs.aws.amazon.com/ec2/
