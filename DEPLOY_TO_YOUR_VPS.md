# 🎯 تعليمات النشر على VPS الخاص بك

## معلومات الخادم

```
IP: 77.37.35.25
Domains: flows.aqeeli.com, wfapi.aqeeli.com
Port: 22
User: root
Auth: ED25519 Private Key
```

---

## الخطوات التنفيذية

### 1️⃣ نقل المشروع للـ VPS

**من جهازك الحالي (Genspark Sandbox):**

```bash
# إنشاء ملف مضغوط
cd /home/user/webapp
tar -czf fpa-deploy.tar.gz \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='data/*' \
  floor-plan-analyzer/

# المسار النهائي: /home/user/webapp/fpa-deploy.tar.gz
```

**نقل للـ VPS باستخدام SCP:**

```bash
# استبدل /path/to/your/key بمسار المفتاح الخاص
scp -i /path/to/your/ed25519/key \
  fpa-deploy.tar.gz \
  root@77.37.35.25:/root/
```

---

### 2️⃣ الاتصال بالـ VPS

```bash
ssh -i /path/to/your/ed25519/key root@77.37.35.25
```

---

### 3️⃣ تثبيت Docker (إذا لم يكن مثبتاً)

```bash
# تحديث النظام
apt-get update && apt-get upgrade -y

# تثبيت Docker
curl -fsSL https://get.docker.com | bash

# تثبيت Docker Compose
apt-get install docker-compose-plugin -y

# التحقق
docker --version
docker compose version
```

**النتيجة المتوقعة:**
```
Docker version 24.0+
Docker Compose version v2.20+
```

---

### 4️⃣ إعداد المشروع

```bash
# إنشاء مجلد النشر
mkdir -p /opt/floor-plan-analyzer
cd /opt/floor-plan-analyzer

# فك الضغط
tar -xzf /root/fpa-deploy.tar.gz --strip-components=1

# إنشاء المجلدات المطلوبة
mkdir -p data/{uploads,outputs,cache}
mkdir -p models
mkdir -p /opt/backups/floor-plan-analyzer

# نسخ ملف البيئة
cp .env.example .env
```

---

### 5️⃣ تعديل ملف البيئة

```bash
nano .env
```

**غيّر هذه القيم الأساسية:**

```env
# Database Password - قم بتغييرها لكلمة سر قوية
DB_PASSWORD=AqEeLi_FPA_2024_Strong_Pass!@#

# Secret Key - قم بتوليد مفتاح عشوائي
SECRET_KEY=استخدم_الأمر_التالي_لتوليد_مفتاح

# Allowed Origins - أضف نطاقاتك
ALLOWED_ORIGINS=https://flows.aqeeli.com,https://wfapi.aqeeli.com,http://77.37.35.25

# API Workers (حسب موارد VPS)
API_WORKERS=4

# Max Concurrent Jobs
MAX_CONCURRENT_JOBS=5
```

**لتوليد SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**انسخ الناتج وضعه في SECRET_KEY**

**احفظ الملف:**
```
Ctrl + O  (Save)
Enter
Ctrl + X  (Exit)
```

---

### 6️⃣ النشر

```bash
# التأكد من الأذونات
chmod +x infra/deploy.sh infra/update.sh

# تشغيل سكريبت النشر
sudo ./infra/deploy.sh
```

**سيستغرق 3-5 دقائق للتحميل والبناء...**

**النتيجة المتوقعة:**
```
============================================
✅ Deployment completed successfully!
============================================

API URL: http://77.37.35.25:8000
Docs: http://77.37.35.25:8000/api/docs
```

---

### 7️⃣ التحقق من النشر

```bash
# فحص الحاويات
docker ps

# يجب أن ترى 3 حاويات:
# - fpa_api (Up)
# - fpa_database (Up, healthy)
# - fpa_redis (Up, healthy)

# فحص الصحة
curl http://localhost:8000/health

# النتيجة المتوقعة:
# {"status":"healthy","message":"System is operational","version":"1.0.0"}

# عرض Logs
docker logs --tail=50 fpa_api
```

---

