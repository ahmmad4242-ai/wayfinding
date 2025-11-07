# 🚀 دليل النشر على VPS

## معلومات الخادم

**الخادم (VPS):**
- IP: `77.37.35.25`
- النطاقات: `flows.aqeeli.com`, `wfapi.aqeeli.com`
- نظام التشغيل: Ubuntu/Debian
- المنفذ: 22 (SSH)

**المتطلبات:**
- Docker 20.10+
- Docker Compose v2+
- 4GB RAM (على الأقل)
- 20GB مساحة تخزين

---

## خطوات النشر التفصيلية

### 1️⃣ الاتصال بالـ VPS

```bash
# باستخدام المفتاح الخاص
ssh -i /path/to/private/key root@77.37.35.25

# أو إذا كان المفتاح مضافاً لـ ssh-agent
ssh root@77.37.35.25
```

### 2️⃣ تثبيت المتطلبات الأساسية

```bash
# تحديث النظام
apt-get update && apt-get upgrade -y

# تثبيت Docker
curl -fsSL https://get.docker.com | bash

# تثبيت Docker Compose
apt-get install docker-compose-plugin -y

# التحقق من التثبيت
docker --version
docker compose version

# إضافة المستخدم الحالي لمجموعة docker (إذا لم تكن root)
usermod -aG docker $USER
```

### 3️⃣ نقل الملفات للـ VPS

**من جهازك المحلي (خارج SSH):**

```bash
# انتقل لمجلد المشروع
cd /home/user/webapp/floor-plan-analyzer

# ضغط المشروع
tar -czf fpa.tar.gz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' .

# نقل للـ VPS
scp -i /path/to/private/key fpa.tar.gz root@77.37.35.25:/root/

# أو استخدام rsync (أسرع للتحديثات)
rsync -avz -e "ssh -i /path/to/private/key" \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='data/' \
  ./ root@77.37.35.25:/root/floor-plan-analyzer/
```

### 4️⃣ إعداد المشروع على VPS

```bash
# عودة للـ SSH على VPS
ssh root@77.37.35.25

# إنشاء مجلد النشر
mkdir -p /opt/floor-plan-analyzer
cd /opt/floor-plan-analyzer

# فك الضغط (إذا استخدمت tar)
tar -xzf /root/fpa.tar.gz -C /opt/floor-plan-analyzer/

# أو إذا استخدمت rsync، الملفات موجودة بالفعل
```

### 5️⃣ إعداد ملف البيئة (.env)

```bash
# نسخ ملف المثال
cp .env.example .env

# تعديل الإعدادات
nano .env
```

**إعدادات مهمة يجب تغييرها:**

```env
# Database - قم بتغيير كلمة المرور
DB_PASSWORD=ضع_كلمة_سر_قوية_هنا_123

# Security - قم بتوليد مفتاح آمن
SECRET_KEY=توليد_مفتاح_عشوائي_طويل_هنا

# API
API_WORKERS=4
MAX_CONCURRENT_JOBS=5

# Allowed Origins
ALLOWED_ORIGINS=https://flows.aqeeli.com,https://wfapi.aqeeli.com,http://77.37.35.25

# OCR Settings
TESSERACT_LANG=ara+eng
ENABLE_EASYOCR=true
```

**لتوليد SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 6️⃣ إنشاء المجلدات المطلوبة

```bash
mkdir -p /opt/floor-plan-analyzer/data/{uploads,outputs,cache}
mkdir -p /opt/floor-plan-analyzer/models
mkdir -p /opt/backups/floor-plan-analyzer

# تعيين الصلاحيات
chmod -R 755 /opt/floor-plan-analyzer
chmod 600 /opt/floor-plan-analyzer/.env
```

### 7️⃣ النشر باستخدام السكريبت

```bash
cd /opt/floor-plan-analyzer

# تشغيل سكريبت النشر
sudo ./infra/deploy.sh
```

