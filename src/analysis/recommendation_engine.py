"""
Recommendation Engine for Wayfinding Improvements

Generates prioritized, evidence-based recommendations based on:
- Space Syntax analysis
- VGA metrics
- Agent simulation results
- Signage evaluation
- WES score components

Categories:
- Quick Wins: Low-cost, high-impact (signage, color coding)
- Structural Changes: Higher-cost, transformative (circulation, visibility)
"""

import numpy as np
from typing import Dict, List, Any, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecommendationCategory(Enum):
    QUICK_WIN = "quick_win"
    STRUCTURAL = "structural"
    ACCESSIBILITY = "accessibility"
    SIGNAGE = "signage"
    SPATIAL = "spatial"


class RecommendationPriority(Enum):
    CRITICAL = "critical"  # WES impact > 10 points
    HIGH = "high"  # WES impact 5-10 points
    MEDIUM = "medium"  # WES impact 2-5 points
    LOW = "low"  # WES impact < 2 points


@dataclass
class Recommendation:
    """Structured recommendation"""
    priority: RecommendationPriority
    category: RecommendationCategory
    title_ar: str
    title_en: str
    description_ar: str
    description_en: str
    issue: str
    estimated_wes_impact: float
    estimated_cost: str  # "Low", "Medium", "High"
    implementation_difficulty: str  # "Easy", "Moderate", "Difficult"
    implementation_time: str  # "Days", "Weeks", "Months"
    affected_locations: List[str]
    supporting_evidence: Dict[str, Any]


