# تعليمات تحديث Frontend على الخادم

## ✅ تم رفع التعديل بنجاح إلى GitHub

التعديل: تغيير `API_URL` من `http://localhost:8001` إلى `https://wfapi.aqeeli.com`

**Commit**: c5c86fb
**Branch**: main
**Repository**: ahmmad4242-ai/wayfinding

---

## 📋 الخطوات المطلوبة على الخادم (VPS: 77.37.35.25)

قم بتنفيذ الأوامر التالية على الخادم:

```bash
# 1. الانتقال إلى مجلد المشروع
cd /root/wayfinding

# 2. سحب آخر التحديثات من GitHub
git pull origin main

# 3. نسخ ملفات Frontend المحدثة
cp -r frontend/* /var/www/wfapi/

# 4. التحقق من التعديل
echo "🔍 Verifying API_URL:"
grep -n "const API_URL" /var/www/wfapi/index.html

# 5. اختبار الموقع
curl -I https://wfapi.aqeeli.com/
```

---

## ✅ النتيجة المتوقعة

بعد تنفيذ الأوامر، يجب أن ترى:

```
181:        const API_URL = 'https://wfapi.aqeeli.com';
```

**ليس**:
```
181:        const API_URL = 'http://localhost:8001';
```

---

## 🧪 اختبار النظام

1. افتح المتصفح واذهب إلى: https://wfapi.aqeeli.com/
2. اضغط **Ctrl+Shift+R** لمسح الـ cache
3. حاول رفع ملف floor plan (PDF أو صورة)
4. تأكد من ظهور شريط التقدم
5. انتظر اكتمال التحليل
6. تحقق من عرض النتائج

---

## 🐛 إذا استمرت المشكلة

### خيار 1: تعديل مباشر على الملف

```bash
# تعديل الملف مباشرة
nano /var/www/wfapi/index.html

# ابحث عن السطر 181:
# const API_URL = 'http://localhost:8001';

# وغيره إلى:
# const API_URL = 'https://wfapi.aqeeli.com';

# احفظ بـ Ctrl+O ثم اخرج بـ Ctrl+X
```

### خيار 2: استخدام sed

```bash
sed -i "s|const API_URL = 'http://localhost:8001';|const API_URL = 'https://wfapi.aqeeli.com';|g" /var/www/wfapi/index.html

# تحقق من النتيجة
grep "const API_URL" /var/www/wfapi/index.html
```

---

## 📊 معلومات إضافية

### حالة الـ API (يجب أن تكون working)

```bash
# تحقق من Docker containers
docker ps

# يجب أن ترى:
# - floor-plan-analyzer-fpa_api-1
# - floor-plan-analyzer-fpa_database-1
# - floor-plan-analyzer-fpa_redis-1

# اختبار API
curl http://localhost:8000/health
curl https://wfapi.aqeeli.com/health
```

### حالة Nginx

```bash
# تحقق من nginx
systemctl status nginx

# اختبار إعدادات nginx
nginx -t

# إعادة تحميل nginx (إذا لزم الأمر)
systemctl reload nginx
```

---

## 📝 ملاحظات

- التعديل موجود الآن على GitHub في branch main
- Commit hash: c5c86fb
- بعد تنفيذ `git pull`، سيتم تحميل الملف المحدث تلقائيًا
- تأكد من مسح cache المتصفح بعد التحديث
- إذا كانت المشكلة مستمرة، قد تحتاج إلى فحص إعدادات Cloudflare Proxy

---

## 🎯 الخطوة التالية بعد الإصلاح

بمجرد حل مشكلة `API_URL`:

1. ✅ **اختبار رفع الملفات**: رفع floor plan فعلي
2. ✅ **اختبار التقارير**: التحقق من تحميل JSON/PDF reports
3. ✅ **توثيق API**: تحديث README بتعليمات الاستخدام
4. ✅ **اختبار Performance**: قياس أوقات التحليل

---

**آخر تحديث**: 2025-11-08
**المطوّر**: Claude Code Agent
