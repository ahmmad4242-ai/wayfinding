"""
Pydantic Models - نماذج البيانات
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class HealthResponse(BaseModel):
    """نموذج استجابة الصحة"""
    status: str
    message: str
    version: str
    endpoints: Optional[Dict[str, str]] = None


class AnalysisRequest(BaseModel):
    """نموذج طلب التحليل"""
    scale: Optional[float] = Field(None, description="مقياس الرسم")
    unit: str = Field("meters", description="وحدة القياس")
    building_type: str = Field("hospital", description="نوع المبنى")
    enable_color_analysis: bool = Field(True, description="تفعيل التحليل اللوني")


class AnalysisResponse(BaseModel):
    """نموذج استجابة التحليل"""
    job_id: str
    status: str
    message: str
    estimated_time: Optional[str] = None


class JobStatus(BaseModel):
    """نموذج حالة المهمة"""
    job_id: str
    status: str
    progress: int
    message: str
    result: Optional[Dict[str, Any]] = None


class Point(BaseModel):
    """نقطة ثنائية الأبعاد"""
    x: float
    y: float


class BoundingBox(BaseModel):
    """صندوق محيط"""
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    width: float
    height: float


class Room(BaseModel):
    """غرفة"""
    id: str
    name: Optional[str] = None
    function: Optional[str] = None
    area: float
    perimeter: float
    centroid: Point
    polygon: List[Point]
    floor_level: int = 0


class Door(BaseModel):
    """باب"""
    id: str
    width: float
    location: Point
    swing_direction: Optional[str] = None
    from_room: Optional[str] = None
    to_room: Optional[str] = None


class Window(BaseModel):
    """نافذة"""
    id: str
    width: float
    height: float
    location: Point
    room_id: Optional[str] = None


class Wall(BaseModel):
    """جدار"""
    id: str
    start: Point
    end: Point
    thickness: float
    length: float


class Corridor(BaseModel):
    """ممر"""
    id: str
    area: float
    width: float
    length: float
    polygon: List[Point]


class Stair(BaseModel):
    """درج"""
    id: str
    location: Point
    width: float
    type: str  # straight, spiral, L-shaped


class Elevator(BaseModel):
    """مصعد"""
    id: str
    location: Point
    capacity: Optional[int] = None


class Elements(BaseModel):
    """جميع العناصر المستخرجة"""
    rooms: List[Room] = []
    doors: List[Door] = []
    windows: List[Window] = []
    walls: List[Wall] = []
    corridors: List[Corridor] = []
    stairs: List[Stair] = []
    elevators: List[Elevator] = []


class AreaMetrics(BaseModel):
    """مقاييس المساحات"""
    gfa: float = Field(..., description="إجمالي مساحة الطابق")
    nia: float = Field(..., description="صافي المساحة الداخلية")
    gla: float = Field(..., description="المساحة الإجمالية القابلة للتأجير")
    efficiency: float = Field(..., description="كفاءة المساحة = NIA/GFA")
    circulation_ratio: float = Field(..., description="نسبة الممرات")
    total_rooms: int
    total_corridors: int


class WayfindingMetrics(BaseModel):
    """مقاييس التوجيه"""
    avg_path_length: float
    avg_turns: float
    decision_points: int
    visibility_integration_index: float
    complexity_score: float


class EgressMetrics(BaseModel):
    """مقاييس الإخلاء"""
    max_travel_distance: float
    min_required_exits: int
    actual_exits: int
    bottlenecks: List[Dict[str, Any]] = []
    compliant: bool


class ComplianceResult(BaseModel):
    """نتيجة فحص الامتثال"""
    code: str
    category: str
    requirement: str
    actual_value: Any
    required_value: Any
    compliant: bool
    severity: str  # critical, warning, info


class ColorInfo(BaseModel):
    """معلومات اللون"""
    rgb: List[int]
    hex: str
    percentage: float
    name: Optional[str] = None


class ColorAnalysis(BaseModel):
    """تحليل الألوان"""
    dominant_colors: List[ColorInfo]
    color_palette: List[ColorInfo]
    brightness_avg: float
    contrast_ratio: float
    heatmap_url: Optional[str] = None
