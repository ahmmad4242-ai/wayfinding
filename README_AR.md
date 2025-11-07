# محلل مخططات الطوابق 🏗️

نظام متكامل لتحليل المخططات المعمارية واستخراج المقاييس والامتثال للكود

## 🎯 نظرة عامة

**محلل مخططات الطوابق** هو أداة احترافية متقدمة لتحليل المخططات المعمارية تلقائياً، مصممة خصيصاً للمستشفيات والمباني التجارية والسكنية.

### الميزات الرئيسية

#### 📐 استخراج العناصر التلقائي
- **كشف الجدران**: استخدام خوارزميات Hough Transform و RANSAC
- **الأبواب والنوافذ**: كشف ذكي للرموز المعمارية
- **الغرف والممرات**: تقسيم تلقائي للمساحات
- **السلالم والمصاعد**: التعرف على عناصر الحركة العمودية

#### 📊 المقاييس والتحليلات
- **GFA** (Gross Floor Area): إجمالي مساحة الطابق
- **NIA** (Net Internal Area): صافي المساحة الداخلية  
- **GLA** (Gross Leasable Area): المساحة القابلة للتأجير
- **كفاءة المساحة**: NIA/GFA
- **نسبة الممرات**: نسبة الممرات من المساحة الكلية

#### 🚶 تحليل التوجيه (Wayfinding)
- **Space Syntax**: مؤشرات Integration و Choice
- **Visibility Analysis**: شبكات الرؤية و Isovists
- **Decision Points**: نقاط القرار والالتباس
- **أطوال المسارات**: متوسط المسافات والانعطافات
- **توصيات اللوحات**: أماكن مثلى للوحات الإرشادية

#### ✅ فحص الامتثال للكود
- **الكود السعودي SBC**: اشتراطات البناء السعودي
- **Fire Safety**: فحص السلامة والإخلاء
- **ADA Compliance**: الوصول الشامل
- **عروض الممرات**: فحص الحدود الدنيا
- **مسافات الهروب**: التحقق من مسافات الإخلاء

#### 🎨 التحليل اللوني المتقدم (جديد!)
- **استخراج الألوان السائدة**: K-Means clustering
- **لوحة الألوان**: Color palette كاملة
- **الإحصائيات**: السطوع، التباين، التشبع
- **الخرائط الحرارية**: Heatmaps للكثافة اللونية
- **التوزيع اللوني**: تحليل توزيع الألوان في المخطط
- **التوصيات**: اقتراحات بناءً على التحليل

#### 📈 رسوم بيانية تفاعلية
- **مخططات المساحات**: توزيع المساحات بالغرف
- **مخططات الامتثال**: نسب التوافق مع الكود
- **رسوم التوجيه**: تحليلات المسارات
- **مخططات الألوان**: عرض تفاعلي للوحة الألوان

## 🏗️ البنية التقنية

### Stack التقني

```
Backend:
├── FastAPI (Python 3.11)
├── OpenCV + scikit-image (معالجة الصور)
├── PyTorch + Ultralytics (Deep Learning)
├── NetworkX + iGraph (تحليل الشبكات)
├── PostgreSQL + PostGIS (قاعدة البيانات)
└── Redis (Caching)

Frontend:
├── React 18
├── TailwindCSS
├── Chart.js (الرسوم البيانية)
└── Axios (HTTP Client)

Infrastructure:
├── Docker + Docker Compose
├── Nginx (Reverse Proxy)
└── SSL/TLS
```

### بنية المشروع

```
floor-plan-analyzer/
├── src/
│   ├── parser/               # معالجة PDF/DWG/صور
│   ├── detection/            # كشف الأبواب/الجدران
│   ├── analysis/             # حساب المساحات والمقاييس
│   ├── wayfinding/           # تحليل التوجيه
│   ├── compliance/           # فحص الامتثال
│   ├── coloranalysis/        # التحليل اللوني (جديد!)
│   ├── api/                  # FastAPI endpoints
│   └── config.py             # الإعدادات
├── frontend/                 # واجهة الويب
├── models/                   # نماذج التعلم العميق
├── tests/                    # الاختبارات
├── infra/                    # ملفات النشر
│   ├── deploy.sh             # سكريبت النشر
│   ├── update.sh             # سكريبت التحديث
│   └── nginx.conf            # إعدادات Nginx
├── docker-compose.yml        # Docker configuration
└── README_AR.md              # هذا الملف
```