class RecommendationEngine:
    """
    Generates prioritized wayfinding improvement recommendations
    
    Based on comprehensive analysis of all wayfinding metrics
    """
    
    def __init__(self):
        """Initialize recommendation engine"""
        self.recommendations = []
    
    async def generate_recommendations(
        self,
        space_syntax_results: Dict[str, Any],
        vga_results: Dict[str, Any],
        agent_simulation_results: Dict[str, Any],
        signage_results: Dict[str, Any],
        wes_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive recommendations
        
        Returns prioritized list of actionable improvements
        """
        logger.info("Generating wayfinding recommendations...")
        
        self.recommendations = []
        
        # Analyze each component
        await self._analyze_space_syntax(space_syntax_results, wes_results)
        await self._analyze_vga(vga_results, wes_results)
        await self._analyze_agent_simulation(agent_simulation_results, wes_results)
        await self._analyze_signage(signage_results, wes_results)
        await self._analyze_wes_priorities(wes_results)
        
        # Sort by priority and impact
        self.recommendations.sort(
            key=lambda r: (
                ['critical', 'high', 'medium', 'low'].index(r.priority.value),
                -r.estimated_wes_impact
            )
        )
        
        # Categorize
        categorized = {
            'critical': [r for r in self.recommendations if r.priority == RecommendationPriority.CRITICAL],
            'high': [r for r in self.recommendations if r.priority == RecommendationPriority.HIGH],
            'medium': [r for r in self.recommendations if r.priority == RecommendationPriority.MEDIUM],
            'low': [r for r in self.recommendations if r.priority == RecommendationPriority.LOW],
            'quick_wins': [r for r in self.recommendations if r.category == RecommendationCategory.QUICK_WIN],
            'structural': [r for r in self.recommendations if r.category == RecommendationCategory.STRUCTURAL],
            'all': self.recommendations
        }
        
        logger.info(f"Generated {len(self.recommendations)} recommendations")
        return categorized
    
    async def _analyze_space_syntax(self, results: Dict, wes_results: Dict):
        """Generate recommendations from Space Syntax analysis"""
        # Check bottlenecks
        critical_nodes = results.get('critical_nodes', {})
        bottlenecks = critical_nodes.get('bottlenecks', [])
        
        if len(bottlenecks) > 3:
            self.recommendations.append(Recommendation(
                priority=RecommendationPriority.HIGH,
                category=RecommendationCategory.STRUCTURAL,
                title_ar="معالجة الاختناقات المرورية",
                title_en="Address Traffic Bottlenecks",
                description_ar=f"تم تحديد {len(bottlenecks)} نقطة اختناق رئيسية. توسيع الممرات أو إضافة مسارات بديلة.",
                description_en=f"Identified {len(bottlenecks)} major bottleneck points. Widen corridors or add alternative routes.",
                issue=f"High betweenness at {len(bottlenecks)} nodes causing congestion",
                estimated_wes_impact=8.5,
                estimated_cost="High",
                implementation_difficulty="Difficult",
                implementation_time="Months",
                affected_locations=bottlenecks[:5],
                supporting_evidence={"betweenness_nodes": bottlenecks}
            ))
        
        # Check integration
        integration = results.get('integration', {})
        mean_integration = integration.get('mean_integration', 0.5)
        
        if mean_integration < 0.6:
            self.recommendations.append(Recommendation(
                priority=RecommendationPriority.MEDIUM,
                category=RecommendationCategory.STRUCTURAL,
                title_ar="تحسين التكامل المكاني",
                title_en="Improve Spatial Integration",
                description_ar="التصميم يظهر عمقاً مكانياً عالياً. إضافة ممرات اتصال أو اختصارات.",
                description_en="Design shows high spatial depth. Add connecting corridors or shortcuts.",
                issue=f"Low mean integration ({mean_integration:.2f})",
                estimated_wes_impact=6.0,
                estimated_cost="High",
                implementation_difficulty="Difficult",
                implementation_time="Months",
                affected_locations=[],
                supporting_evidence={"mean_integration": mean_integration}
            ))
    
    async def _analyze_vga(self, results: Dict, wes_results: Dict):
        """Generate recommendations from VGA analysis"""
        summary = results.get('summary_statistics', {})
        blind_spot_pct = summary.get('blind_spot_percentage', 0)
        
        if blind_spot_pct > 15:
            critical_points = results.get('critical_points', {})
            blind_spots = critical_points.get('blind_spots', [])
            
            self.recommendations.append(Recommendation(
                priority=RecommendationPriority.HIGH,
                category=RecommendationCategory.STRUCTURAL,
                title_ar="إزالة النقاط العمياء",
                title_en="Remove Blind Spots",
                description_ar=f"{blind_spot_pct:.0f}% من المساحة تعاني من رؤية منخفضة. إزالة عوائق أو إضافة نوافذ.",
                description_en=f"{blind_spot_pct:.0f}% of space has low visibility. Remove obstructions or add windows.",
                issue=f"High blind spot percentage ({blind_spot_pct:.0f}%)",
                estimated_wes_impact=7.5,
                estimated_cost="Medium",
                implementation_difficulty="Moderate",
                implementation_time="Weeks",
                affected_locations=blind_spots[:5],
                supporting_evidence={"blind_spot_percentage": blind_spot_pct}
            ))
    
    async def _analyze_agent_simulation(self, results: Dict, wes_results: Dict):
        """Generate recommendations from agent simulation"""
        scenarios = results.get('scenarios', {})
        
        for scenario_name, scenario_data in scenarios.items():
            metrics = scenario_data.get('aggregate_metrics', {})
            
            # High error rate
            mean_errors = metrics.get('mean_errors', 0)
            if mean_errors > 2.0:
                self.recommendations.append(Recommendation(
                    priority=RecommendationPriority.CRITICAL,
                    category=RecommendationCategory.QUICK_WIN,
                    title_ar=f"تقليل الأخطاء في مسار: {scenario_name}",
                    title_en=f"Reduce Errors on Route: {scenario_name}",
                    description_ar=f"معدل خطأ عالي ({mean_errors:.1f}). إضافة لافتات توجيهية في نقاط القرار.",
                    description_en=f"High error rate ({mean_errors:.1f}). Add directional signage at decision points.",
                    issue=f"Mean errors: {mean_errors:.1f}",
                    estimated_wes_impact=12.0,
                    estimated_cost="Low",
                    implementation_difficulty="Easy",
                    implementation_time="Days",
                    affected_locations=[scenario_name],
                    supporting_evidence={"mean_errors": mean_errors, "scenario": scenario_name}
                ))
            
            # Low first-pass success
            first_pass = metrics.get('first_pass_success_rate', 1.0)
            if first_pass < 0.6:
                self.recommendations.append(Recommendation(
                    priority=RecommendationPriority.HIGH,
                    category=RecommendationCategory.SIGNAGE,
                    title_ar=f"تحسين نجاح المرور الأول: {scenario_name}",
                    title_en=f"Improve First-Pass Success: {scenario_name}",
                    description_ar=f"فقط {first_pass*100:.0f}% يصلون بدون أخطاء. تحسين اللافتات والمعالم.",
                    description_en=f"Only {first_pass*100:.0f}% reach without errors. Improve signage and landmarks.",
                    issue=f"First-pass success: {first_pass*100:.0f}%",
                    estimated_wes_impact=9.0,
                    estimated_cost="Low-Medium",
                    implementation_difficulty="Easy",
                    implementation_time="Days-Weeks",
                    affected_locations=[scenario_name],
                    supporting_evidence={"first_pass_success": first_pass, "scenario": scenario_name}
                ))
    
    async def _analyze_signage(self, results: Dict, wes_results: Dict):
        """Generate recommendations from signage analysis"""
        coverage = results.get('coverage', {})
        coverage_pct = coverage.get('coverage_percentage', 0)
        
        if coverage_pct < 80:
            uncovered = coverage.get('uncovered_points', [])
            self.recommendations.append(Recommendation(
                priority=RecommendationPriority.CRITICAL,
                category=RecommendationCategory.QUICK_WIN,
                title_ar="زيادة تغطية اللافتات",
                title_en="Increase Signage Coverage",
                description_ar=f"فقط {coverage_pct:.0f}% من نقاط القرار بها لافتات. إضافة لافتات في النقاط المفقودة.",
                description_en=f"Only {coverage_pct:.0f}% of decision points have signage. Add signs at missing points.",
                issue=f"Coverage: {coverage_pct:.0f}%",
                estimated_wes_impact=15.0,
                estimated_cost="Low",
                implementation_difficulty="Easy",
                implementation_time="Days",
                affected_locations=uncovered[:5],
                supporting_evidence={"coverage_percentage": coverage_pct, "uncovered_points": uncovered}
            ))
        
        # Readability issues
        readability = results.get('readability', {})
        readability_score = readability.get('readability_score', 1.0)
        
        if readability_score < 0.7:
            self.recommendations.append(Recommendation(
                priority=RecommendationPriority.HIGH,
                category=RecommendationCategory.QUICK_WIN,
                title_ar="تحسين وضوح اللافتات",
                title_en="Improve Signage Readability",
                description_ar="اللافتات تعاني من ضعف الوضوح. زيادة حجم الخط، التباين، والإضاءة.",
                description_en="Signs have poor readability. Increase font size, contrast, and lighting.",
                issue=f"Readability score: {readability_score*100:.0f}%",
                estimated_wes_impact=10.0,
                estimated_cost="Low",
                implementation_difficulty="Easy",
                implementation_time="Days",
                affected_locations=[],
                supporting_evidence={"readability_score": readability_score}
            ))
    
    async def _analyze_wes_priorities(self, wes_results: Dict):
        """Generate recommendations from WES improvement priorities"""
        priorities = wes_results.get('improvement_priorities', [])
        
        for priority in priorities[:3]:  # Top 3
            metric = priority['metric']
            impact = priority['impact_on_wes']
            
            if metric == 'errors' and priority['priority'] == 'HIGH':
                self.recommendations.append(Recommendation(
                    priority=RecommendationPriority.CRITICAL,
                    category=RecommendationCategory.SIGNAGE,
                    title_ar="معالجة الأخطاء الملاحية - أولوية قصوى",
                    title_en="Address Navigation Errors - Top Priority",
                    description_ar=f"الأخطاء الملاحية لها أعلى تأثير على WES (+{impact:.1f} نقطة إذا تحسنت).",
                    description_en=f"Navigation errors have highest WES impact (+{impact:.1f} points if improved).",
                    issue=f"Errors metric needs improvement",
                    estimated_wes_impact=impact,
                    estimated_cost="Low",
                    implementation_difficulty="Easy",
                    implementation_time="Days",
                    affected_locations=[],
                    supporting_evidence=priority
                ))
    
    def format_recommendations_for_export(self) -> List[Dict[str, Any]]:
        """Format recommendations for JSON export"""
        formatted = []
        for rec in self.recommendations:
            formatted.append({
                'priority': rec.priority.value,
                'category': rec.category.value,
                'title': {
                    'ar': rec.title_ar,
                    'en': rec.title_en
                },
                'description': {
                    'ar': rec.description_ar,
                    'en': rec.description_en
                },
                'issue': rec.issue,
                'estimated_wes_impact': rec.estimated_wes_impact,
                'estimated_cost': rec.estimated_cost,
                'implementation_difficulty': rec.implementation_difficulty,
                'implementation_time': rec.implementation_time,
                'affected_locations': rec.affected_locations,
                'supporting_evidence': rec.supporting_evidence
            })
        return formatted
