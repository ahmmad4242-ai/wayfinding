"""
Image Processor - معالج الصور
معالجة الصور وتحسينها للتحليل
"""
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Tuple, Optional
from loguru import logger

from src.config import settings


class ImageProcessor:
    """معالج الصور الأساسي"""
    
    def __init__(self):
        self.dpi = settings.ocr_dpi
    
    async def process(self, file_path: Path) -> np.ndarray:
        """
        معالجة الصورة الأساسية
        
        Args:
            file_path: مسار الملف
        
        Returns:
            الصورة المعالجة (numpy array)
        """
        try:
            logger.info(f"📷 Processing image: {file_path}")
            
            # Load image
            if file_path.suffix.lower() == '.pdf':
                image = await self._process_pdf(file_path)
            else:
                image = await self._load_image(file_path)
            
            # Preprocessing pipeline
            image = await self._preprocess(image)
            
            return image
            
        except Exception as e:
            logger.error(f"❌ Error processing image: {str(e)}")
            raise
    
    async def _load_image(self, file_path: Path) -> np.ndarray:
        """تحميل صورة"""
        img = cv2.imread(str(file_path))
        if img is None:
            raise ValueError(f"فشل تحميل الصورة: {file_path}")
        return img
    
    async def _process_pdf(self, file_path: Path) -> np.ndarray:
        """معالجة ملف PDF"""
        try:
            from pdf2image import convert_from_path
            
            # Convert first page to image
            images = convert_from_path(
                str(file_path),
                dpi=self.dpi,
                first_page=1,
                last_page=1
            )
            
            if not images:
                raise ValueError("فشل تحويل PDF إلى صورة")
            
            # Convert PIL to OpenCV format
            pil_image = images[0]
            image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            return image
            
        except Exception as e:
            logger.error(f"❌ Error processing PDF: {str(e)}")
            raise
    
    async def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        معالجة مسبقة للصورة
        - إزالة التشويش
        - تحسين التباين
        - تصحيح الميل
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Detect and correct skew
        enhanced = await self._deskew(enhanced)
        
        # Convert back to BGR for consistency
        processed = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        
        return processed
    
    async def _deskew(self, image: np.ndarray) -> np.ndarray:
        """تصحيح ميل الصورة"""
        try:
            # Detect edges
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
            
            if lines is None:
                return image
            
            # Calculate average angle
            angles = []
            for rho, theta in lines[:, 0]:
                angle = np.degrees(theta) - 90
                if -45 < angle < 45:
                    angles.append(angle)
            
            if not angles:
                return image
            
            median_angle = np.median(angles)
            
            # Rotate image
            if abs(median_angle) > 0.5:
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                rotated = cv2.warpAffine(
                    image, M, (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )
                logger.info(f"🔄 Corrected skew: {median_angle:.2f}°")
                return rotated
            
            return image
            
        except Exception as e:
            logger.warning(f"⚠️ Could not deskew image: {str(e)}")
            return image
    
    async def extract_scale(self, image: np.ndarray) -> Optional[float]:
        """
        استخراج المقياس من الصورة
        (البحث عن شريط المقياس)
        """
        try:
            # This is a placeholder - actual implementation would use
            # OCR and pattern matching to find scale bars
            logger.info("🔍 Attempting to extract scale from image...")
            
            # TODO: Implement scale extraction
            # 1. Look for scale bar patterns
            # 2. Use OCR to read scale text
            # 3. Calculate scale ratio
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Could not extract scale: {str(e)}")
            return None
    
    async def create_binary(self, image: np.ndarray) -> np.ndarray:
        """إنشاء صورة ثنائية للكشف"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(
            gray, 0, 255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        return binary
    
    async def detect_layers(self, image: np.ndarray) -> dict:
        """
        محاولة فصل الطبقات (إذا كانت بألوان مختلفة)
        """
        try:
            # Convert to HSV for better color separation
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # This is a simplified approach
            # In production, you'd use more sophisticated color clustering
            
            layers = {
                "walls": None,
                "doors": None,
                "text": None
            }
            
            # TODO: Implement layer separation based on colors
            
            return layers
            
        except Exception as e:
            logger.warning(f"⚠️ Could not separate layers: {str(e)}")
            return {}