## 📦 التثبيت والنشر

### المتطلبات الأساسية

- **VPS** مع Ubuntu 20.04+ أو Debian 11+
- **Docker** و **Docker Compose**
- **4GB RAM** على الأقل
- **20GB** مساحة تخزين

### الخطوة 1: إعداد VPS

```bash
# تثبيت Docker
curl -fsSL https://get.docker.com | bash

# تثبيت Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# التحقق من التثبيت
docker --version
docker compose version
```

### الخطوة 2: نقل الملفات للـ VPS

```bash
# من جهازك المحلي، قم بضغط المشروع
tar -czf fpa.tar.gz floor-plan-analyzer/

# نقل للـ VPS باستخدام scp
scp fpa.tar.gz root@77.37.35.25:/root/

# على الـ VPS، فك الضغط
ssh root@77.37.35.25
cd /root
tar -xzf fpa.tar.gz
cd floor-plan-analyzer
```

### الخطوة 3: إعداد المتغيرات البيئية

```bash
# نسخ ملف الإعدادات
cp .env.example .env

# تعديل الإعدادات
nano .env
```

**متغيرات مهمة يجب تعديلها:**

```env
# Database
DB_PASSWORD=قم_بتغيير_هذا_الباسورد

# Security
SECRET_KEY=قم_بتوليد_مفتاح_آمن_هنا

# API
API_WORKERS=4  # عدد العمليات (workers)
MAX_CONCURRENT_JOBS=5

# Domains
ALLOWED_ORIGINS=https://flows.aqeeli.com,https://wfapi.aqeeli.com
```

### الخطوة 4: النشر

```bash
# تشغيل سكريبت النشر
chmod +x infra/deploy.sh
sudo ./infra/deploy.sh
```

**سيقوم السكريبت بـ:**
1. ✅ إنشاء المجلدات المطلوبة
2. ✅ نسخ الملفات
3. ✅ بناء صور Docker
4. ✅ تشغيل جميع الخدمات
5. ✅ التحقق من الصحة

### الخطوة 5: التحقق

```bash
# فحص الخدمات
docker ps

# فحص الصحة
curl http://localhost:8000/health

# عرض Logs
docker logs -f fpa_api
```

## 🚀 الاستخدام

### API Endpoints

#### 1. تحليل مخطط

```bash
POST /api/analyze
Content-Type: multipart/form-data

Parameters:
  - file: ملف المخطط (PDF, PNG, JPG, DWG)
  - scale: مقياس الرسم (optional)
  - unit: وحدة القياس (meters/feet)
  - building_type: نوع المبنى (hospital/office/residential)
  - enable_color_analysis: تفعيل التحليل اللوني (true/false)

Response:
{
  "job_id": "uuid",
  "status": "processing",
  "message": "تم استلام الملف",
  "estimated_time": "2-5 دقائق"
}
```

**مثال باستخدام curl:**

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@hospital_floor_plan.pdf" \
  -F "scale=100" \
  -F "unit=meters" \
  -F "building_type=hospital" \
  -F "enable_color_analysis=true"
```

#### 2. حالة المهمة

```bash
GET /api/status/{job_id}

Response:
{
  "job_id": "uuid",
  "status": "completed",
  "progress": 100,
  "message": "اكتمل التحليل",
  "result": { ... }
}
```

#### 3. الحصول على التقرير

```bash
GET /api/report/{job_id}?format=json

