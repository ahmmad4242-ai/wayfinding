# أوامر نشر VPS جاهزة | Ready VPS Deployment Commands

## 🚀 دليل النشر السريع | Quick Deployment Guide

---

## المتطلبات الأساسية | Prerequisites

### على الـ VPS:
- Ubuntu 20.04+ أو Debian 11+
- Docker و Docker Compose مثبتان
- Port 80 و 443 متاحان
- نطاق (Domain) يشير إلى IP الخادم

---

## الخطوة 1: رفع الملفات إلى VPS | Step 1: Upload Files to VPS

### الطريقة الأولى: استخدام tar.gz

```bash
# على جهازك المحلي (Local):
# افترض أن لديك ملف: floor-plan-analyzer-deploy.tar.gz

# رفع الملف إلى VPS
scp floor-plan-analyzer-deploy.tar.gz root@YOUR_VPS_IP:/root/

# تسجيل الدخول للـ VPS
ssh root@YOUR_VPS_IP

# فك الضغط
cd /root
tar -xzf floor-plan-analyzer-deploy.tar.gz
cd floor-plan-analyzer
```

### الطريقة الثانية: استخدام Git Clone

```bash
# تسجيل الدخول للـ VPS
ssh root@YOUR_VPS_IP

# استنساخ المشروع من GitHub
cd /root
git clone https://github.com/YOUR_USERNAME/floor-plan-analyzer.git
cd floor-plan-analyzer
```

---

## الخطوة 2: تثبيت المتطلبات | Step 2: Install Dependencies

```bash
# تحديث النظام
sudo apt update && sudo apt upgrade -y

# تثبيت Docker (إذا لم يكن مثبتًا)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# تثبيت Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# التحقق من التثبيت
docker --version
docker-compose --version
```

---

## الخطوة 3: إعداد ملفات البيئة | Step 3: Configure Environment

```bash
# إنشاء ملف .env من النموذج
cd /root/floor-plan-analyzer
cp .env.example .env

# تحرير الإعدادات
nano .env
```

### محتوى .env:

```bash
# API Configuration
FPA_ENV=production
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Domain & SSL
DOMAIN=your-domain.com
LETSENCRYPT_EMAIL=your-email@example.com

# Security
SECRET_KEY=your-random-secret-key-here-generate-32-chars
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Database (if needed)
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=floorplan_db
# DB_USER=floorplan_user
# DB_PASSWORD=secure_password_here

# Paths
UPLOAD_DIR=/app/data/uploads
OUTPUT_DIR=/app/data/outputs
MODELS_DIR=/app/models

# Analysis Settings
MAX_FILE_SIZE_MB=50
DEFAULT_SCALE=100
DEFAULT_AGENTS=100

# Academic Analysis Settings
ENABLE_SPACE_SYNTAX=true
ENABLE_VGA=true
ENABLE_AGENT_SIMULATION=true
ENABLE_HEATMAPS=true
VGA_SAMPLE_LIMIT=5000
SIMULATION_AGENTS_PER_SCENARIO=50
```

احفظ الملف: `Ctrl+O`, ثم `Enter`, ثم `Ctrl+X`

---

## الخطوة 4: بناء الحاويات | Step 4: Build Containers

```bash
# بناء صورة Docker
cd /root/floor-plan-analyzer
docker-compose build

# التحقق من الصور المبنية
docker images | grep floor-plan
```

---

## الخطوة 5: تشغيل النظام | Step 5: Start the System

```bash
# تشغيل جميع الخدمات
docker-compose up -d

# التحقق من الحاويات الجارية
docker-compose ps

# يجب أن ترى:
# - floor-plan-api (port 8000)
# - nginx (port 80, 443)
```

---

## الخطوة 6: إعداد Nginx و SSL | Step 6: Configure Nginx & SSL

### تثبيت Certbot (Let's Encrypt)

```bash
# تثبيت Certbot
sudo apt install certbot python3-certbot-nginx -y

# الحصول على شهادة SSL
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# التحقق من التجديد التلقائي
sudo certbot renew --dry-run
```

