"""
Color Extractor - مستخرج الألوان
تحليل الألوان واستخراج لوحة الألوان السائدة
"""
import cv2
import numpy as np
from typing import List, Dict, Any
from sklearn.cluster import KMeans
from loguru import logger
import colorsys

from src.config import settings


class ColorExtractor:
    """مستخرج الألوان"""
    
    def __init__(self):
        self.palette_size = settings.color_palette_size
    
    async def extract(self, image: np.ndarray) -> Dict[str, Any]:
        """
        استخراج الألوان وإنشاء التحليلات اللونية
        
        Args:
            image: الصورة المراد تحليلها
        
        Returns:
            تحليل شامل للألوان مع الرسوم البيانية
        """
        try:
            logger.info("🎨 Extracting colors and creating visualizations...")
            
            # Extract dominant colors
            dominant_colors = await self._extract_dominant_colors(image)
            
            # Create color palette
            palette = await self._create_palette(image)
            
            # Calculate color statistics
            stats = await self._calculate_color_stats(image)
            
            # Create heatmap
            heatmap_data = await self._create_heatmap(image)
            
            # Analyze color distribution
            distribution = await self._analyze_distribution(image)
            
            result = {
                "dominant_colors": dominant_colors,
                "color_palette": palette,
                "statistics": stats,
                "heatmap": heatmap_data,
                "distribution": distribution,
                "recommendations": await self._generate_recommendations(dominant_colors, stats)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error extracting colors: {str(e)}")
            raise
    
    async def _extract_dominant_colors(
        self,
        image: np.ndarray,
        n_colors: int = 5
    ) -> List[Dict[str, Any]]:
        """استخراج الألوان السائدة باستخدام K-Means"""
        try:
            # Reshape image to list of pixels
            pixels = image.reshape(-1, 3)
            
            # Remove black and white (borders/background)
            mask = ~((pixels.sum(axis=1) < 30) | (pixels.sum(axis=1) > 725))
            pixels = pixels[mask]
            
            if len(pixels) == 0:
                return []
            
            # Sample for performance (max 10000 pixels)
            if len(pixels) > 10000:
                indices = np.random.choice(len(pixels), 10000, replace=False)
                pixels = pixels[indices]
            
            # K-Means clustering
            kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
            kmeans.fit(pixels)
            
            # Get colors and their frequencies
            colors = kmeans.cluster_centers_.astype(int)
            labels = kmeans.labels_
            
            # Calculate percentages
            unique, counts = np.unique(labels, return_counts=True)
            percentages = (counts / counts.sum() * 100).tolist()
            
            # Convert to result format
            dominant = []
            for i, (color, pct) in enumerate(zip(colors, percentages)):
                b, g, r = color
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                color_name = await self._get_color_name(r, g, b)
                
                dominant.append({
                    "rgb": [int(r), int(g), int(b)],
                    "hex": hex_color,
                    "percentage": round(float(pct), 2),
                    "name": color_name,
                    "rank": i + 1
                })
            
            # Sort by percentage
            dominant.sort(key=lambda x: x["percentage"], reverse=True)
            
            return dominant
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting dominant colors: {str(e)}")
            return []
    
    async def _create_palette(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """إنشاء لوحة ألوان شاملة"""
        return await self._extract_dominant_colors(image, self.palette_size)
    
    async def _calculate_color_stats(self, image: np.ndarray) -> Dict[str, Any]:
        """حساب الإحصائيات اللونية"""
        try:
            # Convert to different color spaces
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calculate statistics
            stats = {
                # Brightness
                "brightness_avg": float(np.mean(gray)),
                "brightness_std": float(np.std(gray)),
                "brightness_min": float(np.min(gray)),
                "brightness_max": float(np.max(gray)),
                
                # Saturation
                "saturation_avg": float(np.mean(hsv[:, :, 1])),
                "saturation_std": float(np.std(hsv[:, :, 1])),
                
                # Hue
                "hue_avg": float(np.mean(hsv[:, :, 0])),
                "hue_std": float(np.std(hsv[:, :, 0])),
                
                # Contrast
                "contrast_ratio": float(np.max(gray) / (np.min(gray) + 1)),
                "contrast_std": float(np.std(gray)),
                
                # Color temperature (warm vs cool)
                "temperature": await self._calculate_temperature(image)
            }
            
            return stats
            
        except Exception as e:
            logger.warning(f"⚠️ Error calculating color stats: {str(e)}")
            return {}
    
    async def _calculate_temperature(self, image: np.ndarray) -> str:
        """حساب درجة حرارة اللون (دافئ/بارد)"""
        # Calculate average red vs blue
        avg_red = np.mean(image[:, :, 2])
        avg_blue = np.mean(image[:, :, 0])
        
        if avg_red > avg_blue * 1.1:
            return "warm"
        elif avg_blue > avg_red * 1.1:
            return "cool"
        else:
            return "neutral"
    
    async def _create_heatmap(self, image: np.ndarray) -> Dict[str, Any]:
        """إنشاء خريطة حرارية للكثافة اللونية"""
        try:
            # Convert to grayscale for intensity
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Create heatmap
            heatmap = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
            
            # Calculate zones
            h, w = gray.shape
            zones = {
                "top_left": float(np.mean(gray[0:h//2, 0:w//2])),
                "top_right": float(np.mean(gray[0:h//2, w//2:w])),
                "bottom_left": float(np.mean(gray[h//2:h, 0:w//2])),
                "bottom_right": float(np.mean(gray[h//2:h, w//2:w])),
                "center": float(np.mean(gray[h//4:3*h//4, w//4:3*w//4]))
            }
            
            return {
                "zones": zones,
                "overall_intensity": float(np.mean(gray)),
                "hotspots": await self._find_hotspots(gray)
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error creating heatmap: {str(e)}")
            return {}
    
    async def _find_hotspots(self, gray: np.ndarray, threshold: float = 200) -> List[Dict]:
        """إيجاد النقاط الساخنة (المناطق عالية الكثافة)"""
        # Find bright regions
        _, thresh = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        hotspots = []
        for contour in contours[:10]:  # Top 10
            M = cv2.moments(contour)
            if M["m00"] > 0:
                cx = M["m10"] / M["m00"]
                cy = M["m01"] / M["m00"]
                area = cv2.contourArea(contour)
                
                hotspots.append({
                    "location": {"x": float(cx), "y": float(cy)},
                    "area": float(area)
                })
        
        return hotspots
    
    async def _analyze_distribution(self, image: np.ndarray) -> Dict[str, Any]:
        """تحليل توزيع الألوان في المخطط"""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Count pixels in hue ranges
        ranges = {
            "red": ((0, 10), (170, 180)),
            "orange": ((10, 25),),
            "yellow": ((25, 35),),
            "green": ((35, 85),),
            "cyan": ((85, 95),),
            "blue": ((95, 135),),
            "purple": ((135, 170),)
        }
        
        distribution = {}
        total_pixels = image.shape[0] * image.shape[1]
        
        for color_name, hue_ranges in ranges.items():
            count = 0
            for hue_range in hue_ranges:
                mask = cv2.inRange(hsv[:, :, 0], hue_range[0], hue_range[1])
                count += np.count_nonzero(mask)
            
            distribution[color_name] = round(count / total_pixels * 100, 2)
        
        return distribution
    
    async def _get_color_name(self, r: int, g: int, b: int) -> str:
        """الحصول على اسم اللون التقريبي"""
        # Convert to HSV for better color naming
        hsv = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        hue = hsv[0] * 360
        sat = hsv[1] * 100
        val = hsv[2] * 100
        
        # Very dark or light
        if val < 20:
            return "أسود"
        if val > 90 and sat < 10:
            return "أبيض"
        if sat < 20:
            return "رمادي"
        
        # Hue-based names
        if hue < 15 or hue >= 345:
            return "أحمر"
        elif hue < 45:
            return "برتقالي"
        elif hue < 70:
            return "أصفر"
        elif hue < 150:
            return "أخضر"
        elif hue < 210:
            return "أزرق سماوي"
        elif hue < 270:
            return "أزرق"
        elif hue < 330:
            return "بنفسجي"
        else:
            return "وردي"
    
    async def _generate_recommendations(
        self,
        colors: List[Dict],
        stats: Dict
    ) -> List[str]:
        """توليد توصيات بناءً على التحليل اللوني"""
        recommendations = []
        
        # Contrast check
        if stats.get("contrast_ratio", 0) < 2:
            recommendations.append("التباين منخفض - قد يكون المخطط صعب القراءة")
        
        # Brightness check
        brightness = stats.get("brightness_avg", 0)
        if brightness < 50:
            recommendations.append("المخطط داكن جداً - يُنصح بتحسين الإضاءة")
        elif brightness > 200:
            recommendations.append("المخطط فاتح جداً - قد تكون التفاصيل غير واضحة")
        
        # Color diversity
        if len(colors) < 3:
            recommendations.append("تنوع لوني محدود - قد يكون المخطط بسيط جداً")
        
        # Temperature
        temp = stats.get("temperature")
        if temp == "warm":
            recommendations.append("الألوان دافئة - مناسب للمساحات الاجتماعية")
        elif temp == "cool":
            recommendations.append("الألوان باردة - مناسب للمساحات المهنية")
        
        return recommendations