**سيقوم السكريبت بـ:**
- ✅ إنشاء نسخة احتياطية من النشر السابق (إن وجد)
- ✅ نسخ الملفات للموقع الصحيح
- ✅ بناء صور Docker
- ✅ تشغيل جميع الخدمات (API, Database, Redis)
- ✅ التحقق من الصحة

### 8️⃣ التحقق من النشر

```bash
# فحص حالة الحاويات
docker ps

# يجب أن ترى:
# - fpa_api (running)
# - fpa_database (running)
# - fpa_redis (running)

# فحص الصحة
curl http://localhost:8000/health

# عرض Logs
docker logs -f fpa_api
```

**النتيجة المتوقعة:**
```json
{
  "status": "healthy",
  "message": "System is operational",
  "version": "1.0.0"
}
```

---

## إعداد النطاق (Domain) و SSL

### 9️⃣ إعداد DNS

تأكد من أن النطاقات تشير للـ IP:

```
A Record: flows.aqeeli.com → 77.37.35.25
A Record: wfapi.aqeeli.com → 77.37.35.25
```

### 🔟 تثبيت Nginx

```bash
# تثبيت Nginx
apt-get install nginx -y

# إنشاء ملف الإعدادات
nano /etc/nginx/sites-available/floor-plan-analyzer
```

**محتوى الملف:**

```nginx
upstream fpa_backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name flows.aqeeli.com wfapi.aqeeli.com;
    
    client_max_body_size 50M;
    client_body_timeout 300s;
    
    location / {
        proxy_pass http://fpa_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    location /static/ {
        alias /opt/floor-plan-analyzer/frontend/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# تفعيل الموقع
ln -s /etc/nginx/sites-available/floor-plan-analyzer /etc/nginx/sites-enabled/

# اختبار الإعدادات
nginx -t

# إعادة تشغيل Nginx
systemctl restart nginx
```

### 1️⃣1️⃣ إعداد SSL باستخدام Certbot

```bash
# تثبيت Certbot
apt-get install certbot python3-certbot-nginx -y

# الحصول على شهادة SSL
certbot --nginx -d flows.aqeeli.com -d wfapi.aqeeli.com

# اختبار التجديد التلقائي
certbot renew --dry-run
```

سيطلب منك:
1. إدخال البريد الإلكتروني
2. الموافقة على الشروط
3. اختيار إعادة التوجيه HTTPS

---

## الاختبار النهائي

```bash
# اختبار HTTP (قبل SSL)
curl http://flows.aqeeli.com/health

# اختبار HTTPS (بعد SSL)
curl https://flows.aqeeli.com/health

# اختبار رفع ملف
curl -X POST https://flows.aqeeli.com/api/analyze \
  -F "file=@test_plan.pdf" \
  -F "building_type=hospital"
```

---

## إدارة الخدمة

### عرض Logs

```bash
# Logs مباشرة
docker logs -f fpa_api

# آخر 100 سطر
docker logs --tail=100 fpa_api

# جميع الخدمات
docker-compose -f /opt/floor-plan-analyzer/docker-compose.yml logs -f
```

### إعادة التشغيل

```bash
cd /opt/floor-plan-analyzer

# إعادة تشغيل خدمة واحدة
docker-compose restart api

# إعادة تشغيل الكل
docker-compose restart

# إيقاف وإعادة تشغيل
docker-compose down && docker-compose up -d
```

### التحديث

```bash
# باستخدام سكريبت التحديث
cd /opt/floor-plan-analyzer
./infra/update.sh

# أو يدوياً
git pull  # إذا كنت تستخدم git
docker-compose build --no-cache
docker-compose up -d --no-deps api
```

### النسخ الاحتياطي

