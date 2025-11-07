"""
Metrics Calculator - حاسبة المقاييس
حساب مقاييس الأداء والكفاءة
"""
from typing import Dict, Any
from loguru import logger


class MetricsCalculator:
    """حاسبة المقاييس"""
    
    async def calculate(
        self,
        areas: Dict[str, Any],
        elements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        حساب جميع المقاييس
        
        Args:
            areas: بيانات المساحات
            elements: العناصر المكتشفة
        
        Returns:
            المقاييس المحسوبة
        """
        try:
            logger.info("📊 Calculating metrics...")
            
            base_metrics = areas.get("metrics", {})
            
            # Add additional calculations
            metrics = {
                **base_metrics,
                "density_metrics": await self._calculate_density(areas, elements),
                "connectivity_metrics": await self._calculate_connectivity(elements),
                "distribution_metrics": await self._calculate_distribution(areas)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Error calculating metrics: {str(e)}")
            raise
    
    async def _calculate_density(
        self,
        areas: Dict,
        elements: Dict
    ) -> Dict[str, float]:
        """حساب الكثافة"""
        gfa = areas.get("metrics", {}).get("gfa", 1)
        
        return {
            "doors_per_100m2": len(elements.get("doors", [])) / gfa * 100 if gfa > 0 else 0,
            "rooms_per_100m2": len(elements.get("rooms", [])) / gfa * 100 if gfa > 0 else 0,
            "walls_per_100m2": len(elements.get("walls", [])) / gfa * 100 if gfa > 0 else 0
        }
    
    async def _calculate_connectivity(self, elements: Dict) -> Dict[str, Any]:
        """حساب معدلات الاتصال"""
        num_rooms = len(elements.get("rooms", []))
        num_doors = len(elements.get("doors", []))
        
        return {
            "avg_doors_per_room": num_doors / num_rooms if num_rooms > 0 else 0,
            "connectivity_index": num_doors / (num_rooms + 1) if num_rooms > 0 else 0
        }
    
    async def _calculate_distribution(self, areas: Dict) -> Dict[str, Any]:
        """حساب توزيع المساحات"""
        rooms = areas.get("elements", {}).get("rooms", [])
        
        if not rooms:
            return {}
        
        room_areas = [r["area"] for r in rooms]
        
        import numpy as np
        
        return {
            "area_std_dev": float(np.std(room_areas)),
            "area_variance": float(np.var(room_areas)),
            "area_range": float(max(room_areas) - min(room_areas))
        }
