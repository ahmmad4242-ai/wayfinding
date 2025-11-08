"""
Academic Wayfinding Analysis API - واجهة برمجية للتحليل الأكاديمي للتوجيه

Implements comprehensive wayfinding analysis based on:
- Space Syntax (Hillier & Hanson 1984)
- Visibility Graph Analysis (Turner et al.)
- Agent-Based Simulation (Huang 2017)
- Signage Evaluation (Rousek & Hallbeck 2011)
- WES Composite Score

For hospital wayfinding optimization
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional, Dict, Any, List
import uuid
import json
from pathlib import Path
import shutil
from loguru import logger
import asyncio

# Import academic analysis modules
from src.wayfinding.space_syntax import SpaceSyntaxAnalyzer
from src.wayfinding.vga_isovists import VisibilityAnalyzer
from src.wayfinding.agent_simulation import AgentSimulator, AgentType
from src.wayfinding.signage_analyzer import SignageAnalyzer, SignageElement, Landmark, SignageType
from src.wayfinding.wes_calculator import WESCalculator, WESWeights
from src.visualization.heatmap_generator import HeatmapGenerator
from src.analysis.recommendation_engine import RecommendationEngine

# Configuration
app = FastAPI(
    title="Floor Plan Analyzer - Academic Wayfinding API",
    description="نظام متقدم لتحليل التوجيه الأكاديمي في المستشفيات",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage
jobs_storage: Dict[str, Dict[str, Any]] = {}


@app.on_event("startup")
async def startup_event():
    """تهيئة التطبيق"""
    logger.info("🚀 Starting Academic Wayfinding Analysis API...")
    logger.info("📚 Modules: Space Syntax, VGA, Agent Simulation, Signage, WES")


@app.get("/")
async def root():
    """الصفحة الرئيسية"""
    return {
        "status": "running",
        "message": "Academic Wayfinding Analysis API",
        "version": "2.0.0",
        "features": [
            "Space Syntax (Hillier)",
            "VGA & Isovists (Benedikt/Turner)",
            "Agent-Based Simulation (Huang 2017)",
            "Signage Evaluation",
            "WES Score (0-100)",
            "Heatmaps & Recommendations"
        ]
    }


@app.get("/health")
async def health_check():
    """فحص صحة النظام"""
    return {
        "status": "healthy",
        "message": "System operational",
        "version": "2.0.0"
    }


@app.post("/api/analyze/wayfinding")
async def analyze_wayfinding(
    file: UploadFile = File(...),
    scale: float = 100.0,  # pixels per meter
    scenarios: Optional[str] = None,  # JSON string of scenarios
    n_agents: int = 100,
    enable_heatmaps: bool = True,
    background_tasks: BackgroundTasks = None
):
    """
    تحليل شامل للتوجيه (Wayfinding)
    
    Args:
        file: مخطط الطابق
        scale: المقياس (بكسل/متر)
        scenarios: سيناريوهات التنقل (JSON)
        n_agents: عدد العملاء للمحاكاة
        enable_heatmaps: تفعيل الخرائط الحرارية
    
    Returns:
        معرف المهمة
    """
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Save file
        upload_path = Path(f"./uploads/{job_id}_{file.filename}")
        upload_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"📁 Uploaded: {job_id}")
        
        # Parse scenarios
        if scenarios:
            scenarios_data = json.loads(scenarios)
        else:
            # Default hospital scenarios
            scenarios_data = [
                {"name": "entrance_to_emergency", "start": "entrance", "destination": "emergency"},
                {"name": "entrance_to_radiology", "start": "entrance", "destination": "radiology"},
                {"name": "entrance_to_pharmacy", "start": "entrance", "destination": "pharmacy"}
            ]
        
        # Initialize job
        jobs_storage[job_id] = {
            "status": "processing",
            "filename": file.filename,
            "progress": 0,
            "message": "بدء التحليل الأكاديمي..."
        }
        
        # Start processing
        background_tasks.add_task(
            process_academic_analysis,
            job_id,
            upload_path,
            scale,
            scenarios_data,
            n_agents,
            enable_heatmaps
        )
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "بدأ التحليل الأكاديمي المتقدم",
            "estimated_time": "5-10 دقائق"
        }
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """الحصول على حالة المهمة"""
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")
    
    return jobs_storage[job_id]


@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    """الحصول على النتائج الكاملة"""
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")
    
    job = jobs_storage[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="التحليل لم يكتمل")
    
    return JSONResponse(content=job.get("result", {}))


@app.get("/api/heatmap/{job_id}/{heatmap_type}")
async def get_heatmap(job_id: str, heatmap_type: str):
    """
    الحصول على خريطة حرارية
    
    Types: betweenness, integration, vga, errors
    """
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")
    
    heatmap_path = Path(f"./heatmaps/{job_id}/{heatmap_type}_heatmap.png")
    
    if not heatmap_path.exists():
        raise HTTPException(status_code=404, detail="الخريطة الحرارية غير متوفرة")
    
    return FileResponse(heatmap_path, media_type="image/png")


async def process_academic_analysis(
    job_id: str,
    file_path: Path,
    scale: float,
    scenarios: List[Dict],
    n_agents: int,
    enable_heatmaps: bool
):
    """
    معالجة التحليل الأكاديمي الكامل
    """
    try:
        logger.info(f"🔬 Starting academic analysis for job {job_id}")
        
        # ============= STEP 1: Image Processing & Graph Extraction =============
        jobs_storage[job_id].update({
            "progress": 10,
            "message": "معالجة الصورة واستخراج الرسم البياني..."
        })
        
        # TODO: Implement image processing and graph extraction
        # For now, create a sample graph
        import networkx as nx
        graph = await create_sample_hospital_graph()
        
        # ============= STEP 2: Space Syntax Analysis =============
        jobs_storage[job_id].update({
            "progress": 20,
            "message": "تحليل Space Syntax..."
        })
        
        space_syntax = SpaceSyntaxAnalyzer(graph)
        ss_results = await space_syntax.analyze(graph, weighted=True)
        
        logger.info(f"✅ Space Syntax complete")
        
        # ============= STEP 3: VGA & Isovists =============
        jobs_storage[job_id].update({
            "progress": 35,
            "message": "حساب VGA والـ Isovists..."
        })
        
        # Load floor plan image
        import cv2
        floor_plan_img = cv2.imread(str(file_path))
        
        # Extract walls (simplified)
        walls = []  # TODO: Extract from image
        
        vga_analyzer = VisibilityAnalyzer(floor_plan_img, walls, scale)
        vga_results = await vga_analyzer.analyze(floor_plan_img, walls, scale)
        
        logger.info(f"✅ VGA complete")
        
        # ============= STEP 4: Signage Analysis =============
        jobs_storage[job_id].update({
            "progress": 50,
            "message": "تحليل اللافتات والمعالم..."
        })
        
        # Sample signage data
        decision_points = ["node_1", "node_2", "node_3"]
        signage_elements = await create_sample_signage()
        landmarks = await create_sample_landmarks()
        
        signage_analyzer = SignageAnalyzer(
            graph,
            decision_points,
            signage_elements,
            landmarks,
            vga_results
        )
        signage_results = await signage_analyzer.analyze()
        
        logger.info(f"✅ Signage analysis complete")
        
        # ============= STEP 5: Agent-Based Simulation =============
        jobs_storage[job_id].update({
            "progress": 65,
            "message": "محاكاة العملاء (Agent Simulation)..."
        })
        
        signage_nodes = [s.node_id for s in signage_elements]
        landmark_nodes = [l.node_id for l in landmarks]
        
        agent_sim = AgentSimulator(graph, signage_nodes, landmark_nodes)
        simulation_results = await agent_sim.simulate(graph, scenarios, n_agents_per_scenario=n_agents)
        
        logger.info(f"✅ Agent simulation complete")
        
        # ============= STEP 6: WES Calculation =============
        jobs_storage[job_id].update({
            "progress": 80,
            "message": "حساب درجة WES..."
        })
        
        wes_calc = WESCalculator()
        wes_results = await wes_calc.calculate_wes(
            ss_results,
            vga_results,
            simulation_results,
            signage_results
        )
        
        logger.info(f"✅ WES Score: {wes_results['wes_score']:.1f}/100")
        
        # ============= STEP 7: Heatmaps =============
        if enable_heatmaps:
            jobs_storage[job_id].update({
                "progress": 90,
                "message": "إنشاء الخرائط الحرارية..."
            })
            
            heatmap_gen = HeatmapGenerator(floor_plan_img, scale)
            output_dir = f"./heatmaps/{job_id}"
            heatmaps = await heatmap_gen.generate_all_heatmaps(
                ss_results,
                vga_results,
                simulation_results,
                output_dir
            )
            
            logger.info(f"✅ Heatmaps generated")
        else:
            heatmaps = {}
        
        # ============= STEP 8: Recommendations =============
        jobs_storage[job_id].update({
            "progress": 95,
            "message": "إنشاء التوصيات..."
        })
        
        rec_engine = RecommendationEngine()
        recommendations = await rec_engine.generate_recommendations(
            ss_results,
            vga_results,
            simulation_results,
            signage_results,
            wes_results
        )
        
        logger.info(f"✅ Generated {len(recommendations['all'])} recommendations")
        
        # ============= COMPILE RESULTS =============
        result = {
            "job_id": job_id,
            "metadata": {
                "filename": jobs_storage[job_id]["filename"],
                "scale": scale,
                "scenarios": scenarios,
                "n_agents": n_agents
            },
            "space_syntax": ss_results,
            "vga": vga_results,
            "signage": signage_results,
            "agent_simulation": simulation_results,
            "wes": wes_results,
            "heatmaps": heatmaps,
            "recommendations": rec_engine.format_recommendations_for_export(),
            "summary": {
                "wes_score": wes_results['wes_score'],
                "grade": wes_results['grade'],
                "interpretation": wes_results['interpretation'],
                "critical_recommendations": len(recommendations['critical']),
                "high_recommendations": len(recommendations['high']),
                "total_recommendations": len(recommendations['all'])
            }
        }
        
        # Update job
        jobs_storage[job_id].update({
            "status": "completed",
            "progress": 100,
            "message": "اكتمل التحليل الأكاديمي بنجاح ✅",
            "result": result
        })
        
        logger.info(f"✅ Job {job_id} completed successfully")
        logger.info(f"📊 WES Score: {wes_results['wes_score']:.1f}/100 ({wes_results['grade']})")
        
    except Exception as e:
        logger.error(f"❌ Error in job {job_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        jobs_storage[job_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"خطأ: {str(e)}"
        })


async def create_sample_hospital_graph() -> nx.Graph:
    """Create sample hospital graph for testing"""
    import networkx as nx
    
    G = nx.Graph()
    
    # Add nodes
    nodes = [
        "entrance", "node_1", "node_2", "node_3", "node_4",
        "emergency", "radiology", "pharmacy", "reception"
    ]
    for node in nodes:
        G.add_node(node)
    
    # Add edges with weights (distances in meters)
    edges = [
        ("entrance", "node_1", 10.0),
        ("node_1", "node_2", 15.0),
        ("node_1", "node_3", 12.0),
        ("node_2", "emergency", 8.0),
        ("node_2", "reception", 5.0),
        ("node_3", "radiology", 20.0),
        ("node_3", "node_4", 10.0),
        ("node_4", "pharmacy", 15.0)
    ]
    
    for src, dst, weight in edges:
        G.add_edge(src, dst, weight=weight)
    
    return G


async def create_sample_signage() -> List[SignageElement]:
    """Create sample signage data"""
    signage = [
        SignageElement(
            node_id="entrance",
            signage_type=SignageType.DIRECTIONAL,
            font_size_mm=40.0,
            contrast_ratio=7.0,
            lighting_lux=200.0,
            color_zone="main",
            height_cm=170.0,
            languages=["ar", "en"],
            has_icons=True,
            destinations=["Emergency", "Radiology", "Pharmacy"]
        ),
        SignageElement(
            node_id="node_1",
            signage_type=SignageType.DIRECTIONAL,
            font_size_mm=35.0,
            contrast_ratio=5.5,
            lighting_lux=150.0,
            color_zone="main",
            height_cm=170.0,
            languages=["ar", "en"],
            has_icons=True,
            destinations=["Emergency", "Radiology"]
        )
    ]
    return signage


async def create_sample_landmarks() -> List[Landmark]:
    """Create sample landmarks"""
    landmarks = [
        Landmark(
            node_id="node_1",
            landmark_type="fountain",
            distinctiveness=0.8,
            visibility_area=120.0,
            color_uniqueness=0.7
        )
    ]
    return landmarks


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main_academic:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
