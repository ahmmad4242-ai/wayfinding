#!/bin/bash
# ═══════════════════════════════════════════════════════════
# إصلاح Frontend API_URL على الخادم
# نفذ هذا الملف على VPS: bash FIX_NOW.sh
# ═══════════════════════════════════════════════════════════

set -e  # Exit on error

echo "🔧 Starting frontend update..."
echo ""

# Navigate to repository
cd /root/wayfinding

# Pull latest changes
echo "📥 Pulling latest code from GitHub..."
git pull origin main

# Copy frontend files
echo "📋 Copying frontend files..."
cp -r frontend/* /var/www/wfapi/

echo ""
echo "✅ Update completed!"
echo ""

# Verify the fix
echo "🔍 Verifying API_URL:"
grep -n "const API_URL" /var/www/wfapi/index.html

echo ""

# Check for localhost references
if grep -q "localhost:8001" /var/www/wfapi/index.html; then
    echo "❌ ERROR: Still contains localhost:8001!"
    echo "Applying manual fix..."
    sed -i "s|const API_URL = 'http://localhost:8001';|const API_URL = 'https://wfapi.aqeeli.com';|g" /var/www/wfapi/index.html
    echo "✅ Manual fix applied"
    echo ""
    echo "🔍 Verification after manual fix:"
    grep -n "const API_URL" /var/www/wfapi/index.html
else
    echo "✅ No localhost:8001 references found!"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Frontend update complete!"
echo ""
echo "🧪 Next steps:"
echo "1. Open: https://wfapi.aqeeli.com/"
echo "2. Press: Ctrl+Shift+R (clear cache)"
echo "3. Test: Upload a floor plan file"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
