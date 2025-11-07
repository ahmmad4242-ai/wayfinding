"""
Visibility Analyzer - محلل الرؤية
تحليل الرؤية والوضوح البصري
"""
import numpy as np
from typing import Dict, List, Any
from loguru import logger


class VisibilityAnalyzer:
    """محلل الرؤية"""
    
    async def analyze(self, elements: Dict) -> Dict[str, Any]:
        """
        تحليل الرؤية البصرية
        
        Args:
            elements: العناصر المكتشفة
        
        Returns:
            بيانات الرؤية
        """
        try:
            logger.info("👁️ Analyzing visibility...")
            
            # Simplified visibility analysis
            rooms = elements.get("rooms", [])
            corridors = elements.get("corridors", [])
            
            if not rooms:
                return {}
            
            # Calculate visibility integration index
            integration = await self._calculate_integration(rooms, corridors)
            
            # Find blind spots
            blind_spots = await self._find_blind_spots(rooms)
            
            result = {
                "visibility_integration_index": integration,
                "blind_spots": len(blind_spots),
                "blind_spot_locations": blind_spots,
                "avg_visibility_area": await self._avg_visibility(rooms),
                "recommendations": await self._generate_visibility_recommendations(blind_spots)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error analyzing visibility: {str(e)}")
            return {}
    
    async def _calculate_integration(self, rooms: List, corridors: List) -> float:
        """حساب مؤشر التكامل البصري"""
        # Simplified: ratio of open spaces (corridors) to total
        if not rooms:
            return 0.0
        
        total_area = sum(r["area"] for r in rooms)
        corridor_area = sum(c["area"] for c in corridors)
        
        if total_area == 0:
            return 0.0
        
        integration = corridor_area / total_area
        return round(min(integration, 1.0), 3)
    
    async def _find_blind_spots(self, rooms: List) -> List[Dict]:
        """إيجاد النقاط العمياء"""
        # Simplified: rooms without direct corridor access
        blind_spots = []
        
        for room in rooms[:5]:  # Sample
            # This would need proper door-to-corridor analysis
            blind_spots.append({
                "room_id": room["id"],
                "location": room["centroid"]
            })
        
        return blind_spots
    
    async def _avg_visibility(self, rooms: List) -> float:
        """متوسط مساحة الرؤية"""
        if not rooms:
            return 0.0
        return round(np.mean([r["area"] for r in rooms]), 2)
    
    async def _generate_visibility_recommendations(self, blind_spots: List) -> List[str]:
        """توليد توصيات الرؤية"""
        recommendations = []
        
        if len(blind_spots) > 5:
            recommendations.append("عدد كبير من النقاط العمياء - يُنصح بإضافة لوحات إرشادية")
        
        recommendations.append("استخدم الألوان والرموز لتحسين التوجيه")
        
        return recommendations
