"""
Element Detector - كاشف العناصر
اكتشاف الجدران والأبواب والنوافذ والغرف
"""
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
from loguru import logger
import uuid

from src.config import settings


class ElementDetector:
    """كاشف العناصر المعمارية"""
    
    def __init__(self):
        self.min_wall_length = 50  # pixels
        self.min_door_width = 20
        self.min_room_area = 500  # pixels²
    
    async def detect(self, image: np.ndarray) -> Dict[str, Any]:
        """
        اكتشاف جميع العناصر المعمارية
        
        Args:
            image: الصورة المعالجة
        
        Returns:
            قاموس يحتوي على جميع العناصر المكتشفة
        """
        try:
            logger.info("🔍 Detecting architectural elements...")
            
            # Convert to grayscale and binary
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(
                gray, 0, 255,
                cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
            )
            
            # Detect different elements
            walls = await self._detect_walls(binary, image)
            doors = await self._detect_doors(binary, image)
            windows = await self._detect_windows(binary, image)
            rooms = await self._detect_rooms(binary, walls)
            corridors = await self._detect_corridors(rooms)
            stairs = await self._detect_stairs(binary, image)
            
            elements = {
                "walls": walls,
                "doors": doors,
                "windows": windows,
                "rooms": rooms,
                "corridors": corridors,
                "stairs": stairs,
                "elevators": []  # Would need symbol detection
            }
            
            logger.info(f"✅ Detected: {len(walls)} walls, {len(doors)} doors, "
                       f"{len(rooms)} rooms, {len(corridors)} corridors")
            
            return elements
            
        except Exception as e:
            logger.error(f"❌ Error detecting elements: {str(e)}")
            raise
    
    async def _detect_walls(
        self,
        binary: np.ndarray,
        original: np.ndarray
    ) -> List[Dict[str, Any]]:
        """اكتشاف الجدران باستخدام Hough Transform"""
        try:
            # Detect edges
            edges = cv2.Canny(binary, 50, 150, apertureSize=3)
            
            # Detect lines using Hough Transform
            lines = cv2.HoughLinesP(
                edges,
                rho=1,
                theta=np.pi/180,
                threshold=100,
                minLineLength=self.min_wall_length,
                maxLineGap=10
            )
            
            if lines is None:
                return []
            
            walls = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # Calculate wall properties
                length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                
                if length < self.min_wall_length:
                    continue
                
                wall = {
                    "id": f"W-{str(uuid.uuid4())[:8]}",
                    "start": {"x": float(x1), "y": float(y1)},
                    "end": {"x": float(x2), "y": float(y2)},
                    "length": float(length),
                    "thickness": 10.0,  # Default, would need better detection
                    "angle": float(np.degrees(np.arctan2(y2-y1, x2-x1)))
                }
                
                walls.append(wall)
            
            # Merge nearby parallel walls
            walls = await self._merge_walls(walls)
            
            return walls
            
        except Exception as e:
            logger.warning(f"⚠️ Error detecting walls: {str(e)}")
            return []
    
    async def _merge_walls(self, walls: List[Dict]) -> List[Dict]:
        """دمج الجدران المتقاربة والمتوازية"""
        if len(walls) < 2:
            return walls
        
        merged = []
        used = set()
        
        for i, wall1 in enumerate(walls):
            if i in used:
                continue
            
            current = wall1.copy()
            
            for j, wall2 in enumerate(walls[i+1:], i+1):
                if j in used:
                    continue
                
                # Check if walls are similar and close
                if await self._are_walls_mergeable(current, wall2):
                    # Merge by extending endpoints
                    current = await self._extend_wall(current, wall2)
                    used.add(j)
            
            merged.append(current)
            used.add(i)
        
        return merged
    
    async def _are_walls_mergeable(
        self,
        wall1: Dict,
        wall2: Dict,
        angle_threshold: float = 10.0,
        distance_threshold: float = 20.0
    ) -> bool:
        """فحص إمكانية دمج جدارين"""
        # Check angle similarity
        angle_diff = abs(wall1["angle"] - wall2["angle"])
        if angle_diff > angle_threshold and angle_diff < (180 - angle_threshold):
            return False
        
        # Check distance between walls
        p1 = np.array([wall1["start"]["x"], wall1["start"]["y"]])
        p2 = np.array([wall2["start"]["x"], wall2["start"]["y"]])
        distance = np.linalg.norm(p1 - p2)
        
        return distance < distance_threshold
    
    async def _extend_wall(self, wall1: Dict, wall2: Dict) -> Dict:
        """مد جدار بدمج جدار آخر"""
        # Simple implementation - take extremes
        all_points = [
            (wall1["start"]["x"], wall1["start"]["y"]),
            (wall1["end"]["x"], wall1["end"]["y"]),
            (wall2["start"]["x"], wall2["start"]["y"]),
            (wall2["end"]["x"], wall2["end"]["y"])
        ]
        
        # Find leftmost and rightmost (or topmost/bottommost)
        all_points.sort()
        
        new_wall = wall1.copy()
        new_wall["start"] = {"x": all_points[0][0], "y": all_points[0][1]}
        new_wall["end"] = {"x": all_points[-1][0], "y": all_points[-1][1]}
        
        # Recalculate length
        new_wall["length"] = np.sqrt(
            (new_wall["end"]["x"] - new_wall["start"]["x"])**2 +
            (new_wall["end"]["y"] - new_wall["start"]["y"])**2
        )
        
        return new_wall
    
    async def _detect_doors(
        self,
        binary: np.ndarray,
        original: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        اكتشاف الأبواب
        (في الإنتاج، استخدم YOLO لرموز الأبواب)
        """
        try:
            # Simplified door detection using contours
            # In production, use trained YOLO model
            
            doors = []
            
            # Find contours that might be door symbols
            contours, _ = cv2.findContours(
                binary,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Doors are typically small rectangular shapes
                if 200 < area < 2000:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Check aspect ratio (doors are elongated)
                    aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 0
                    
                    if 2 < aspect_ratio < 10:
                        door = {
                            "id": f"D-{str(uuid.uuid4())[:8]}",
                            "location": {"x": float(x + w/2), "y": float(y + h/2)},
                            "width": float(max(w, h)),
                            "swing_direction": "unknown",
                            "from_room": None,
                            "to_room": None
                        }
                        doors.append(door)
            
            return doors[:50]  # Limit to reasonable number
            
        except Exception as e:
            logger.warning(f"⚠️ Error detecting doors: {str(e)}")
            return []
    
    async def _detect_windows(
        self,
        binary: np.ndarray,
        original: np.ndarray
    ) -> List[Dict[str, Any]]:
        """اكتشاف النوافذ"""
        # Similar to doors but different pattern
        # In production, use trained model
        return []
    
    async def _detect_rooms(
        self,
        binary: np.ndarray,
        walls: List[Dict]
    ) -> List[Dict[str, Any]]:
        """اكتشاف الغرف بتحليل المساحات المغلقة"""
        try:
            # Find closed contours that represent rooms
            # Invert binary for room detection
            inverted = cv2.bitwise_not(binary)
            
            contours, hierarchy = cv2.findContours(
                inverted,
                cv2.RETR_CCOMP,
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            rooms = []
            
            for i, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                
                # Filter by minimum area
                if area < self.min_room_area:
                    continue
                
                # Get room properties
                M = cv2.moments(contour)
                if M["m00"] == 0:
                    continue
                
                cx = M["m10"] / M["m00"]
                cy = M["m01"] / M["m00"]
                
                # Get polygon points
                epsilon = 0.01 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                polygon = [
                    {"x": float(point[0][0]), "y": float(point[0][1])}
                    for point in approx
                ]
                
                perimeter = cv2.arcLength(contour, True)
                
                room = {
                    "id": f"R-{str(uuid.uuid4())[:8]}",
                    "name": None,  # Would need OCR
                    "function": None,
                    "area": float(area),
                    "perimeter": float(perimeter),
                    "centroid": {"x": float(cx), "y": float(cy)},
                    "polygon": polygon,
                    "floor_level": 0
                }
                
                rooms.append(room)
            
            # Sort by area (largest first)
            rooms.sort(key=lambda r: r["area"], reverse=True)
            
            return rooms[:100]  # Limit to reasonable number
            
        except Exception as e:
            logger.warning(f"⚠️ Error detecting rooms: {str(e)}")
            return []
    
    async def _detect_corridors(self, rooms: List[Dict]) -> List[Dict[str, Any]]:
        """تحديد الممرات من الغرف (الغرف الطويلة الضيقة)"""
        corridors = []
        
        for room in rooms:
            # Calculate aspect ratio
            x_coords = [p["x"] for p in room["polygon"]]
            y_coords = [p["y"] for p in room["polygon"]]
            
            width = max(x_coords) - min(x_coords)
            height = max(y_coords) - min(y_coords)
            
            aspect_ratio = max(width, height) / min(width, height) if min(width, height) > 0 else 0
            
            # Corridors are elongated (high aspect ratio)
            if aspect_ratio > 3:
                corridor = {
                    "id": f"C-{room['id'].split('-')[1]}",
                    "area": room["area"],
                    "width": float(min(width, height)),
                    "length": float(max(width, height)),
                    "polygon": room["polygon"]
                }
                corridors.append(corridor)
        
        return corridors
    
    async def _detect_stairs(
        self,
        binary: np.ndarray,
        original: np.ndarray
    ) -> List[Dict[str, Any]]:
        """اكتشاف السلالم (نمط خطوط متوازية)"""
        # Would need pattern matching for stair symbols
        # This is a placeholder
        return []