### 8️⃣ إعداد Nginx للنطاقات

```bash
# تثبيت Nginx
apt-get install nginx -y

# إنشاء ملف الإعدادات
nano /etc/nginx/sites-available/floor-plan-analyzer
```

**انسخ هذه الإعدادات:**

```nginx
upstream fpa_backend {
    server localhost:8000;
    keepalive 64;
}

server {
    listen 80;
    server_name flows.aqeeli.com wfapi.aqeeli.com 77.37.35.25;
    
    # زيادة حجم الرفع
    client_max_body_size 50M;
    client_body_buffer_size 128k;
    client_body_timeout 300s;
    
    # Logging
    access_log /var/log/nginx/fpa-access.log;
    error_log /var/log/nginx/fpa-error.log;
    
    # Main API
    location / {
        proxy_pass http://fpa_backend;
        proxy_http_version 1.1;
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        
        # Timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Buffering
        proxy_buffering off;
    }
    
    # Static files
    location /static/ {
        alias /opt/floor-plan-analyzer/frontend/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**احفظ وفعّل:**

```bash
# تفعيل الموقع
ln -s /etc/nginx/sites-available/floor-plan-analyzer /etc/nginx/sites-enabled/

# حذف الموقع الافتراضي (اختياري)
rm /etc/nginx/sites-enabled/default

# اختبار الإعدادات
nginx -t

# إعادة تشغيل Nginx
systemctl restart nginx
systemctl enable nginx

# فحص الحالة
systemctl status nginx
```

---

### 9️⃣ إعداد SSL (Certbot)

```bash
# تثبيت Certbot
apt-get install certbot python3-certbot-nginx -y

# الحصول على شهادة SSL
certbot --nginx -d flows.aqeeli.com -d wfapi.aqeeli.com

# سيطلب منك:
# 1. البريد الإلكتروني: [أدخل بريدك]
# 2. الموافقة على الشروط: Y
# 3. إعادة التوجيه HTTPS: 2 (Redirect)

# اختبار التجديد التلقائي
certbot renew --dry-run
```

---

### 🔟 الاختبار النهائي

```bash
# من داخل VPS
curl https://flows.aqeeli.com/health

# من متصفحك
https://flows.aqeeli.com
https://flows.aqeeli.com/api/docs

# اختبار رفع ملف
curl -X POST https://flows.aqeeli.com/api/analyze \
  -F "file=@test.pdf" \
  -F "building_type=hospital" \
  -F "enable_color_analysis=true"
```

**إذا نجح كل شيء، ستحصل على:**
```json
{
  "job_id": "uuid-here",
  "status": "processing",
  "message": "تم استلام الملف وبدأ التحليل"
}
```

---

## 🔧 الإدارة اليومية

### عرض الإحصائيات
```bash
# استخدام الموارد
docker stats