### إعداد Nginx (إذا لم يكن في Docker Compose)

```bash
# إنشاء ملف تكوين Nginx
sudo nano /etc/nginx/sites-available/floor-plan-analyzer
```

```nginx
# HTTP → HTTPS Redirect
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com www.your-domain.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS Server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Client Upload Limits
    client_max_body_size 100M;
    client_body_timeout 300s;

    # Frontend (Static Files)
    location / {
        root /root/floor-plan-analyzer/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API Backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long analysis
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # API Docs
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:8000/redoc;
        proxy_set_header Host $host;
    }

    # Health Check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
    }
}
```

```bash
# تفعيل الإعدادات
sudo ln -s /etc/nginx/sites-available/floor-plan-analyzer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## الخطوة 7: التحقق من النشر | Step 7: Verify Deployment

### فحص الحالة

```bash
# فحص صحة API
curl http://localhost:8000/health

# يجب أن ترى:
# {"status":"healthy","message":"System is operational","version":"1.0.0"}

# فحص عبر الإنترنت
curl https://your-domain.com/health

# فحص السجلات
docker-compose logs -f api

# فحص استهلاك الموارد
docker stats
```

### الوصول للنظام

- **الواجهة الأمامية**: `https://your-domain.com`
- **API Docs**: `https://your-domain.com/docs`
- **ReDoc**: `https://your-domain.com/redoc`
- **Health Check**: `https://your-domain.com/health`

---

## الخطوة 8: أوامر الصيانة | Step 8: Maintenance Commands

### إيقاف وتشغيل

```bash
# إيقاف النظام
cd /root/floor-plan-analyzer
docker-compose down

# تشغيل النظام
docker-compose up -d

# إعادة تشغيل
docker-compose restart
```

### تحديث النظام

```bash
# سحب آخر التحديثات من GitHub
cd /root/floor-plan-analyzer
git pull origin main

# إعادة بناء الحاويات
docker-compose down
docker-compose build
docker-compose up -d
```

### النسخ الاحتياطي

```bash
# نسخ احتياطي للبيانات
cd /root
tar -czf floor-plan-backup-$(date +%Y%m%d).tar.gz \
    floor-plan-analyzer/data/ \
    floor-plan-analyzer/.env

# نقل النسخة الاحتياطية لمكان آمن
scp floor-plan-backup-*.tar.gz user@backup-server:/backups/
```

### تنظيف المساحة

```bash
# حذف الصور غير المستخدمة
docker image prune -a

# حذف الحاويات المتوقفة
docker container prune

# حذف الملفات المؤقتة
rm -rf /root/floor-plan-analyzer/data/uploads/*
rm -rf /root/floor-plan-analyzer/data/outputs/*
```

### عرض السجلات

```bash
# سجلات API
docker-compose logs -f api

# سجلات Nginx (خارج Docker)
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# سجلات النظام
journalctl -u docker -f
```

---

## الخطوة 9: المراقبة | Step 9: Monitoring

### تثبيت أدوات المراقبة (اختياري)

```bash
# تثبيت htop للمراقبة
sudo apt install htop -y
htop

# تثبيت netdata للمراقبة المتقدمة
bash <(curl -Ss https://my-netdata.io/kickstart.sh)

# الوصول لـ Netdata
# http://YOUR_VPS_IP:19999
```

### إعداد تنبيهات (اختياري)

يمكنك إعداد تنبيهات عبر:
- **Email**: باستخدام Postfix
- **Telegram**: باستخدام بوت Telegram
- **Slack**: باستخدام Webhooks

---

## الخطوة 10: الأمان | Step 10: Security Hardening

### جدار الحماية

```bash
# تثبيت UFW
sudo apt install ufw -y

# السماح بالخدمات الأساسية فقط
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# تفعيل الجدار
sudo ufw enable

# التحقق من الحالة
sudo ufw status
```

### تأمين SSH

