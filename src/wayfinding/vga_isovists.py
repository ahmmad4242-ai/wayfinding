"""
Visibility Graph Analysis (VGA) & Isovists
تحليل الرؤية البصرية وحقول الرؤية
Based on: Benedikt (1979), Turner et al. (2001)
"""
import numpy as np
import cv2
from typing import Dict, List, Any, Tuple
from loguru import logger
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union
import networkx as nx


class VisibilityAnalyzer:
    """محلل الرؤية المتقدم - VGA و Isovists"""
    
    def __init__(self, grid_size: float = 0.5):
        """
        Args:
            grid_size: حجم شبكة العينات بالمتر (0.5-1.0م)
        """
        self.grid_size = grid_size
        self.floor_plan = None
        self.obstacles = []
        self.visibility_graph = None
    
    async def analyze(
        self,
        floor_plan_image: np.ndarray,
        walls: List[Dict],
        scale_px_per_meter: float
    ) -> Dict[str, Any]:
        """
        تحليل الرؤية الشامل
        
        Args:
            floor_plan_image: صورة المخطط
            walls: قائمة الجدران
            scale_px_per_meter: معامل التحويل
        
        Returns:
            نتائج تحليل الرؤية
        """
        try:
            logger.info("👁️ Starting Visibility Graph Analysis...")
            
            self.floor_plan = floor_plan_image
            self.obstacles = await self._prepare_obstacles(walls)
            
            # إنشاء شبكة نقاط العينات
            sample_points = await self._generate_sample_grid(
                floor_plan_image,
                scale_px_per_meter
            )
            
            logger.info(f"Generated {len(sample_points)} sample points")
            
            # حساب Isovists لكل نقطة عينة
            isovists = await self._calculate_isovists(sample_points)
            
            # بناء Visibility Graph
            vg = await self._build_visibility_graph(sample_points, isovists)
            
            # حساب مؤشرات VGA
            vga_metrics = await self._calculate_vga_metrics(vg, isovists)
            
            # تحديد نقاط حرجة
            critical_points = await self._identify_critical_visibility_points(
                vga_metrics
            )
            
            result = {
                "sample_points": sample_points,
                "isovists": isovists,
                "visibility_graph": vg,
                "vga_metrics": vga_metrics,
                "critical_points": critical_points,
                "summary": await self._generate_visibility_summary(vga_metrics)
            }
            
            logger.info("✅ VGA analysis completed")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in VGA analysis: {str(e)}")
            raise
    
    async def _prepare_obstacles(self, walls: List[Dict]) -> List[LineString]:
        """
        تحضير العوائق (الجدران) كخطوط Shapely
        """
        obstacles = []
        
        for wall in walls:
            start = wall.get("start", {})
            end = wall.get("end", {})
            
            line = LineString([
                (start.get("x", 0), start.get("y", 0)),
                (end.get("x", 0), end.get("y", 0))
            ])
            obstacles.append(line)
        
        return obstacles
    
    async def _generate_sample_grid(
        self,
        image: np.ndarray,
        scale: float
    ) -> List[Tuple[float, float]]:
        """
        إنشاء شبكة نقاط عينات منتظمة
        """
        h, w = image.shape[:2]
        grid_step_px = int(self.grid_size * scale)
        
        if grid_step_px < 1:
            grid_step_px = 1
        
        points = []
        
        # إنشاء شبكة منتظمة
        for y in range(0, h, grid_step_px):
            for x in range(0, w, grid_step_px):
                # تحقق إذا كانت النقطة في مساحة حرة (ليست جدار)
                if await self._is_free_space(x, y, image):
                    points.append((float(x), float(y)))
        
        # حد أقصى للنقاط (لتجنب الأحمال الكبيرة)
        if len(points) > 5000:
            # عينة عشوائية
            indices = np.random.choice(len(points), 5000, replace=False)
            points = [points[i] for i in indices]
        
        return points
    
    async def _is_free_space(self, x: int, y: int, image: np.ndarray) -> bool:
        """
        فحص إذا كانت نقطة في مساحة حرة
        """
        h, w = image.shape[:2]
        if x < 0 or x >= w or y < 0 or y >= h:
            return False
        
        # تحويل لرمادي إن لزم
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # اعتبار البكسل الفاتح كمساحة حرة
        pixel_value = gray[y, x]
        return pixel_value > 128  # عتبة بسيطة
    
    async def _calculate_isovists(
        self,
        sample_points: List[Tuple[float, float]]
    ) -> Dict[Tuple[float, float], Dict[str, Any]]:
        """
        حساب Isovist لكل نقطة عينة
        
        Isovist = حقل الرؤية من نقطة
        """
        isovists = {}
        
        # عدد الأشعة لحساب Isovist
        n_rays = 72  # كل 5 درجات
        max_distance = 1000  # بكسل
        
        for point in sample_points[:1000]:  # حد أقصى للسرعة
            try:
                isovist_polygon = await self._compute_isovist_polygon(
                    point,
                    n_rays,
                    max_distance
                )
                
                # حساب خصائص Isovist
                properties = await self._analyze_isovist(isovist_polygon)
                
                isovists[point] = {
                    "polygon": isovist_polygon,
                    **properties
                }
                
            except Exception as e:
                logger.warning(f"Failed to compute isovist for {point}: {e}")
                isovists[point] = {
                    "polygon": None,
                    "area": 0,
                    "perimeter": 0,
                    "max_radial": 0,
                    "mean_radial": 0
                }
        
        return isovists
    
    async def _compute_isovist_polygon(
        self,
        origin: Tuple[float, float],
        n_rays: int,
        max_distance: float
    ) -> Polygon:
        """
        حساب مضلع Isovist من نقطة الأصل
        """
        rays_endpoints = []
        
        for i in range(n_rays):
            angle = 2 * np.pi * i / n_rays
            
            # اتجاه الشعاع
            dx = np.cos(angle)
            dy = np.sin(angle)
            
            # نقطة النهاية المحتملة
            end_x = origin[0] + dx * max_distance
            end_y = origin[1] + dy * max_distance
            
            ray = LineString([origin, (end_x, end_y)])
            
            # إيجاد أقرب تقاطع مع عائق
            closest_intersection = None
            min_distance = max_distance
            
            for obstacle in self.obstacles:
                if ray.intersects(obstacle):
                    intersection = ray.intersection(obstacle)
                    
                    if intersection.is_empty:
                        continue
                    
                    # الحصول على نقطة التقاطع
                    if hasattr(intersection, 'coords'):
                        int_point = list(intersection.coords)[0]
                    elif hasattr(intersection, 'geoms'):
                        int_point = list(intersection.geoms[0].coords)[0]
                    else:
                        continue
                    
                    # حساب المسافة
                    dist = np.sqrt(
                        (int_point[0] - origin[0])**2 +
                        (int_point[1] - origin[1])**2
                    )
                    
                    if dist < min_distance:
                        min_distance = dist
                        closest_intersection = int_point
            
            # إضافة نقطة النهاية
            if closest_intersection:
                rays_endpoints.append(closest_intersection)
            else:
                rays_endpoints.append((end_x, end_y))
        
        # إنشاء المضلع
        if len(rays_endpoints) >= 3:
            return Polygon(rays_endpoints)
        else:
            return Polygon()
    
    async def _analyze_isovist(self, polygon: Polygon) -> Dict[str, float]:
        """
        تحليل خصائص Isovist
        
        Returns:
            Area, Perimeter, Max Radial, Mean Radial, etc.
        """
        if polygon.is_empty:
            return {
                "area": 0,
                "perimeter": 0,
                "max_radial": 0,
                "mean_radial": 0,
                "compactness": 0
            }
        
        area = polygon.area
        perimeter = polygon.length
        
        # حساب الأشعة
        centroid = polygon.centroid
        coords = list(polygon.exterior.coords)
        
        radials = []
        for coord in coords:
            r = np.sqrt(
                (coord[0] - centroid.x)**2 +
                (coord[1] - centroid.y)**2
            )
            radials.append(r)
        
        max_radial = max(radials) if radials else 0
        mean_radial = np.mean(radials) if radials else 0
        
        # Compactness = 4π·Area / Perimeter²
        compactness = (4 * np.pi * area) / (perimeter**2) if perimeter > 0 else 0
        
        return {
            "area": float(area),
            "perimeter": float(perimeter),
            "max_radial": float(max_radial),
            "mean_radial": float(mean_radial),
            "compactness": float(compactness)
        }
    
    async def _build_visibility_graph(
        self,
        points: List[Tuple[float, float]],
        isovists: Dict
    ) -> nx.Graph:
        """
        بناء Visibility Graph
        عقد = نقاط العينات
        حواف = اتصالات بصرية مباشرة
        """
        vg = nx.Graph()
        
        # إضافة العقد
        for point in points:
            vg.add_node(point)
        
        # إضافة الحواف (اتصال بصري)
        threshold_distance = 50  # عتبة المسافة للاتصال
        
        for i, p1 in enumerate(points[:500]):  # حد للسرعة
            for p2 in points[i+1:500]:
                # حساب المسافة
                dist = np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
                
                if dist < threshold_distance:
                    # فحص إذا كان هناك اتصال بصري مباشر
                    if await self._has_line_of_sight(p1, p2):
                        vg.add_edge(p1, p2, weight=dist)
        
        self.visibility_graph = vg
        return vg
    
    async def _has_line_of_sight(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float]
    ) -> bool:
        """
        فحص إذا كان هناك خط رؤية مباشر بين نقطتين
        """
        line = LineString([p1, p2])
        
        for obstacle in self.obstacles:
            if line.intersects(obstacle):
                return False
        
        return True
    
    async def _calculate_vga_metrics(
        self,
        vg: nx.Graph,
        isovists: Dict
    ) -> Dict[str, Any]:
        """
        حساب مؤشرات VGA
        """
        metrics = {}
        
        # Visual Integration لكل نقطة
        for node in vg.nodes():
            try:
                # عدد النقاط المرئية مباشرة
                visible_neighbors = len(list(vg.neighbors(node)))
                
                # Isovist area
                isovist_data = isovists.get(node, {})
                isovist_area = isovist_data.get("area", 0)
                
                # Visual Integration = دالة من عدد الجيران و Isovist Area
                visual_integration = (
                    0.5 * visible_neighbors +
                    0.5 * (isovist_area / 10000)  # تطبيع
                )
                
                metrics[node] = {
                    "visual_integration": float(visual_integration),
                    "visible_neighbors": visible_neighbors,
                    "isovist_area": float(isovist_area),
                    "isovist_perimeter": float(isovist_data.get("perimeter", 0)),
                    "max_radial": float(isovist_data.get("max_radial", 0)),
                    "mean_radial": float(isovist_data.get("mean_radial", 0))
                }
                
            except Exception as e:
                logger.warning(f"Failed VGA metrics for {node}: {e}")
                metrics[node] = {
                    "visual_integration": 0,
                    "visible_neighbors": 0,
                    "isovist_area": 0
                }
        
        return metrics
    
    async def _identify_critical_visibility_points(
        self,
        vga_metrics: Dict
    ) -> Dict[str, List]:
        """
        تحديد النقاط الحرجة بصرياً
        """
        # نقاط ذات تكامل بصري عالٍ (سهلة الرؤية)
        high_integration = sorted(
            vga_metrics.items(),
            key=lambda x: x[1].get("visual_integration", 0),
            reverse=True
        )[:20]
        
        # نقاط ذات تكامل بصري منخفض (نقاط عمياء)
        low_integration = sorted(
            vga_metrics.items(),
            key=lambda x: x[1].get("visual_integration", 0)
        )[:20]
        
        # نقاط ذات Isovist Area كبيرة (رؤية واسعة)
        large_isovist = sorted(
            vga_metrics.items(),
            key=lambda x: x[1].get("isovist_area", 0),
            reverse=True
        )[:20]
        
        return {
            "high_visual_integration": [
                {"point": point, "value": data["visual_integration"]}
                for point, data in high_integration
            ],
            "blind_spots": [
                {"point": point, "value": data["visual_integration"]}
                for point, data in low_integration
            ],
            "wide_view_points": [
                {"point": point, "area": data["isovist_area"]}
                for point, data in large_isovist
            ]
        }
    
    async def _generate_visibility_summary(
        self,
        vga_metrics: Dict
    ) -> Dict[str, float]:
        """
        توليد ملخص إحصائي للرؤية
        """
        if not vga_metrics:
            return {}
        
        visual_integrations = [
            m.get("visual_integration", 0) for m in vga_metrics.values()
        ]
        isovist_areas = [
            m.get("isovist_area", 0) for m in vga_metrics.values()
        ]
        
        return {
            "mean_visual_integration": float(np.mean(visual_integrations)),
            "std_visual_integration": float(np.std(visual_integrations)),
            "min_visual_integration": float(np.min(visual_integrations)),
            "max_visual_integration": float(np.max(visual_integrations)),
            "mean_isovist_area": float(np.mean(isovist_areas)),
            "std_isovist_area": float(np.std(isovist_areas)),
            "blind_spots_count": sum(1 for v in visual_integrations if v < 0.2)
        }