# مساحة القرص
df -h
du -sh /opt/floor-plan-analyzer/data/*

# عدد الملفات المرفوعة
ls -l /opt/floor-plan-analyzer/data/uploads/ | wc -l
```

### Logs
```bash
# Logs مباشرة
docker logs -f fpa_api

# آخر 100 سطر
docker logs --tail=100 fpa_api

# Nginx logs
tail -f /var/log/nginx/fpa-access.log
tail -f /var/log/nginx/fpa-error.log
```

### إعادة التشغيل
```bash
cd /opt/floor-plan-analyzer

# خدمة واحدة
docker-compose restart api

# جميع الخدمات
docker-compose restart
```

### التحديث
```bash
cd /opt/floor-plan-analyzer

# استلام ملفات جديدة (عبر scp)
# ثم:
./infra/update.sh
```

### النسخ الاحتياطي
```bash
# نسخ احتياطي للقاعدة
docker exec fpa_database pg_dump -U fpa_user fpa_db > \
  /opt/backups/floor-plan-analyzer/db_$(date +%Y%m%d).sql

# نسخ احتياطي للبيانات
tar -czf /opt/backups/floor-plan-analyzer/data_$(date +%Y%m%d).tar.gz \
  /opt/floor-plan-analyzer/data/
```

### النسخ الاحتياطي التلقائي
```bash
# إضافة لـ crontab
crontab -e

# أضف هذه الأسطر:
# نسخ احتياطي يومي في 2 صباحاً
0 2 * * * docker exec fpa_database pg_dump -U fpa_user fpa_db > /opt/backups/floor-plan-analyzer/db_$(date +\%Y\%m\%d).sql

# تنظيف النسخ القديمة (> 30 يوم)
0 3 * * * find /opt/backups/floor-plan-analyzer -type f -mtime +30 -delete
```

---

## ⚠️ استكشاف الأخطاء الشائعة

### 1. لا يمكن الوصول للـ API

```bash
# فحص الحاويات
docker ps -a

# إذا كانت متوقفة:
docker-compose up -d

# فحص المنفذ
netstat -tulpn | grep 8000

# فحص Firewall
ufw status
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
```

### 2. خطأ Database Connection

```bash
# فحص Database
docker logs fpa_database

# إعادة تشغيل
docker-compose restart db

# التحقق من الاتصال
docker exec -it fpa_database psql -U fpa_user -d fpa_db -c "SELECT 1;"
```

### 3. خطأ في رفع الملف

```bash
# تحقق من حجم الملف في Nginx
nano /etc/nginx/sites-available/floor-plan-analyzer
# تأكد من: client_max_body_size 50M;

# إعادة تشغيل Nginx
systemctl restart nginx
```

### 4. نفاذ المساحة

```bash
# تنظيف الملفات القديمة
find /opt/floor-plan-analyzer/data/uploads -type f -mtime +7 -delete
find /opt/floor-plan-analyzer/data/outputs -type f -mtime +7 -delete

# تنظيف Docker
docker system prune -af
```

---

## 📊 المراقبة

### إعداد فحص صحة تلقائي

```bash
# إنشاء سكريبت المراقبة
nano /opt/scripts/check-fpa-health.sh
```

```bash
#!/bin/bash
if ! curl -f -s http://localhost:8000/health > /dev/null; then
    echo "$(date): FPA API is down! Restarting..." >> /var/log/fpa-monitor.log
    cd /opt/floor-plan-analyzer
    docker-compose restart api
fi
```

```bash
chmod +x /opt/scripts/check-fpa-health.sh

# إضافة لـ crontab (كل 5 دقائق)
crontab -e

# أضف:
*/5 * * * * /opt/scripts/check-fpa-health.sh
```

---

## 🎯 ملخص الأوامر السريعة

```bash
# الحالة
docker ps

# Logs
docker logs -f fpa_api

# إعادة تشغيل
docker-compose restart

# إيقاف
docker-compose down

# تشغيل
docker-compose up -d

# التحديث
./infra/update.sh

# نسخ احتياطي
docker exec fpa_database pg_dump -U fpa_user fpa_db > backup.sql
```

---

## ✅ قائمة التحقق

- [x] Docker مثبت
- [ ] الملفات منقولة للـ VPS
- [ ] .env معدّل بكلمات سر قوية
- [ ] النشر اكتمل بنجاح
- [ ] `/health` يعمل
- [ ] Nginx مثبت ومُعدّ
- [ ] DNS يشير للـ IP الصحيح
- [ ] SSL مثبت (Certbot)
- [ ] النطاقات تعمل بـ HTTPS
- [ ] النسخ الاحتياطي التلقائي مُفعّل
- [ ] المراقبة مُفعّلة

---

## 📞 للدعم

راجع الملفات التالية للمساعدة:
- `README_AR.md` - الدليل الشامل
- `DEPLOYMENT_GUIDE_AR.md` - دليل النشر المفصل
- `QUICK_START.md` - البدء السريع
- `PROJECT_SUMMARY.md` - ملخص المشروع

---

**جاهز للنشر على VPS الخاص بك!** 🚀

بعد اتباع هذه الخطوات، سيكون لديك نظام محلل مخططات الطوابق يعمل بكامل طاقته على:
- ✅ https://flows.aqeeli.com
- ✅ https://wfapi.aqeeli.com