```bash
# تحرير إعدادات SSH
sudo nano /etc/ssh/sshd_config

# غيّر الإعدادات التالية:
# PermitRootLogin no
# PasswordAuthentication no  # (بعد إعداد مفاتيح SSH)
# Port 2222  # (غيّر المنفذ الافتراضي)

# إعادة تشغيل SSH
sudo systemctl restart sshd
```

### تحديثات تلقائية

```bash
# تثبيت unattended-upgrades
sudo apt install unattended-upgrades -y

# تفعيل التحديثات التلقائية
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

---

## استكشاف الأخطاء | Troubleshooting

### المشكلة 1: API لا يستجيب

```bash
# فحص حالة الحاوية
docker-compose ps

# فحص السجلات
docker-compose logs api

# إعادة تشغيل
docker-compose restart api
```

### المشكلة 2: خطأ في الذاكرة

```bash
# فحص الذاكرة المتاحة
free -h

# زيادة Swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### المشكلة 3: بطء التحليل

```bash
# زيادة عدد Workers
# في .env:
API_WORKERS=8

# تقليل حد العينات
VGA_SAMPLE_LIMIT=3000
SIMULATION_AGENTS_PER_SCENARIO=30

# إعادة تشغيل
docker-compose restart
```

### المشكلة 4: خطأ SSL

```bash
# تجديد الشهادة يدويًا
sudo certbot renew --force-renewal

# إعادة تشغيل Nginx
sudo systemctl restart nginx
```

---

## أوامر سريعة مجمّعة | Quick Commands Summary

```bash
# النشر الكامل (من الصفر)
ssh root@YOUR_VPS_IP
cd /root
git clone https://github.com/YOUR_USERNAME/floor-plan-analyzer.git
cd floor-plan-analyzer
cp .env.example .env
nano .env  # تحرير الإعدادات
docker-compose build
docker-compose up -d
sudo certbot --nginx -d your-domain.com

# التحقق
curl http://localhost:8000/health
curl https://your-domain.com/health

# المراقبة
docker-compose logs -f api
docker stats

# التحديث
cd /root/floor-plan-analyzer
git pull
docker-compose down
docker-compose build
docker-compose up -d

# النسخ الاحتياطي
tar -czf backup-$(date +%Y%m%d).tar.gz floor-plan-analyzer/

# التنظيف
docker system prune -a
rm -rf /root/floor-plan-analyzer/data/uploads/*
```

---

## 📞 الدعم | Support

إذا واجهت أي مشاكل:

1. **فحص السجلات**: `docker-compose logs -f`
2. **فحص الوثائق**: `README_AR.md`, `ACADEMIC_METHODOLOGY.md`
3. **فحص Issues على GitHub**: `github.com/YOUR_USERNAME/floor-plan-analyzer/issues`
4. **إنشاء Issue جديد** مع تفاصيل المشكلة

---

## ✅ قائمة التحقق | Deployment Checklist

- [ ] VPS جاهز بـ Ubuntu/Debian
- [ ] Docker و Docker Compose مثبتان
- [ ] النطاق يشير إلى IP الصحيح
- [ ] الملفات مرفوعة (Git أو tar.gz)
- [ ] ملف .env مُعدّل بالقيم الصحيحة
- [ ] الحاويات تعمل: `docker-compose ps`
- [ ] API يستجيب: `curl /health`
- [ ] SSL مُعدّ بـ Certbot
- [ ] Nginx يعمل بشكل صحيح
- [ ] جدار الحماية مفعّل
- [ ] النسخ الاحتياطي مجدول
- [ ] المراقبة مفعّلة
- [ ] الواجهة الأمامية تعمل
- [ ] API Docs متاحة: `/docs`

---

*تمت كتابة هذا الدليل لضمان نشر سريع وآمن على VPS. جميع الأوامر مختبرة على Ubuntu 20.04 LTS.*

*This guide is written to ensure quick and secure VPS deployment. All commands are tested on Ubuntu 20.04 LTS.*
