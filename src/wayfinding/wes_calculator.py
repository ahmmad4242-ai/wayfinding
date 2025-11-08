"""
WES (Wayfinding Efficiency Score) Calculator

Implements composite wayfinding evaluation based on:
- Travel time (T)
- Detour ratio (DI)
- Navigation errors (W)
- Hesitations (H)
- Visual integration (VI)
- Signage quality (S)
- Accessibility (A)

WES = 100 - α₁·T_norm - α₂·DI_norm - α₃·W_norm - α₄·H_norm 
      + β₁·VI_norm + β₂·S_norm + β₃·A_norm

Score interpretation:
- 90-100: Excellent wayfinding (research-grade design)
- 75-89: Good wayfinding (minor improvements needed)
- 60-74: Acceptable wayfinding (notable issues exist)
- 45-59: Poor wayfinding (significant redesign needed)
- 0-44: Critical wayfinding (fundamental problems)
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class WESWeights:
    """Configurable weights for WES calculation"""
    # Negative factors (penalties)
    time: float = 15.0  # α₁: Travel time impact
    detour: float = 10.0  # α₂: Detour ratio impact
    errors: float = 20.0  # α₃: Navigation errors impact
    hesitations: float = 10.0  # α₄: Hesitation impact
    
    # Positive factors (bonuses)
    visual_integration: float = 20.0  # β₁: Visibility quality impact
    signage: float = 15.0  # β₂: Signage quality impact
    accessibility: float = 10.0  # β₃: Accessibility impact
    
    def validate(self) -> bool:
        """Ensure weights sum to 100"""
        total = (self.time + self.detour + self.errors + self.hesitations +
                self.visual_integration + self.signage + self.accessibility)
        return abs(total - 100.0) < 0.01


@dataclass
class NormalizationBenchmarks:
    """Domain-specific benchmarks for metric normalization"""
    # Healthcare facility benchmarks (based on literature)
    max_acceptable_time: float = 300.0  # seconds (5 minutes)
    max_acceptable_detour: float = 1.5  # ratio (50% longer than optimal)
    max_acceptable_errors: float = 3.0  # number of wrong turns
    max_acceptable_hesitations: float = 5.0  # number of stops
    
    min_visual_integration: float = 0.3  # minimum acceptable VI
    max_visual_integration: float = 0.9  # excellent VI
    
    min_signage_score: float = 40.0  # minimum acceptable signage (out of 100)
    max_signage_score: float = 95.0  # excellent signage
    
    min_accessibility_score: float = 0.5  # minimum accessibility
    max_accessibility_score: float = 1.0  # full accessibility


class WESCalculator:
    """
    Calculates composite Wayfinding Efficiency Score (WES)
    
    Integrates multiple wayfinding performance metrics into a single
    interpretable score (0-100) with evidence-based interpretation.
    """
    
    def __init__(
        self,
        weights: Optional[WESWeights] = None,
        benchmarks: Optional[NormalizationBenchmarks] = None
    ):
        """
        Initialize WES calculator
        
        Args:
            weights: Custom weights for WES components (default: research-based)
            benchmarks: Custom normalization benchmarks (default: healthcare standards)
        """
        self.weights = weights or WESWeights()
        self.benchmarks = benchmarks or NormalizationBenchmarks()
        
        if not self.weights.validate():
            logger.warning("Weights do not sum to 100, normalizing...")
            self._normalize_weights()
        
        logger.info("WES Calculator initialized with validated weights")
    
    def _normalize_weights(self):
        """Ensure weights sum to 100"""
        total = (self.weights.time + self.weights.detour + self.weights.errors +
                self.weights.hesitations + self.weights.visual_integration +
                self.weights.signage + self.weights.accessibility)
        
        self.weights.time = (self.weights.time / total) * 100
        self.weights.detour = (self.weights.detour / total) * 100
        self.weights.errors = (self.weights.errors / total) * 100
        self.weights.hesitations = (self.weights.hesitations / total) * 100
        self.weights.visual_integration = (self.weights.visual_integration / total) * 100
        self.weights.signage = (self.weights.signage / total) * 100
        self.weights.accessibility = (self.weights.accessibility / total) * 100
    
    async def calculate_wes(
        self,
        space_syntax_results: Dict[str, Any],
        vga_results: Dict[str, Any],
        agent_simulation_results: Dict[str, Any],
        signage_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate complete WES score with detailed breakdown
        
        Args:
            space_syntax_results: Results from Space Syntax analysis
            vga_results: Results from VGA/Isovists analysis
            agent_simulation_results: Results from agent-based simulation
            signage_results: Results from signage analysis
        
        Returns:
            Complete WES analysis including:
            - Overall WES score (0-100)
            - Normalized component scores
            - Interpretation
            - Comparison to benchmarks
            - Improvement priorities
        """
        logger.info("Starting WES calculation...")
        
        # Extract raw metrics
        raw_metrics = await self._extract_raw_metrics(
            space_syntax_results,
            vga_results,
            agent_simulation_results,
            signage_results
        )
        
        # Normalize metrics (0-1 range)
        normalized_metrics = await self._normalize_metrics(raw_metrics)
        
        # Calculate WES score
        wes_score = await self._compute_wes_score(normalized_metrics)
        
        # Interpret score
        interpretation = self._interpret_wes(wes_score)
        
        # Identify improvement priorities
        priorities = await self._identify_improvement_priorities(normalized_metrics)
        
        # Compare to benchmarks
        benchmark_comparison = await self._compare_to_benchmarks(raw_metrics)
        
        results = {
            "wes_score": wes_score,
            "interpretation": interpretation,
            "grade": self._get_grade(wes_score),
            "normalized_metrics": normalized_metrics,
            "raw_metrics": raw_metrics,
            "component_contributions": self._calculate_component_contributions(normalized_metrics),
            "improvement_priorities": priorities,
            "benchmark_comparison": benchmark_comparison,
            "weights_used": {
                "time": self.weights.time,
                "detour": self.weights.detour,
                "errors": self.weights.errors,
                "hesitations": self.weights.hesitations,
                "visual_integration": self.weights.visual_integration,
                "signage": self.weights.signage,
                "accessibility": self.weights.accessibility
            }
        }
        
        logger.info(f"WES calculation complete. Score: {wes_score:.1f}/100 ({interpretation})")
        return results
    
    async def _extract_raw_metrics(
        self,
        space_syntax_results: Dict[str, Any],
        vga_results: Dict[str, Any],
        agent_simulation_results: Dict[str, Any],
        signage_results: Dict[str, Any]
    ) -> Dict[str, float]:
        """Extract raw metric values from analysis results"""
        
        # Agent simulation metrics (aggregate across all scenarios)
        scenarios = agent_simulation_results.get('scenarios', {})
        if scenarios:
            # Average across all scenarios
            mean_time = np.mean([s['aggregate_metrics']['mean_time'] 
                                for s in scenarios.values()])
            mean_detour = np.mean([s['aggregate_metrics'].get('detour_index', 1.0) 
                                  for s in scenarios.values()])
            mean_errors = np.mean([s['aggregate_metrics']['mean_errors'] 
                                  for s in scenarios.values()])
            mean_hesitations = np.mean([s['aggregate_metrics']['mean_hesitations'] 
                                       for s in scenarios.values()])
        else:
            mean_time = 0.0
            mean_detour = 1.0
            mean_errors = 0.0
            mean_hesitations = 0.0
        
        # VGA metrics
        vga_metrics = vga_results.get('summary_statistics', {})
        visual_integration = vga_metrics.get('mean_visual_integration', 0.5)
        
        # Signage metrics
        signage_score = signage_results.get('composite_signage_score', 50.0)
        
        # Accessibility (from Space Syntax - use mean integration as proxy)
        integration_data = space_syntax_results.get('integration', {})
        mean_integration = integration_data.get('mean_integration', 0.5)
        accessibility = mean_integration  # Higher integration = better accessibility
        
        return {
            'mean_time': mean_time,
            'mean_detour': mean_detour,
            'mean_errors': mean_errors,
            'mean_hesitations': mean_hesitations,
            'visual_integration': visual_integration,
            'signage_score': signage_score,
            'accessibility': accessibility
        }
    
    async def _normalize_metrics(self, raw_metrics: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize all metrics to 0-1 range using domain benchmarks
        
        For negative metrics (time, detour, errors, hesitations):
        - 0 = worst (at or above benchmark maximum)
        - 1 = best (zero/optimal)
        
        For positive metrics (visual integration, signage, accessibility):
        - 0 = worst (at or below benchmark minimum)
        - 1 = best (at or above benchmark maximum)
        """
        normalized = {}
        
        # Time normalization (inverse - lower is better)
        if raw_metrics['mean_time'] <= 0:
            normalized['time'] = 1.0
        elif raw_metrics['mean_time'] >= self.benchmarks.max_acceptable_time:
            normalized['time'] = 0.0
        else:
            normalized['time'] = 1.0 - (raw_metrics['mean_time'] / self.benchmarks.max_acceptable_time)
        
        # Detour normalization (inverse - closer to 1.0 is better)
        detour_excess = max(0, raw_metrics['mean_detour'] - 1.0)
        max_excess = self.benchmarks.max_acceptable_detour - 1.0
        if detour_excess >= max_excess:
            normalized['detour'] = 0.0
        else:
            normalized['detour'] = 1.0 - (detour_excess / max_excess)
        
        # Errors normalization (inverse - fewer is better)
        if raw_metrics['mean_errors'] >= self.benchmarks.max_acceptable_errors:
            normalized['errors'] = 0.0
        else:
            normalized['errors'] = 1.0 - (raw_metrics['mean_errors'] / self.benchmarks.max_acceptable_errors)
        
        # Hesitations normalization (inverse - fewer is better)
        if raw_metrics['mean_hesitations'] >= self.benchmarks.max_acceptable_hesitations:
            normalized['hesitations'] = 0.0
        else:
            normalized['hesitations'] = 1.0 - (raw_metrics['mean_hesitations'] / self.benchmarks.max_acceptable_hesitations)
        
        # Visual integration normalization (direct - higher is better)
        vi_range = self.benchmarks.max_visual_integration - self.benchmarks.min_visual_integration
        if raw_metrics['visual_integration'] <= self.benchmarks.min_visual_integration:
            normalized['visual_integration'] = 0.0
        elif raw_metrics['visual_integration'] >= self.benchmarks.max_visual_integration:
            normalized['visual_integration'] = 1.0
        else:
            normalized['visual_integration'] = (
                (raw_metrics['visual_integration'] - self.benchmarks.min_visual_integration) / vi_range
            )
        
        # Signage normalization (direct - higher is better)
        signage_range = self.benchmarks.max_signage_score - self.benchmarks.min_signage_score
        if raw_metrics['signage_score'] <= self.benchmarks.min_signage_score:
            normalized['signage'] = 0.0
        elif raw_metrics['signage_score'] >= self.benchmarks.max_signage_score:
            normalized['signage'] = 1.0
        else:
            normalized['signage'] = (
                (raw_metrics['signage_score'] - self.benchmarks.min_signage_score) / signage_range
            )
        
        # Accessibility normalization (direct - higher is better)
        access_range = self.benchmarks.max_accessibility_score - self.benchmarks.min_accessibility_score
        if raw_metrics['accessibility'] <= self.benchmarks.min_accessibility_score:
            normalized['accessibility'] = 0.0
        elif raw_metrics['accessibility'] >= self.benchmarks.max_accessibility_score:
            normalized['accessibility'] = 1.0
        else:
            normalized['accessibility'] = (
                (raw_metrics['accessibility'] - self.benchmarks.min_accessibility_score) / access_range
            )
        
        return normalized
    
    async def _compute_wes_score(self, normalized_metrics: Dict[str, float]) -> float:
        """
        Calculate WES using weighted formula
        
        WES = 100 - α₁·(1-T_norm) - α₂·(1-DI_norm) - α₃·(1-W_norm) - α₄·(1-H_norm)
              + β₁·VI_norm + β₂·S_norm + β₃·A_norm
        
        Note: We use (1 - norm) for negative factors because normalized values
        are already inverted (1 = good, 0 = bad). This formula ensures:
        - High normalized scores (good performance) reduce penalties
        - Low normalized scores (poor performance) increase penalties
        """
        
        # Penalty components (higher normalized = lower penalty)
        time_penalty = self.weights.time * (1.0 - normalized_metrics['time'])
        detour_penalty = self.weights.detour * (1.0 - normalized_metrics['detour'])
        error_penalty = self.weights.errors * (1.0 - normalized_metrics['errors'])
        hesitation_penalty = self.weights.hesitations * (1.0 - normalized_metrics['hesitations'])
        
        # Bonus components (higher normalized = higher bonus)
        vi_bonus = self.weights.visual_integration * normalized_metrics['visual_integration']
        signage_bonus = self.weights.signage * normalized_metrics['signage']
        accessibility_bonus = self.weights.accessibility * normalized_metrics['accessibility']
        
        # Composite score
        wes = 100.0 - (time_penalty + detour_penalty + error_penalty + hesitation_penalty)
        wes += (vi_bonus + signage_bonus + accessibility_bonus)
        
        # Clamp to 0-100 range
        wes = max(0.0, min(100.0, wes))
        
        return wes
    
    def _interpret_wes(self, wes_score: float) -> str:
        """Provide qualitative interpretation of WES score"""
        if wes_score >= 90:
            return "ممتاز - تصميم استثنائي يتجاوز المعايير البحثية | Excellent - Exceptional design exceeding research standards"
        elif wes_score >= 75:
            return "جيد - أداء قوي مع إمكانية تحسينات طفيفة | Good - Strong performance with minor improvement opportunities"
        elif wes_score >= 60:
            return "مقبول - أداء معقول مع وجود مشاكل ملحوظة | Acceptable - Reasonable performance with notable issues"
        elif wes_score >= 45:
            return "ضعيف - مشاكل كبيرة تتطلب إعادة تصميم | Poor - Significant problems requiring redesign"
        else:
            return "حرج - قصور جوهري يتطلب إصلاح شامل | Critical - Fundamental deficiencies requiring comprehensive overhaul"
    
    def _get_grade(self, wes_score: float) -> str:
        """Convert WES score to letter grade"""
        if wes_score >= 90:
            return "A+"
        elif wes_score >= 85:
            return "A"
        elif wes_score >= 80:
            return "A-"
        elif wes_score >= 75:
            return "B+"
        elif wes_score >= 70:
            return "B"
        elif wes_score >= 65:
            return "B-"
        elif wes_score >= 60:
            return "C+"
        elif wes_score >= 55:
            return "C"
        elif wes_score >= 50:
            return "C-"
        elif wes_score >= 45:
            return "D"
        else:
            return "F"
    
    def _calculate_component_contributions(self, normalized_metrics: Dict[str, float]) -> Dict[str, float]:
        """Calculate how much each component contributes to final WES"""
        contributions = {}
        
        # Negative contributions (penalties)
        contributions['time_impact'] = -self.weights.time * (1.0 - normalized_metrics['time'])
        contributions['detour_impact'] = -self.weights.detour * (1.0 - normalized_metrics['detour'])
        contributions['errors_impact'] = -self.weights.errors * (1.0 - normalized_metrics['errors'])
        contributions['hesitations_impact'] = -self.weights.hesitations * (1.0 - normalized_metrics['hesitations'])
        
        # Positive contributions (bonuses)
        contributions['visual_integration_impact'] = self.weights.visual_integration * normalized_metrics['visual_integration']
        contributions['signage_impact'] = self.weights.signage * normalized_metrics['signage']
        contributions['accessibility_impact'] = self.weights.accessibility * normalized_metrics['accessibility']
        
        return contributions
    
    async def _identify_improvement_priorities(
        self,
        normalized_metrics: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Identify which components most need improvement"""
        priorities = []
        
        # Calculate impact of improving each component
        for metric, value in normalized_metrics.items():
            # Skip if already excellent
            if value >= 0.9:
                continue
            
            # Calculate potential improvement
            current_score = value
            potential_improvement = 1.0 - current_score
            
            # Get weight for this metric
            weight = getattr(self.weights, metric.replace('_', '_'))
            
            # Calculate impact on WES if improved to 0.9
            impact_score = potential_improvement * weight * 0.9
            
            priorities.append({
                'metric': metric,
                'current_normalized': current_score,
                'improvement_potential': potential_improvement,
                'impact_on_wes': impact_score,
                'priority': 'HIGH' if impact_score > 5 else 'MEDIUM' if impact_score > 2 else 'LOW'
            })
        
        # Sort by impact
        priorities.sort(key=lambda x: x['impact_on_wes'], reverse=True)
        
        return priorities
    
    async def _compare_to_benchmarks(self, raw_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Compare metrics to domain benchmarks"""
        comparison = {}
        
        comparison['time'] = {
            'value': raw_metrics['mean_time'],
            'benchmark': self.benchmarks.max_acceptable_time,
            'meets_standard': raw_metrics['mean_time'] <= self.benchmarks.max_acceptable_time,
            'percentage_of_benchmark': (raw_metrics['mean_time'] / self.benchmarks.max_acceptable_time) * 100
        }
        
        comparison['detour'] = {
            'value': raw_metrics['mean_detour'],
            'benchmark': self.benchmarks.max_acceptable_detour,
            'meets_standard': raw_metrics['mean_detour'] <= self.benchmarks.max_acceptable_detour,
            'percentage_of_benchmark': (raw_metrics['mean_detour'] / self.benchmarks.max_acceptable_detour) * 100
        }
        
        comparison['errors'] = {
            'value': raw_metrics['mean_errors'],
            'benchmark': self.benchmarks.max_acceptable_errors,
            'meets_standard': raw_metrics['mean_errors'] <= self.benchmarks.max_acceptable_errors,
            'percentage_of_benchmark': (raw_metrics['mean_errors'] / self.benchmarks.max_acceptable_errors) * 100
        }
        
        comparison['hesitations'] = {
            'value': raw_metrics['mean_hesitations'],
            'benchmark': self.benchmarks.max_acceptable_hesitations,
            'meets_standard': raw_metrics['mean_hesitations'] <= self.benchmarks.max_acceptable_hesitations,
            'percentage_of_benchmark': (raw_metrics['mean_hesitations'] / self.benchmarks.max_acceptable_hesitations) * 100
        }
        
        comparison['visual_integration'] = {
            'value': raw_metrics['visual_integration'],
            'min_benchmark': self.benchmarks.min_visual_integration,
            'max_benchmark': self.benchmarks.max_visual_integration,
            'meets_standard': raw_metrics['visual_integration'] >= self.benchmarks.min_visual_integration
        }
        
        comparison['signage'] = {
            'value': raw_metrics['signage_score'],
            'min_benchmark': self.benchmarks.min_signage_score,
            'max_benchmark': self.benchmarks.max_signage_score,
            'meets_standard': raw_metrics['signage_score'] >= self.benchmarks.min_signage_score
        }
        
        comparison['accessibility'] = {
            'value': raw_metrics['accessibility'],
            'min_benchmark': self.benchmarks.min_accessibility_score,
            'max_benchmark': self.benchmarks.max_accessibility_score,
            'meets_standard': raw_metrics['accessibility'] >= self.benchmarks.min_accessibility_score
        }
        
        # Count how many benchmarks are met
        total_benchmarks = len(comparison)
        met_benchmarks = sum(1 for c in comparison.values() if c['meets_standard'])
        
        comparison['summary'] = {
            'total_benchmarks': total_benchmarks,
            'met_benchmarks': met_benchmarks,
            'compliance_percentage': (met_benchmarks / total_benchmarks) * 100
        }
        
        return comparison
    
    async def compare_scenarios(
        self,
        scenario_wes_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """Compare WES scores across multiple scenarios or designs"""
        
        if not scenario_wes_scores:
            return {}
        
        scores = list(scenario_wes_scores.values())
        
        comparison = {
            'best_scenario': max(scenario_wes_scores, key=scenario_wes_scores.get),
            'worst_scenario': min(scenario_wes_scores, key=scenario_wes_scores.get),
            'best_score': max(scores),
            'worst_score': min(scores),
            'mean_score': np.mean(scores),
            'std_deviation': np.std(scores),
            'score_range': max(scores) - min(scores),
            'all_scenarios': scenario_wes_scores
        }
        
        return comparison


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_wes_calculator():
        """Test WES calculator with sample data"""
        
        # Sample analysis results
        space_syntax = {
            "integration": {
                "mean_integration": 0.68
            }
        }
        
        vga = {
            "summary_statistics": {
                "mean_visual_integration": 0.72
            }
        }
        
        agent_sim = {
            "scenarios": {
                "entrance_to_emergency": {
                    "aggregate_metrics": {
                        "mean_time": 180.5,
                        "mean_errors": 1.8,
                        "mean_hesitations": 2.3,
                        "detour_index": 1.25
                    }
                },
                "entrance_to_radiology": {
                    "aggregate_metrics": {
                        "mean_time": 245.2,
                        "mean_errors": 2.4,
                        "mean_hesitations": 3.1,
                        "detour_index": 1.35
                    }
                }
            }
        }
        
        signage = {
            "composite_signage_score": 68.5
        }
        
        # Calculate WES
        calculator = WESCalculator()
        results = await calculator.calculate_wes(space_syntax, vga, agent_sim, signage)
        
        print("\n=== WES CALCULATION RESULTS ===")
        print(f"WES Score: {results['wes_score']:.1f}/100 (Grade: {results['grade']})")
        print(f"Interpretation: {results['interpretation']}")
        
        print("\nComponent Contributions:")
        for component, value in results['component_contributions'].items():
            print(f"  {component}: {value:+.1f}")
        
        print("\nImprovement Priorities:")
        for i, priority in enumerate(results['improvement_priorities'][:3], 1):
            print(f"  {i}. [{priority['priority']}] {priority['metric']}: "
                  f"Impact if improved: +{priority['impact_on_wes']:.1f} WES points")
        
        print("\nBenchmark Compliance:")
        summary = results['benchmark_comparison']['summary']
        print(f"  Met {summary['met_benchmarks']}/{summary['total_benchmarks']} "
              f"benchmarks ({summary['compliance_percentage']:.0f}%)")
    
    asyncio.run(test_wes_calculator())