Formats: json, pdf, csv, excel
```

### مثال على النتيجة

```json
{
  "job_id": "abc-123",
  "metadata": {
    "filename": "hospital_plan.pdf",
    "scale": 100,
    "unit": "meters",
    "building_type": "hospital"
  },
  "elements": {
    "rooms": 45,
    "doors": 78,
    "corridors": 12,
    "stairs": 3
  },
  "metrics": {
    "gfa": 1850.5,
    "nia": 1340.2,
    "gla": 1210.8,
    "efficiency": 0.72,
    "circulation_ratio": 0.23
  },
  "wayfinding": {
    "avg_path_length": 42.7,
    "avg_turns": 3.1,
    "decision_points": 14,
    "complexity_score": 68.5
  },
  "compliance": {
    "overall_score": 85.3,
    "passed": 42,
    "failed": 7,
    "critical_issues": 2
  },
  "color_analysis": {
    "dominant_colors": [
      {
        "rgb": [255, 255, 255],
        "hex": "#ffffff",
        "percentage": 45.2,
        "name": "أبيض"
      }
    ],
    "statistics": {
      "brightness_avg": 185.3,
      "contrast_ratio": 3.2,
      "temperature": "cool"
    }
  }
}
```

## 🔧 الإدارة والصيانة

### عرض Logs

```bash
# جميع الخدمات
docker-compose logs -f

# API فقط
docker-compose logs -f api

# Database فقط
docker-compose logs -f db
```

### إعادة التشغيل

```bash
# إعادة تشغيل خدمة واحدة
docker-compose restart api

# إعادة تشغيل الكل
docker-compose restart
```

### التحديث

```bash
# باستخدام سكريبت التحديث
./infra/update.sh

# أو يدوياً
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### النسخ الاحتياطي

```bash
# نسخ احتياطي للقاعدة
docker exec fpa_database pg_dump -U fpa_user fpa_db > backup.sql

# نسخ احتياطي للبيانات
tar -czf data_backup.tar.gz data/

# نسخ احتياطي كامل
tar -czf full_backup.tar.gz /opt/floor-plan-analyzer/
```

### الاستعادة

```bash
# استعادة القاعدة
docker exec -i fpa_database psql -U fpa_user fpa_db < backup.sql
```

## 🌐 إعداد النطاق (Domain)

### Nginx Reverse Proxy

أنشئ ملف `/opt/floor-plan-analyzer/infra/nginx.conf`:

```nginx
server {
    listen 80;
    server_name flows.aqeeli.com wfapi.aqeeli.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /usr/share/nginx/html/;
    }
}
```

### SSL باستخدام Certbot

```bash
# تثبيت Certbot
sudo apt-get install certbot python3-certbot-nginx

# الحصول على شهادة SSL
sudo certbot --nginx -d flows.aqeeli.com -d wfapi.aqeeli.com

# التجديد التلقائي
sudo certbot renew --dry-run
```

## 📊 مراقبة الأداء

### Metrics

```bash
# استخدام الذاكرة
docker stats

# مساحة القرص
df -h /opt/floor-plan-analyzer/data/

# عدد المهام المعالجة
curl http://localhost:8000/api/stats
```

### Health Checks

```bash
# API Health
curl http://localhost:8000/health

# Database Health
docker exec fpa_database pg_isready -U fpa_user

# Redis Health
docker exec fpa_redis redis-cli ping
```

## 🐛 استكشاف الأخطاء

### المشكلة: API لا يستجيب

```bash
# فحص الـ logs
docker logs fpa_api

# إعادة التشغيل
docker-compose restart api
```

### المشكلة: نفاذ الذاكرة

```bash
# زيادة حد الذاكرة في docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 4G
```

### المشكلة: بطء المعالجة

- قلل عدد `MAX_CONCURRENT_JOBS` في `.env`
- زد عدد `API_WORKERS`
- تحقق من موارد VPS

## 📞 الدعم والمساهمة

### الإبلاغ عن مشكلة

افتح Issue في GitHub مع:
- وصف المشكلة
- خطوات إعادة الإنتاج
- Logs ذات الصلة

### المساهمة

1. Fork المشروع
2. أنشئ فرع للميزة (`git checkout -b feature/AmazingFeature`)
3. Commit التغييرات (`git commit -m 'Add AmazingFeature'`)
4. Push للفرع (`git push origin feature/AmazingFeature`)
5. افتح Pull Request

## 📄 الترخيص

MIT License - انظر ملف [LICENSE](LICENSE) للتفاصيل

## 🙏 شكر وتقدير

- **OpenCV** - معالجة الصور
- **FastAPI** - إطار عمل API
- **PostgreSQL** - قاعدة البيانات
- **Docker** - الحاويات

---

**تم التطوير بواسطة** محلل مخططات الطوابق - 2024

للأسئلة والدعم: [GitHub Issues](https://github.com/yourusername/floor-plan-analyzer/issues)
