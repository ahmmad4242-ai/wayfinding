"""
Area Analyzer - محلل المساحات
حساب المساحات وتحويلها للوحدات الحقيقية
"""
import numpy as np
from typing import Dict, List, Any, Optional
from loguru import logger


class AreaAnalyzer:
    """محلل المساحات"""
    
    def __init__(self):
        self.pixels_per_meter = None
    
    async def analyze(
        self,
        elements: Dict[str, Any],
        scale: Optional[float],
        unit: str = "meters"
    ) -> Dict[str, Any]:
        """
        تحليل المساحات وتحويلها للوحدات الحقيقية
        
        Args:
            elements: العناصر المكتشفة
            scale: مقياس الرسم (مثلاً 1/100)
            unit: وحدة القياس
        
        Returns:
            المساحات المحسوبة بالوحدات الحقيقية
        """
        try:
            logger.info("📐 Analyzing areas and converting units...")
            
            # Estimate scale if not provided
            if scale is None:
                scale = await self._estimate_scale(elements)
                logger.info(f"📏 Estimated scale: 1/{scale}")
            
            # Calculate conversion factor
            self.pixels_per_meter = await self._calculate_conversion(scale, unit)
            
            # Convert all measurements
            converted_elements = await self._convert_measurements(elements)
            
            # Calculate summary metrics
            metrics = await self._calculate_metrics(converted_elements)
            
            result = {
                "scale": scale,
                "unit": unit,
                "pixels_per_meter": self.pixels_per_meter,
                "elements": converted_elements,
                "metrics": metrics
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error analyzing areas: {str(e)}")
            raise
    
    async def _estimate_scale(self, elements: Dict) -> float:
        """
        تقدير المقياس من حجم الأبواب
        (الأبواب عادة 0.8-1.2 متر)
        """
        doors = elements.get("doors", [])
        
        if not doors:
            # Default scale assumption
            logger.warning("⚠️ No doors found for scale estimation, using default 1/100")
            return 100.0
        
        # Average door width in pixels
        avg_door_width_px = np.mean([d["width"] for d in doors])
        
        # Assume standard door width of 0.9m
        standard_door_m = 0.9
        
        # Calculate scale
        # pixels_per_meter = avg_door_width_px / standard_door_m
        # scale = reference_length / drawing_length
        # For 1/100 scale: 1m in reality = 1cm on drawing = fewer pixels
        
        estimated_scale = avg_door_width_px / (standard_door_m * 100)
        
        # Reasonable scale range: 1/50 to 1/200
        estimated_scale = max(50, min(200, estimated_scale))
        
        return estimated_scale
    
    async def _calculate_conversion(self, scale: float, unit: str) -> float:
        """
        حساب معامل التحويل من بكسل إلى وحدة حقيقية
        
        Args:
            scale: مقياس الرسم (مثلاً 100 لـ 1/100)
            unit: وحدة القياس
        
        Returns:
            عدد البكسل في المتر الواحد
        """
        # Assume 300 DPI scan
        dpi = 300
        
        # Pixels per inch
        px_per_inch = dpi
        
        # Convert scale drawing to real world
        # 1/100 scale means: 1 unit on drawing = 100 units in reality
        # If drawing is in cm: 1 cm on paper = 100 cm = 1 m in reality
        
        # Inches per meter on the drawing at given scale
        # For 1/100: 1m reality = 1cm on drawing = 0.3937 inches
        inches_per_meter_on_drawing = (100 / scale) * 0.3937
        
        # Pixels per meter
        pixels_per_meter = inches_per_meter_on_drawing * px_per_inch
        
        # Convert to requested unit
        if unit == "feet":
            pixels_per_meter = pixels_per_meter / 0.3048
        
        return pixels_per_meter
    
    async def _convert_measurements(self, elements: Dict) -> Dict:
        """تحويل جميع القياسات من بكسل إلى وحدات حقيقية"""
        converted = {}
        
        # Convert rooms
        converted["rooms"] = []
        for room in elements.get("rooms", []):
            converted_room = room.copy()
            converted_room["area"] = self._px_to_unit_area(room["area"])
            converted_room["perimeter"] = self._px_to_unit(room["perimeter"])
            converted["rooms"].append(converted_room)
        
        # Convert corridors
        converted["corridors"] = []
        for corridor in elements.get("corridors", []):
            converted_corridor = corridor.copy()
            converted_corridor["area"] = self._px_to_unit_area(corridor["area"])
            converted_corridor["width"] = self._px_to_unit(corridor["width"])
            converted_corridor["length"] = self._px_to_unit(corridor["length"])
            converted["corridors"].append(converted_corridor)
        
        # Convert doors
        converted["doors"] = []
        for door in elements.get("doors", []):
            converted_door = door.copy()
            converted_door["width"] = self._px_to_unit(door["width"])
            converted["doors"].append(converted_door)
        
        # Convert walls
        converted["walls"] = []
        for wall in elements.get("walls", []):
            converted_wall = wall.copy()
            converted_wall["length"] = self._px_to_unit(wall["length"])
            converted_wall["thickness"] = self._px_to_unit(wall["thickness"])
            converted["walls"].append(converted_wall)
        
        # Keep other elements as is
        converted["windows"] = elements.get("windows", [])
        converted["stairs"] = elements.get("stairs", [])
        converted["elevators"] = elements.get("elevators", [])
        
        return converted
    
    def _px_to_unit(self, pixels: float) -> float:
        """تحويل من بكسل إلى وحدة قياس"""
        if self.pixels_per_meter is None:
            return pixels
        return pixels / self.pixels_per_meter
    
    def _px_to_unit_area(self, pixels_squared: float) -> float:
        """تحويل مساحة من بكسل² إلى وحدة²"""
        if self.pixels_per_meter is None:
            return pixels_squared
        return pixels_squared / (self.pixels_per_meter ** 2)
    
    async def _calculate_metrics(self, elements: Dict) -> Dict[str, Any]:
        """حساب المقاييس الإجمالية"""
        rooms = elements.get("rooms", [])
        corridors = elements.get("corridors", [])
        
        # Total room area (excluding corridors)
        room_areas = [r["area"] for r in rooms if r not in corridors]
        total_room_area = sum(room_areas) if room_areas else 0
        
        # Total corridor area
        corridor_areas = [c["area"] for c in corridors]
        total_corridor_area = sum(corridor_areas) if corridor_areas else 0
        
        # GFA (Gross Floor Area) - all enclosed spaces
        gfa = total_room_area + total_corridor_area
        
        # NIA (Net Internal Area) - usable spaces (exclude thick walls)
        # Simplified: assume 95% of GFA
        nia = gfa * 0.95
        
        # GLA (Gross Leasable Area) - rentable space
        # Exclude corridors and services
        gla = total_room_area * 0.90
        
        # Efficiency
        efficiency = nia / gfa if gfa > 0 else 0
        
        # Circulation ratio
        circulation_ratio = total_corridor_area / gfa if gfa > 0 else 0
        
        metrics = {
            "gfa": round(gfa, 2),
            "nia": round(nia, 2),
            "gla": round(gla, 2),
            "efficiency": round(efficiency, 3),
            "circulation_ratio": round(circulation_ratio, 3),
            "total_rooms": len(rooms) - len(corridors),
            "total_corridors": len(corridors),
            "avg_room_area": round(np.mean(room_areas), 2) if room_areas else 0,
            "total_room_area": round(total_room_area, 2),
            "total_corridor_area": round(total_corridor_area, 2)
        }
        
        return metrics
