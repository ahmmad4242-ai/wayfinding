#!/bin/bash
# ================================================
# أوامر نشر سريعة لـ aqeeli.com
# Quick deployment commands for aqeeli.com
# ================================================

echo "🚀 Floor Plan Analyzer - Quick Setup for aqeeli.com"
echo ""

# ================================================
# المتغيرات | Variables
# ================================================
DOMAIN="wfapi.aqeeli.com"
EMAIL="admin@aqeeli.com"
PROJECT_DIR="/root/wayfinding"

# ================================================
# 1. التحقق من IP | Check IP
# ================================================
echo "🔍 فحص IP الخادم..."
SERVER_IP=$(curl -s ifconfig.me)
echo "✅ IP الخادم: $SERVER_IP"
echo ""

if [ "$SERVER_IP" != "77.37.35.25" ]; then
    echo "⚠️  تحذير: IP الخادم ($SERVER_IP) لا يطابق DNS (77.37.35.25)"
    echo "   عدّل سجل A في DNS ليشير إلى: $SERVER_IP"
    echo ""
fi

# ================================================
# 2. التحقق من DNS | Check DNS
# ================================================
echo "🔍 فحص DNS..."
DNS_IP=$(dig +short $DOMAIN | tail -n1)

if [ -z "$DNS_IP" ]; then
    echo "❌ DNS لا يحل (resolve) بعد"
    echo "   انتظر 5-10 دقائق لانتشار التغييرات"
    exit 1
else
    echo "✅ DNS يحل إلى: $DNS_IP"
fi
echo ""

# ================================================
# 3. إعداد ملف .env | Setup .env
# ================================================
echo "⚙️ إعداد ملف .env..."
cd $PROJECT_DIR

if [ ! -f ".env" ]; then
    if [ -f ".env.production" ]; then
        cp .env.production .env
        echo "✅ تم نسخ .env.production إلى .env"
    else
        echo "❌ ملف .env.production غير موجود!"
        exit 1
    fi
fi

# تحديث القيم الأساسية
sed -i "s/DOMAIN=.*/DOMAIN=$DOMAIN/" .env
sed -i "s/LETSENCRYPT_EMAIL=.*/LETSENCRYPT_EMAIL=$EMAIL/" .env

echo "✅ تم تحديث .env"
echo ""

# ================================================
# 4. بناء Docker | Build Docker
# ================================================
echo "🐳 بناء صور Docker..."
docker-compose build

if [ $? -eq 0 ]; then
    echo "✅ تم بناء الصور بنجاح"
else
    echo "❌ فشل بناء الصور"
    exit 1
fi
echo ""

# ================================================
# 5. تشغيل الحاويات | Start Containers
# ================================================
echo "🚀 تشغيل الحاويات..."
docker-compose up -d

if [ $? -eq 0 ]; then
    echo "✅ الحاويات تعمل الآن"
else
    echo "❌ فشل تشغيل الحاويات"
    exit 1
fi
echo ""

# انتظار قليلاً لبدء API
echo "⏳ انتظار بدء API..."
sleep 5

# ================================================
# 6. فحص API | Check API
# ================================================
echo "🔍 فحص API..."
API_RESPONSE=$(curl -s http://localhost:8000/health)

if [ -z "$API_RESPONSE" ]; then
    echo "❌ API لا يستجيب"
    echo "فحص السجلات:"
    docker-compose logs --tail=20 api
    exit 1
else
    echo "✅ API يعمل: $API_RESPONSE"
fi
echo ""

# ================================================
# 7. إعداد Nginx | Setup Nginx
# ================================================
echo "🌐 إعداد Nginx..."

# التحقق من تثبيت Nginx
if ! command -v nginx &> /dev/null; then
    echo "📦 تثبيت Nginx..."
    apt update
    apt install nginx -y
fi

# إنشاء ملف إعداد Nginx
cat > /etc/nginx/sites-available/wayfinding << 'EOF'
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

    # SSL (will be configured by Certbot)
    ssl_certificate /etc/letsencrypt/live/wfapi.aqeeli.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wfapi.aqeeli.com/privkey.pem;

    # Security
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

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

    location ~ ^/(docs|health|redoc) {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
EOF

# تفعيل الموقع
ln -sf /etc/nginx/sites-available/wayfinding /etc/nginx/sites-enabled/

# اختبار الإعداد
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ إعداد Nginx صحيح"
    systemctl reload nginx
else
    echo "❌ خطأ في إعداد Nginx"
    exit 1
fi
echo ""

# ================================================
# 8. إعداد SSL | Setup SSL
# ================================================
echo "🔒 إعداد SSL..."

# التحقق من تثبيت Certbot
if ! command -v certbot &> /dev/null; then
    echo "📦 تثبيت Certbot..."
    apt install certbot python3-certbot-nginx -y
fi

echo ""
echo "⚠️  الآن سيتم طلب شهادة SSL من Let's Encrypt"
echo "   سيطلب منك Certbot بعض الأسئلة:"
echo "   1. البريد الإلكتروني: $EMAIL"
echo "   2. الموافقة على الشروط: Y"
echo "   3. إعادة توجيه HTTP → HTTPS: 2 (نعم)"
echo ""
read -p "اضغط Enter للمتابعة..."

certbot --nginx -d $DOMAIN --email $EMAIL --agree-tos --no-eff-email

if [ $? -eq 0 ]; then
    echo "✅ تم إعداد SSL بنجاح"
else
    echo "⚠️  فشل إعداد SSL"
    echo "   جرّب يدوياً: sudo certbot --nginx -d $DOMAIN"
fi
echo ""

# ================================================
# 9. جدار الحماية | Firewall
# ================================================
echo "🛡️ إعداد جدار الحماية..."

if command -v ufw &> /dev/null; then
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    echo "y" | ufw enable
    echo "✅ جدار الحماية مُفعّل"
else
    echo "⚠️  UFW غير مثبت، تخطي..."
fi
echo ""

# ================================================
# 10. الاختبار النهائي | Final Test
# ================================================
echo "🧪 الاختبار النهائي..."
echo ""

echo "1. فحص HTTP:"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN/health)
if [ "$HTTP_STATUS" == "301" ] || [ "$HTTP_STATUS" == "200" ]; then
    echo "   ✅ HTTP يعمل (Status: $HTTP_STATUS)"
else
    echo "   ⚠️  HTTP Status: $HTTP_STATUS"
fi

echo ""
echo "2. فحص HTTPS:"
HTTPS_RESPONSE=$(curl -s https://$DOMAIN/health 2>&1)
if [[ $HTTPS_RESPONSE == *"healthy"* ]]; then
    echo "   ✅ HTTPS يعمل"
    echo "   الاستجابة: $HTTPS_RESPONSE"
else
    echo "   ⚠️  HTTPS لا يعمل بعد"
    echo "   الاستجابة: $HTTPS_RESPONSE"
fi

echo ""
echo "======================================"
echo "✅ اكتمل النشر!"
echo "======================================"
echo ""
echo "📍 معلومات الوصول:"
echo "   - الموقع: https://$DOMAIN"
echo "   - API Docs: https://$DOMAIN/docs"
echo "   - Health: https://$DOMAIN/health"
echo ""
echo "🔧 أوامر مفيدة:"
echo "   - السجلات: docker-compose logs -f api"
echo "   - إعادة تشغيل: docker-compose restart"
echo "   - الحالة: docker-compose ps"
echo ""
echo "======================================"
