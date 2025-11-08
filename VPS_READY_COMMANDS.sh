#!/bin/bash
# ===============================================
# أوامر VPS جاهزة للتنفيذ | Ready VPS Commands
# ===============================================
# انسخ والصق الأوامر التالية على VPS مباشرة
# Copy and paste these commands directly on VPS

echo "🚀 بدء تثبيت Floor Plan Analyzer Academic v2.0.0"
echo "🚀 Starting Floor Plan Analyzer Academic v2.0.0 Installation"
echo ""

# ===============================================
# 1. تحديث النظام | System Update
# ===============================================
echo "📦 تحديث النظام..."
sudo apt update && sudo apt upgrade -y

# ===============================================
# 2. تثبيت Docker | Install Docker
# ===============================================
echo "🐳 تثبيت Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "✅ تم تثبيت Docker"
else
    echo "✅ Docker مثبت مسبقاً"
fi

# ===============================================
# 3. تثبيت Docker Compose | Install Docker Compose
# ===============================================
echo "🐳 تثبيت Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ تم تثبيت Docker Compose"
else
    echo "✅ Docker Compose مثبت مسبقاً"
fi

# التحقق من التثبيت
docker --version
docker-compose --version

# ===============================================
# 4. تحميل المشروع | Download Project
# ===============================================
echo ""
echo "📥 تحميل المشروع..."
cd /root
wget https://page.gensparksite.com/project_backups/floor-plan-analyzer-academic-v2.0.0.tar.gz

echo "📦 فك الضغط..."
tar -xzf floor-plan-analyzer-academic-v2.0.0.tar.gz

# الانتقال لمجلد المشروع
cd /root/home/user/webapp/floor-plan-analyzer

echo "✅ تم تحميل المشروع بنجاح"

# ===============================================
# 5. إعداد ملف .env | Setup .env
# ===============================================
echo ""
echo "⚙️ إعداد ملف .env..."
cp .env.example .env

echo ""
echo "⚠️  انتبه: يجب تعديل ملف .env يدوياً!"
echo "⚠️  Attention: You must edit .env file manually!"
echo ""
echo "استخدم الأمر التالي لتحرير .env:"
echo "nano .env"
echo ""
echo "غيّر القيم التالية | Change these values:"
echo "  - DOMAIN=your-domain.com"
echo "  - LETSENCRYPT_EMAIL=your-email@example.com"
echo "  - SECRET_KEY=generate-random-32-chars"
echo "  - ALLOWED_ORIGINS=https://your-domain.com"
echo ""
read -p "اضغط Enter بعد تعديل .env | Press Enter after editing .env"

# ===============================================
# 6. بناء وتشغيل الحاويات | Build & Run
# ===============================================
echo ""
echo "🏗️ بناء صور Docker..."
docker-compose build

echo "🚀 تشغيل النظام..."
docker-compose up -d

echo ""
echo "✅ النظام يعمل الآن!"
echo "✅ System is now running!"

# ===============================================
# 7. فحص الحالة | Check Status
# ===============================================
echo ""
echo "🔍 فحص حالة الحاويات..."
docker-compose ps

echo ""
echo "🔍 فحص صحة API..."
sleep 5
curl http://localhost:8000/health

# ===============================================
# 8. تثبيت Certbot للـ SSL | Install Certbot
# ===============================================
echo ""
echo "🔒 تثبيت Certbot للـ SSL..."
sudo apt install certbot python3-certbot-nginx -y

echo ""
echo "⚠️  لإعداد SSL، نفّذ الأمر التالي (غيّر your-domain.com):"
echo "⚠️  To setup SSL, run this command (replace your-domain.com):"
echo ""
echo "sudo certbot --nginx -d your-domain.com -d www.your-domain.com"
echo ""

# ===============================================
# 9. إعداد جدار الحماية | Setup Firewall
# ===============================================
echo ""
echo "🛡️ إعداد جدار الحماية UFW..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 22/tcp   # SSH
    sudo ufw allow 80/tcp   # HTTP
    sudo ufw allow 443/tcp  # HTTPS
    echo "✅ تم إعداد جدار الحماية"
    echo ""
    echo "⚠️  لتفعيل الجدار، نفّذ: sudo ufw enable"
else
    sudo apt install ufw -y
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    echo "✅ تم تثبيت وإعداد UFW"
    echo ""
    echo "⚠️  لتفعيل الجدار، نفّذ: sudo ufw enable"
fi

# ===============================================
# 10. الخلاصة | Summary
# ===============================================
echo ""
echo "======================================"
echo "✅ التثبيت اكتمل بنجاح!"
echo "✅ Installation Complete!"
echo "======================================"
echo ""
echo "📍 معلومات الوصول | Access Information:"
echo "   - API: http://localhost:8000"
echo "   - Health: http://localhost:8000/health"
echo "   - Docs: http://localhost:8000/docs"
echo ""
echo "📝 الخطوات التالية | Next Steps:"
echo "   1. إعداد SSL: sudo certbot --nginx -d your-domain.com"
echo "   2. تفعيل جدار الحماية: sudo ufw enable"
echo "   3. الوصول للنظام: https://your-domain.com"
echo ""
echo "📚 الوثائق | Documentation:"
echo "   - VPS_DEPLOYMENT_COMMANDS.md"
echo "   - QUICK_DEPLOYMENT_GUIDE.md"
echo "   - ACADEMIC_METHODOLOGY.md"
echo ""
echo "🔧 أوامر مفيدة | Useful Commands:"
echo "   - عرض السجلات: docker-compose logs -f api"
echo "   - إعادة تشغيل: docker-compose restart"
echo "   - إيقاف: docker-compose down"
echo "   - فحص الموارد: docker stats"
echo ""
echo "======================================"
echo "🎉 استمتع بالنظام! | Enjoy the System!"
echo "======================================"
