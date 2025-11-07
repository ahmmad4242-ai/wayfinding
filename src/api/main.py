"""
FastAPI Main Application - التطبيق الرئيسي
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, Dict, Any
import uuid
from pathlib import Path
import shutil
from loguru import logger

from src.config import settings, ensure_directories
from src.parser.image_processor import ImageProcessor
from src.detection.element_detector import ElementDetector
from src.analysis.metrics_calculator import MetricsCalculator
from src.analysis.area_analyzer import AreaAnalyzer
from src.wayfinding.pathfinder import PathFinder
from src.wayfinding.visibility_analyzer import VisibilityAnalyzer
from src.compliance.code_checker import CodeChecker
from src.coloranalysis.color_extractor import ColorExtractor
from src.api.models import (
    AnalysisRequest,
    AnalysisResponse,
    JobStatus,
    HealthResponse
)

# Initialize FastAPI app
app = FastAPI(
    title="Floor Plan Analyzer API",
    description="محلل مخططات الطوابق - نظام متكامل لتحليل المخططات المعمارية",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
ensure_directories()

# Jobs storage (in production, use Redis/Database)
jobs_storage: Dict[str, Dict[str, Any]] = {}


@app.on_event("startup")
async def startup_event():
    """تهيئة التطبيق عند البدء"""
    logger.info("🚀 Starting Floor Plan Analyzer API...")
    logger.info(f"Environment: {settings.fpa_env}")
    logger.info(f"API Host: {settings.api_host}:{settings.api_port}")
    

@app.on_event("shutdown")
async def shutdown_event():
    """تنظيف الموارد عند الإيقاف"""
    logger.info("🛑 Shutting down Floor Plan Analyzer API...")


@app.get("/", response_model=HealthResponse)
async def root():
    """الصفحة الرئيسية"""
    return {
        "status": "running",
        "message": "Floor Plan Analyzer API - محلل مخططات الطوابق",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/api/analyze",
            "status": "/api/status/{job_id}",
            "report": "/api/report/{job_id}",
            "docs": "/api/docs"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """فحص صحة النظام"""
    return {
        "status": "healthy",
        "message": "System is operational",
        "version": "1.0.0"
    }


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_floor_plan(
    file: UploadFile = File(...),
    scale: Optional[float] = None,
    unit: Optional[str] = "meters",
    building_type: Optional[str] = "hospital",
    enable_color_analysis: Optional[bool] = True,
    background_tasks: BackgroundTasks = None
):
    """
    تحليل مخطط طابق
    
    Args:
        file: ملف المخطط (PDF, PNG, JPG, DWG)
        scale: مقياس الرسم (مثلاً 1/100)
        unit: وحدة القياس (meters, feet)
        building_type: نوع المبنى (hospital, office, residential)
        enable_color_analysis: تفعيل التحليل اللوني
    
    Returns:
        معرف المهمة (job_id) لمتابعة التحليل
    """
    try:
        # Validate file type
        allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"نوع الملف غير مدعوم. الأنواع المدعومة: PDF, PNG, JPG"
            )
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file
        upload_path = settings.upload_dir / f"{job_id}_{file.filename}"
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"📁 File uploaded: {job_id} - {file.filename}")
        
        # Initialize job status
        jobs_storage[job_id] = {
            "status": "processing",
            "filename": file.filename,
            "upload_path": str(upload_path),
            "scale": scale,
            "unit": unit,
            "building_type": building_type,
            "enable_color_analysis": enable_color_analysis,
            "progress": 0,
            "message": "جاري المعالجة..."
        }
        
        # Start background processing
        background_tasks.add_task(
            process_floor_plan,
            job_id,
            upload_path,
            scale,
            unit,
            building_type,
            enable_color_analysis
        )
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "تم استلام الملف وبدأ التحليل",
            "estimated_time": "2-5 دقائق"
        }
        
    except Exception as e:
        logger.error(f"❌ Error in analyze_floor_plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"خطأ في معالجة الملف: {str(e)}")


@app.get("/api/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """
    الحصول على حالة المهمة
    
    Args:
        job_id: معرف المهمة
    
    Returns:
        حالة المهمة وتقدم المعالجة
    """
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")
    
    job = jobs_storage[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job.get("progress", 0),
        "message": job.get("message", ""),
        "result": job.get("result")
    }


@app.get("/api/report/{job_id}")
async def get_report(job_id: str, format: str = "json"):
    """
    الحصول على التقرير النهائي
    
    Args:
        job_id: معرف المهمة
        format: صيغة التقرير (json, pdf, csv, excel)
    
    Returns:
        التقرير بالصيغة المطلوبة
    """
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")
    
    job = jobs_storage[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="التحليل لم يكتمل بعد")
    
    if format == "json":
        return JSONResponse(content=job.get("result", {}))
    
    elif format == "pdf":
        # Generate PDF report
        pdf_path = settings.output_dir / f"{job_id}_report.pdf"
        if pdf_path.exists():
            return FileResponse(
                pdf_path,
                media_type="application/pdf",
                filename=f"floor_plan_report_{job_id}.pdf"
            )
        else:
            raise HTTPException(status_code=404, detail="تقرير PDF غير متوفر")
    
    else:
        raise HTTPException(status_code=400, detail=f"صيغة غير مدعومة: {format}")


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """حذف مهمة ومخرجاتها"""
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")
    
    job = jobs_storage[job_id]
    
    # Delete files
    try:
        upload_path = Path(job["upload_path"])
        if upload_path.exists():
            upload_path.unlink()
        
        output_path = settings.output_dir / f"{job_id}_*"
        for file in settings.output_dir.glob(f"{job_id}_*"):
            file.unlink()
        
        del jobs_storage[job_id]
        
        return {"message": "تم حذف المهمة بنجاح"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في حذف المهمة: {str(e)}")


async def process_floor_plan(
    job_id: str,
    file_path: Path,
    scale: Optional[float],
    unit: str,
    building_type: str,
    enable_color_analysis: bool
):
    """
    معالجة مخطط الطابق (خلفية)
    """
    try:
        logger.info(f"🔄 Processing job {job_id}...")
        
        # Update progress: Parsing
        jobs_storage[job_id].update({
            "progress": 10,
            "message": "تحليل الصورة واستخراج العناصر..."
        })
        
        # 1. Image Processing
        processor = ImageProcessor()
        processed_image = await processor.process(file_path)
        
        # 2. Element Detection
        jobs_storage[job_id].update({
            "progress": 30,
            "message": "اكتشاف الأبواب والجدران والغرف..."
        })
        
        detector = ElementDetector()
        elements = await detector.detect(processed_image)
        
        # 3. Area Analysis
        jobs_storage[job_id].update({
            "progress": 50,
            "message": "حساب المساحات والمقاييس..."
        })
        
        area_analyzer = AreaAnalyzer()
        areas = await area_analyzer.analyze(elements, scale, unit)
        
        # 4. Metrics Calculation
        jobs_storage[job_id].update({
            "progress": 60,
            "message": "حساب مؤشرات الأداء..."
        })
        
        metrics_calc = MetricsCalculator()
        metrics = await metrics_calc.calculate(areas, elements)
        
        # 5. Wayfinding Analysis
        jobs_storage[job_id].update({
            "progress": 70,
            "message": "تحليل التوجيه والمسارات..."
        })
        
        pathfinder = PathFinder()
        wayfinding = await pathfinder.analyze(elements, areas)
        
        visibility = VisibilityAnalyzer()
        visibility_data = await visibility.analyze(elements)
        
        # 6. Compliance Check
        jobs_storage[job_id].update({
            "progress": 80,
            "message": "فحص الامتثال للكود..."
        })
        
        checker = CodeChecker(building_type)
        compliance = await checker.check(elements, areas, metrics)
        
        # 7. Color Analysis (if enabled)
        color_data = None
        if enable_color_analysis:
            jobs_storage[job_id].update({
                "progress": 90,
                "message": "تحليل الألوان والمخطط الحراري..."
            })
            
            color_extractor = ColorExtractor()
            color_data = await color_extractor.extract(processed_image)
        
        # Compile results
        result = {
            "job_id": job_id,
            "metadata": {
                "filename": jobs_storage[job_id]["filename"],
                "scale": scale,
                "unit": unit,
                "building_type": building_type
            },
            "elements": elements,
            "areas": areas,
            "metrics": metrics,
            "wayfinding": wayfinding,
            "visibility": visibility_data,
            "compliance": compliance,
            "color_analysis": color_data
        }
        
        # Update job status
        jobs_storage[job_id].update({
            "status": "completed",
            "progress": 100,
            "message": "اكتمل التحليل بنجاح",
            "result": result
        })
        
        logger.info(f"✅ Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error processing job {job_id}: {str(e)}")
        jobs_storage[job_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"خطأ في المعالجة: {str(e)}"
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=False
    )
