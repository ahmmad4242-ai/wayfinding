"""
Code Checker - فاحص الكود
فحص الامتثال للاشتراطات والكودات
"""
import numpy as np
from typing import Dict, List, Any
from loguru import logger

from src.config import settings


class CodeChecker:
    """فاحص الكود والامتثال"""
    
    def __init__(self, building_type: str = "hospital"):
        self.building_type = building_type
        self.rules = self._load_rules()
    
    def _load_rules(self) -> Dict[str, Any]:
        """تحميل قواعد الكود بحسب نوع المبنى"""
        rules = {
            "hospital": {
                "min_corridor_width": 2.4,  # meters
                "min_door_width": 1.2,
                "max_egress_distance": 45.0,
                "min_exits": 2,
                "min_stair_width": 1.5
            },
            "office": {
                "min_corridor_width": 1.2,
                "min_door_width": 0.9,
                "max_egress_distance": 60.0,
                "min_exits": 2,
                "min_stair_width": 1.1
            },
            "residential": {
                "min_corridor_width": 1.0,
                "min_door_width": 0.8,
                "max_egress_distance": 75.0,
                "min_exits": 1,
                "min_stair_width": 0.9
            }
        }
        
        return rules.get(self.building_type, rules["office"])
    
    async def check(self, elements: Dict, areas: Dict, metrics: Dict) -> Dict[str, Any]:
        """
        فحص الامتثال الشامل
        
        Args:
            elements: العناصر المكتشفة
            areas: بيانات المساحات
            metrics: المقاييس
        
        Returns:
            نتائج فحص الامتثال
        """
        try:
            logger.info("✅ Checking code compliance...")
            
            checks = []
            
            # Check corridor widths
            checks.extend(await self._check_corridor_widths(elements))
            
            # Check door widths
            checks.extend(await self._check_door_widths(elements))
            
            # Check egress distances
            checks.extend(await self._check_egress(elements, areas))
            
            # Check exit count
            checks.extend(await self._check_exits(elements))
            
            # Calculate compliance score
            compliant_count = sum(1 for c in checks if c["compliant"])
            total_checks = len(checks) if checks else 1
            score = (compliant_count / total_checks) * 100
            
            # Categorize issues
            critical = [c for c in checks if not c["compliant"] and c["severity"] == "critical"]
            warnings = [c for c in checks if not c["compliant"] and c["severity"] == "warning"]
            
            result = {
                "building_type": self.building_type,
                "code": settings.default_building_code,
                "overall_score": round(score, 1),
                "total_checks": total_checks,
                "passed": compliant_count,
                "failed": total_checks - compliant_count,
                "critical_issues": len(critical),
                "warnings": len(warnings),
                "checks": checks,
                "summary": await self._generate_summary(checks)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error checking compliance: {str(e)}")
            return {}
    
    async def _check_corridor_widths(self, elements: Dict) -> List[Dict]:
        """فحص عروض الممرات"""
        checks = []
        corridors = elements.get("corridors", [])
        min_width = self.rules["min_corridor_width"]
        
        for corridor in corridors:
            width = corridor.get("width", 0)
            compliant = width >= min_width
            
            checks.append({
                "category": "circulation",
                "requirement": f"الحد الأدنى لعرض الممر: {min_width}m",
                "element_id": corridor["id"],
                "actual_value": round(width, 2),
                "required_value": min_width,
                "compliant": compliant,
                "severity": "critical" if not compliant else "info",
                "message": "مطابق" if compliant else f"عرض غير كافٍ: {round(width, 2)}m"
            })
        
        return checks
    
    async def _check_door_widths(self, elements: Dict) -> List[Dict]:
        """فحص عروض الأبواب"""
        checks = []
        doors = elements.get("doors", [])
        min_width = self.rules["min_door_width"]
        
        for door in doors:
            width = door.get("width", 0)
            compliant = width >= min_width
            
            checks.append({
                "category": "access",
                "requirement": f"الحد الأدنى لعرض الباب: {min_width}m",
                "element_id": door["id"],
                "actual_value": round(width, 2),
                "required_value": min_width,
                "compliant": compliant,
                "severity": "warning" if not compliant else "info",
                "message": "مطابق" if compliant else f"باب ضيق: {round(width, 2)}m"
            })
        
        return checks
    
    async def _check_egress(self, elements: Dict, areas: Dict) -> List[Dict]:
        """فحص مسافات الإخلاء"""
        checks = []
        max_distance = self.rules["max_egress_distance"]
        
        # Simplified: check if any room exceeds maximum dimension
        rooms = elements.get("rooms", [])
        
        for room in rooms[:20]:  # Sample
            # Estimate max travel distance (diagonal)
            polygon = room.get("polygon", [])
            if len(polygon) < 2:
                continue
            
            xs = [p["x"] for p in polygon]
            ys = [p["y"] for p in polygon]
            
            # Convert pixels to meters (approximate)
            max_dim = max(max(xs) - min(xs), max(ys) - min(ys)) / 100  # rough estimate
            
            compliant = max_dim < max_distance
            
            checks.append({
                "category": "egress",
                "requirement": f"أقصى مسافة إخلاء: {max_distance}m",
                "element_id": room["id"],
                "actual_value": round(max_dim, 2),
                "required_value": max_distance,
                "compliant": compliant,
                "severity": "critical" if not compliant else "info",
                "message": "مطابق" if compliant else "مسافة إخلاء مفرطة"
            })
        
        return checks
    
    async def _check_exits(self, elements: Dict) -> List[Dict]:
        """فحص عدد المخارج"""
        checks = []
        min_exits = self.rules["min_exits"]
        
        # Count doors that could be exits (simplified)
        doors = elements.get("doors", [])
        stairs = elements.get("stairs", [])
        
        exit_count = len(stairs) + min(len(doors), 4)  # Rough estimate
        
        compliant = exit_count >= min_exits
        
        checks.append({
            "category": "egress",
            "requirement": f"الحد الأدنى للمخارج: {min_exits}",
            "element_id": "building",
            "actual_value": exit_count,
            "required_value": min_exits,
            "compliant": compliant,
            "severity": "critical" if not compliant else "info",
            "message": "مطابق" if compliant else f"عدد مخارج غير كاف: {exit_count}"
        })
        
        return checks
    
    async def _generate_summary(self, checks: List[Dict]) -> Dict[str, Any]:
        """توليد ملخص النتائج"""
        if not checks:
            return {}
        
        categories = {}
        for check in checks:
            cat = check["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "passed": 0}
            categories[cat]["total"] += 1
            if check["compliant"]:
                categories[cat]["passed"] += 1
        
        return {
            "by_category": categories,
            "needs_attention": [
                c for c in checks 
                if not c["compliant"] and c["severity"] == "critical"
            ][:5]
        }
