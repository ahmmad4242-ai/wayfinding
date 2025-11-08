# 🌐 إعداد DNS لنطاق aqeeli.com

## 📋 الوضع الحالي

لديك نطاق **aqeeli.com** مع السجلات التالية:

| النوع | الاسم | المحتوى | الحالة |
|------|-------|---------|--------|
| A | api | 77.37.35.25 | ✅ Proxied |
| A | aqeeli.com | 194.36.184.20 | ✅ DNS only |
| A | cmp | 178.16.130.125 | ✅ Proxied |
| A | flows | 77.37.35.25 | ⚠️ DNS only |
| A | wfapi | 77.37.35.25 | ⚠️ DNS only |

---

## 🎯 التوصية: استخدام النطاقات الموجودة

### الخيار 1: استخدام wfapi.aqeeli.com (موصى به ✅)

**السجل موجود بالفعل!**
```
wfapi.aqeeli.com → 77.37.35.25
```

**الإعدادات في .env:**
```bash
DOMAIN=wfapi.aqeeli.com
ALLOWED_ORIGINS=https://wfapi.aqeeli.com,https://flows.aqeeli.com,https://aqeeli.com
```

---

### الخيار 2: استخدام flows.aqeeli.com

**السجل موجود بالفعل!**
```
flows.aqeeli.com → 77.37.35.25
```

**الإعدادات في .env:**
```bash
DOMAIN=flows.aqeeli.com
ALLOWED_ORIGINS=https://flows.aqeeli.com,https://wfapi.aqeeli.com,https://aqeeli.com
```

---

## 🔧 إذا أردت إنشاء نطاق فرعي جديد

### مثال: wayfinding.aqeeli.com

في لوحة تحكم DNS الخاصة بك (Cloudflare على ما يبدو):

1. **اضغط "Add record"**
2. **النوع**: A
3. **الاسم**: wayfinding
4. **المحتوى (IPv4)**: `77.37.35.25` (IP خادم VPS)
5. **Proxy status**: 
   - ⚠️ **DNS only** (موصى به للبداية)
   - أو Proxied (إذا أردت حماية Cloudflare)
6. **TTL**: Auto
7. **احفظ**

---

## ✅ التحقق من إعداد DNS

### الطريقة 1: من جهازك المحلي

```bash
# فحص wfapi.aqeeli.com
nslookup wfapi.aqeeli.com

# يجب أن ترى:
# Address: 77.37.35.25
```

### الطريقة 2: من VPS

```bash
# على VPS
ping wfapi.aqeeli.com

# يجب أن يتجاوب
```

### الطريقة 3: عبر الإنترنت

اذهب إلى: https://dnschecker.org/
- أدخل: `wfapi.aqeeli.com`
- تحقق من أن جميع المواقع تُرجع: `77.37.35.25`

---

## 🚀 الخطوات على VPS

### 1. تأكد من IP الخادم

```bash
# على VPS
curl ifconfig.me

# يجب أن يُرجع: 77.37.35.25
```

إذا كان IP مختلفاً، **عدّل سجل A في DNS** ليشير إلى IP الصحيح.

---

### 2. تحديث ملف .env

```bash
cd /root/wayfinding

# نسخ الإعدادات الجاهزة
cp .env.production .env

# تحرير الإعدادات
nano .env
```

**غيّر القيم التالية:**
```bash
DOMAIN=wfapi.aqeeli.com
LETSENCRYPT_EMAIL=admin@aqeeli.com
SECRET_KEY=YourStrongRandomKey32CharsOrMore
```

احفظ: `Ctrl+O` ثم `Enter` ثم `Ctrl+X`

---

### 3. بناء وتشغيل Docker

```bash
# بناء الصور
docker-compose build

# تشغيل الحاويات
docker-compose up -d

# التحقق
docker-compose ps
curl http://localhost:8000/health
```

---

### 4. إعداد Nginx

```bash
sudo nano /etc/nginx/sites-available/wayfinding
```

**انسخ هذا الإعداد:**
```nginx
# HTTP → HTTPS Redirect
server {
    listen 80;
    listen [::]:80;
    server_name wfapi.aqeeli.com;
    
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
    server_name wfapi.aqeeli.com;

    # SSL certificates (will be added by Certbot)
    # ssl_certificate /etc/letsencrypt/live/wfapi.aqeeli.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/wfapi.aqeeli.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Upload limits
    client_max_body_size 100M;
    client_body_timeout 300s;

    # Frontend
    location / {
        root /root/wayfinding/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # API Docs
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
    }
}
```

**تفعيل وإعادة تشغيل:**
```bash
sudo ln -s /etc/nginx/sites-available/wayfinding /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### 5. إعداد SSL مع Certbot

```bash
# تثبيت Certbot (إذا لم يكن مثبتاً)
sudo apt install certbot python3-certbot-nginx -y

# الحصول على شهادة SSL
sudo certbot --nginx -d wfapi.aqeeli.com

# سيطلب منك:
# 1. بريدك الإلكتروني: admin@aqeeli.com
# 2. الموافقة على الشروط: Y
# 3. إعادة توجيه HTTP إلى HTTPS: 2 (نعم)
```

---

### 6. التحقق من النشر

```bash
# فحص SSL
curl https://wfapi.aqeeli.com/health

# يجب أن ترى:
# {"status":"healthy","message":"System is operational","version":"1.0.0"}
```

---

## 🔥 جدار الحماية

```bash
# السماح بالمنافذ الضرورية
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# تفعيل الجدار
sudo ufw enable

# التحقق
sudo ufw status
```

---

## 📊 الاختبار الكامل

### من المتصفح:
```
https://wfapi.aqeeli.com
```
يجب أن تظهر الواجهة الأمامية

### API Docs:
```
https://wfapi.aqeeli.com/docs
```
يجب أن تظهر وثائق API

### Health Check:
```
https://wfapi.aqeeli.com/health
```
يجب أن يُرجع: `{"status":"healthy",...}`

---

## ⚠️ استكشاف المشاكل

### المشكلة: DNS لا يحل (resolve)
**الحل:**
```bash
# انتظر 5-10 دقائق لانتشار DNS
# تحقق من:
nslookup wfapi.aqeeli.com 8.8.8.8
```

### المشكلة: Certbot يفشل
**الحل:**
```bash
# تأكد من أن:
# 1. DNS يحل بشكل صحيح
# 2. المنفذ 80 مفتوح
# 3. Nginx يعمل
sudo systemctl status nginx
```

### المشكلة: API لا يستجيب
**الحل:**
```bash
# فحص الحاويات
docker-compose ps

# فحص السجلات
docker-compose logs -f api

# إعادة تشغيل
docker-compose restart
```

---

## 📋 قائمة التحقق النهائية

- [ ] سجل DNS A يشير إلى IP الصحيح (77.37.35.25)
- [ ] ملف .env محدّث بالنطاق الصحيح
- [ ] Docker يعمل: `docker-compose ps`
- [ ] API يستجيب: `curl http://localhost:8000/health`
- [ ] Nginx مثبت ومُعدّ
- [ ] SSL مُثبّت بنجاح
- [ ] جدار الحماية مُفعّل
- [ ] الموقع يعمل: `https://wfapi.aqeeli.com`

---

## 🎉 عند النجاح

الموقع سيكون متاحاً على:
```
https://wfapi.aqeeli.com
```

API Docs:
```
https://wfapi.aqeeli.com/docs
```

---

**🎓 جاهز للاستخدام الإنتاجي!**