```bash
# نسخ احتياطي للقاعدة
docker exec fpa_database pg_dump -U fpa_user fpa_db > /opt/backups/floor-plan-analyzer/db_$(date +%Y%m%d).sql

# نسخ احتياطي للبيانات
tar -czf /opt/backups/floor-plan-analyzer/data_$(date +%Y%m%d).tar.gz /opt/floor-plan-analyzer/data/

# نسخ احتياطي كامل
tar -czf /opt/backups/floor-plan-analyzer/full_$(date +%Y%m%d).tar.gz /opt/floor-plan-analyzer/
```

### الاستعادة

```bash
# استعادة القاعدة
docker exec -i fpa_database psql -U fpa_user fpa_db < /opt/backups/floor-plan-analyzer/db_20241107.sql

# استعادة البيانات
tar -xzf /opt/backups/floor-plan-analyzer/data_20241107.tar.gz -C /
```

---

## المراقبة

### استخدام الموارد

```bash
# استخدام Docker
docker stats

# استخدام النظام
htop

# مساحة القرص
df -h
du -sh /opt/floor-plan-analyzer/data/*
```

### Health Checks

```bash
# API
curl -f https://flows.aqeeli.com/health || echo "API Down"

# Database
docker exec fpa_database pg_isready -U fpa_user

# Redis
docker exec fpa_redis redis-cli ping
```

### إعداد Cron للمراقبة

```bash
# تعديل crontab
crontab -e

# إضافة:
# فحص الصحة كل 5 دقائق
*/5 * * * * curl -f https://flows.aqeeli.com/health || systemctl restart docker

# نسخ احتياطي يومي في 2 صباحاً
0 2 * * * docker exec fpa_database pg_dump -U fpa_user fpa_db > /opt/backups/floor-plan-analyzer/db_$(date +\%Y\%m\%d).sql

# تنظيف النسخ الاحتياطية القديمة (أكبر من 30 يوم)
0 3 * * * find /opt/backups/floor-plan-analyzer -type f -mtime +30 -delete
```

---

## استكشاف الأخطاء

### المشكلة: لا يمكن الوصول للـ API

```bash
# 1. فحص الحاويات
docker ps -a

# 2. فحص Logs
docker logs fpa_api

# 3. فحص المنفذ
netstat -tulpn | grep 8000

# 4. فحص Nginx
systemctl status nginx
nginx -t

# 5. فحص Firewall
ufw status
ufw allow 80/tcp
ufw allow 443/tcp
```

### المشكلة: خطأ في Database

```bash
# فحص حالة Database
docker logs fpa_database

# إعادة تشغيل Database
docker-compose restart db

# التحقق من الاتصال
docker exec -it fpa_database psql -U fpa_user -d fpa_db -c "SELECT 1;"
```

### المشكلة: نفاذ الذاكرة

```bash
# فحص الذاكرة
free -h

# زيادة حد الذاكرة في docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 4G
```

### المشكلة: بطء التحليل

```bash
# تقليل MAX_CONCURRENT_JOBS في .env
MAX_CONCURRENT_JOBS=3

# زيادة عدد Workers
API_WORKERS=6

# تنظيف Cache
docker exec fpa_redis redis-cli FLUSHALL
```

---

## أوامر مفيدة سريعة

```bash
# حالة الخدمة
cd /opt/floor-plan-analyzer && docker-compose ps

# Logs مباشرة
docker logs -f fpa_api

# دخول للحاوية
docker exec -it fpa_api bash

# قاعدة البيانات
docker exec -it fpa_database psql -U fpa_user -d fpa_db

# إيقاف الكل
docker-compose down

# تشغيل الكل
docker-compose up -d

# إعادة بناء وتشغيل
docker-compose up -d --build
```

---

## الدعم

للمساعدة أو الإبلاغ عن مشاكل:
- 📧 البريد الإلكتروني: support@example.com
- 🐛 GitHub Issues: [رابط المشروع]
- 📖 التوثيق الكامل: README_AR.md

---

تم إعداد هذا الدليل بواسطة فريق محلل مخططات الطوابق © 2024
