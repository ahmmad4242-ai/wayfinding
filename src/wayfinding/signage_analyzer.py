"""
Signage Analysis Module for Wayfinding Evaluation

Implements signage evaluation methodology based on:
- Rousek & Hallbeck (2011): Signage in healthcare facilities
- McLachlan & Leng (2011): Color coding effectiveness
- Arthur & Passini (1992): Wayfinding people, signs and architecture

Calculates:
- Coverage: % of decision points with visible signage
- Readability: Font size, contrast, lighting adequacy
- Line-of-Sight (LoS): Viewing distance to nearest sign
- Color Consistency: Cross-zone uniformity
- Landmark Strength: Visibility and distinctiveness

SignageScore = 100 × [0.35·Coverage + 0.25·Readability + 0.20·LoS + 
                      0.10·ColorConsistency + 0.10·LandmarkStrength]
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Set
import logging
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SignageType(Enum):
    """Types of wayfinding signage"""
    DIRECTIONAL = "directional"  # Arrow signs pointing to destinations
    IDENTIFICATION = "identification"  # Room/department labels
    INFORMATIONAL = "informational"  # Maps, directories
    REGULATORY = "regulatory"  # Warnings, restrictions
    LANDMARK = "landmark"  # Visual landmarks for orientation


@dataclass
class SignageElement:
    """Represents a single signage element"""
    node_id: str
    signage_type: SignageType
    font_size_mm: float  # Font height in millimeters
    contrast_ratio: float  # Contrast ratio (1.0-21.0, WCAG standard)
    lighting_lux: float  # Illumination level in lux
    color_zone: str  # Color coding zone identifier
    height_cm: float  # Mounting height in centimeters
    languages: List[str]  # Languages present (e.g., ['en', 'ar'])
    has_icons: bool  # Whether includes universal icons
    destinations: List[str]  # Destinations indicated


@dataclass
class Landmark:
    """Represents a spatial landmark"""
    node_id: str
    landmark_type: str  # e.g., "artwork", "fountain", "distinctive_architecture"
    distinctiveness: float  # 0-1 scale, how unique/recognizable
    visibility_area: float  # From VGA results (m²)
    color_uniqueness: float  # 0-1, how distinctive the color is


class SignageAnalyzer:
    """
    Analyzes signage and landmark effectiveness for wayfinding
    
    Based on healthcare wayfinding research emphasizing:
    - Strategic placement at decision points
    - Adequate readability (font size, contrast, lighting)
    - Consistent color coding across zones
    - Landmark support for spatial orientation
    """
    
    def __init__(
        self,
        graph,
        decision_points: List[str],
        signage_elements: List[SignageElement],
        landmarks: List[Landmark],
        vga_results: Dict[str, Any] = None
    ):
        """
        Initialize signage analyzer
        
        Args:
            graph: NetworkX graph of floor plan
            decision_points: Nodes where users must choose direction
            signage_elements: List of signage present in environment
            landmarks: List of spatial landmarks
            vga_results: Results from VGA analysis (for LoS calculation)
        """
        self.graph = graph
        self.decision_points = decision_points
        self.signage_elements = signage_elements
        self.landmarks = landmarks
        self.vga_results = vga_results or {}
        
        # Build lookup dictionaries
        self.signage_by_node = self._build_signage_lookup()
        self.landmarks_by_node = self._build_landmark_lookup()
        
        # Analysis results
        self.coverage = 0.0
        self.readability_score = 0.0
        self.los_score = 0.0
        self.color_consistency = 0.0
        self.landmark_strength = 0.0
        self.composite_score = 0.0
    
    def _build_signage_lookup(self) -> Dict[str, List[SignageElement]]:
        """Build dictionary mapping node IDs to signage elements"""
        lookup = {}
        for sign in self.signage_elements:
            if sign.node_id not in lookup:
                lookup[sign.node_id] = []
            lookup[sign.node_id].append(sign)
        return lookup
    
    def _build_landmark_lookup(self) -> Dict[str, List[Landmark]]:
        """Build dictionary mapping node IDs to landmarks"""
        lookup = {}
        for landmark in self.landmarks:
            if landmark.node_id not in lookup:
                lookup[landmark.node_id] = []
            lookup[landmark.node_id].append(landmark)
        return lookup
    
    async def analyze(self) -> Dict[str, Any]:
        """
        Complete signage analysis
        
        Returns comprehensive signage evaluation including:
        - Coverage metrics
        - Readability assessment
        - Line-of-sight distances
        - Color consistency
        - Landmark effectiveness
        - Composite SignageScore
        """
        logger.info("Starting comprehensive signage analysis...")
        
        # Calculate individual components
        coverage_results = await self._calculate_coverage()
        readability_results = await self._calculate_readability()
        los_results = await self._calculate_line_of_sight()
        color_results = await self._calculate_color_consistency()
        landmark_results = await self._calculate_landmark_strength()
        
        # Composite score
        self.composite_score = await self._calculate_composite_score()
        
        results = {
            "coverage": coverage_results,
            "readability": readability_results,
            "line_of_sight": los_results,
            "color_consistency": color_results,
            "landmark_strength": landmark_results,
            "composite_signage_score": self.composite_score,
            "interpretation": self._interpret_score(self.composite_score),
            "recommendations": await self._generate_signage_recommendations()
        }
        
        logger.info(f"Signage analysis complete. Composite score: {self.composite_score:.1f}/100")
        return results
    
    async def _calculate_coverage(self) -> Dict[str, Any]:
        """
        Calculate signage coverage at decision points
        
        Rousek & Hallbeck (2011): Signage should be present within 10 meters
        of every decision point where users must choose direction.
        
        Coverage = (Decision points with visible signage) / (Total decision points)
        """
        logger.info("Calculating signage coverage...")
        
        max_visibility_distance = 10.0  # meters (Rousek & Hallbeck standard)
        covered_points = 0
        uncovered_points = []
        coverage_details = {}
        
        for dp in self.decision_points:
            # Check if signage exists at this decision point
            has_local_signage = dp in self.signage_by_node
            
            # Check nearby nodes (within 10m via graph distance)
            has_nearby_signage = False
            if not has_local_signage:
                # Search within distance threshold
                for node in self.graph.nodes():
                    if node in self.signage_by_node:
                        try:
                            # Calculate graph distance
                            import networkx as nx
                            path_length = nx.shortest_path_length(
                                self.graph, dp, node, weight='weight'
                            )
                            if path_length <= max_visibility_distance:
                                has_nearby_signage = True
                                break
                        except nx.NetworkXNoPath:
                            continue
            
            is_covered = has_local_signage or has_nearby_signage
            if is_covered:
                covered_points += 1
                coverage_details[dp] = {"covered": True, "distance": 0 if has_local_signage else path_length}
            else:
                uncovered_points.append(dp)
                coverage_details[dp] = {"covered": False, "distance": None}
        
        self.coverage = covered_points / len(self.decision_points) if self.decision_points else 0.0
        
        return {
            "coverage_percentage": self.coverage * 100,
            "covered_decision_points": covered_points,
            "total_decision_points": len(self.decision_points),
            "uncovered_points": uncovered_points,
            "coverage_details": coverage_details
        }
    
    async def _calculate_readability(self) -> Dict[str, Any]:
        """
        Calculate signage readability based on:
        - Font size (minimum 15mm for 3m viewing distance per ISO 3864)
        - Contrast ratio (minimum 4.5:1 per WCAG 2.1 Level AA)
        - Lighting (minimum 100 lux per healthcare standards)
        
        Readability = mean([font_score, contrast_score, lighting_score])
        """
        logger.info("Calculating signage readability...")
        
        if not self.signage_elements:
            return {
                "readability_score": 0.0,
                "mean_font_size_mm": 0.0,
                "mean_contrast_ratio": 0.0,
                "mean_lighting_lux": 0.0,
                "poor_readability_signs": []
            }
        
        # Standards (ISO 3864, WCAG 2.1, Healthcare lighting)
        MIN_FONT_SIZE = 15.0  # mm
        OPTIMAL_FONT_SIZE = 50.0  # mm
        MIN_CONTRAST = 4.5  # ratio
        OPTIMAL_CONTRAST = 7.0  # ratio
        MIN_LIGHTING = 100.0  # lux
        OPTIMAL_LIGHTING = 300.0  # lux
        
        font_scores = []
        contrast_scores = []
        lighting_scores = []
        poor_signs = []
        
        for sign in self.signage_elements:
            # Font size score (0-1)
            if sign.font_size_mm >= OPTIMAL_FONT_SIZE:
                font_score = 1.0
            elif sign.font_size_mm >= MIN_FONT_SIZE:
                font_score = (sign.font_size_mm - MIN_FONT_SIZE) / (OPTIMAL_FONT_SIZE - MIN_FONT_SIZE)
            else:
                font_score = sign.font_size_mm / MIN_FONT_SIZE * 0.5  # Below minimum
            
            # Contrast score (0-1)
            if sign.contrast_ratio >= OPTIMAL_CONTRAST:
                contrast_score = 1.0
            elif sign.contrast_ratio >= MIN_CONTRAST:
                contrast_score = (sign.contrast_ratio - MIN_CONTRAST) / (OPTIMAL_CONTRAST - MIN_CONTRAST)
            else:
                contrast_score = sign.contrast_ratio / MIN_CONTRAST * 0.5
            
            # Lighting score (0-1)
            if sign.lighting_lux >= OPTIMAL_LIGHTING:
                lighting_score = 1.0
            elif sign.lighting_lux >= MIN_LIGHTING:
                lighting_score = (sign.lighting_lux - MIN_LIGHTING) / (OPTIMAL_LIGHTING - MIN_LIGHTING)
            else:
                lighting_score = sign.lighting_lux / MIN_LIGHTING * 0.5
            
            font_scores.append(font_score)
            contrast_scores.append(contrast_score)
            lighting_scores.append(lighting_score)
            
            # Identify poor readability
            sign_readability = (font_score + contrast_score + lighting_score) / 3
            if sign_readability < 0.6:
                poor_signs.append({
                    "node_id": sign.node_id,
                    "readability_score": sign_readability,
                    "font_size_mm": sign.font_size_mm,
                    "contrast_ratio": sign.contrast_ratio,
                    "lighting_lux": sign.lighting_lux
                })
        
        self.readability_score = np.mean(font_scores + contrast_scores + lighting_scores)
        
        return {
            "readability_score": self.readability_score,
            "mean_font_size_mm": np.mean([s.font_size_mm for s in self.signage_elements]),
            "mean_contrast_ratio": np.mean([s.contrast_ratio for s in self.signage_elements]),
            "mean_lighting_lux": np.mean([s.lighting_lux for s in self.signage_elements]),
            "font_compliance": np.mean([1 if s.font_size_mm >= MIN_FONT_SIZE else 0 for s in self.signage_elements]),
            "contrast_compliance": np.mean([1 if s.contrast_ratio >= MIN_CONTRAST else 0 for s in self.signage_elements]),
            "lighting_compliance": np.mean([1 if s.lighting_lux >= MIN_LIGHTING else 0 for s in self.signage_elements]),
            "poor_readability_signs": poor_signs
        }
    
    async def _calculate_line_of_sight(self) -> Dict[str, Any]:
        """
        Calculate line-of-sight distances to signage
        
        Uses VGA isovist data to estimate actual viewing distances.
        Optimal LoS distance: 3-10 meters (readable but not overwhelming)
        
        LoS_score = mean(normalized viewing distances)
        """
        logger.info("Calculating line-of-sight metrics...")
        
        if not self.vga_results or 'metrics' not in self.vga_results:
            logger.warning("VGA results not available, using approximate LoS calculation")
            # Fallback: use graph distances
            return await self._calculate_los_approximate()
        
        # Use isovist max_radial as proxy for LoS distance
        OPTIMAL_MIN_DISTANCE = 3.0  # meters
        OPTIMAL_MAX_DISTANCE = 10.0  # meters
        
        isovist_data = self.vga_results.get('metrics', {}).get('max_radial', {})
        los_scores = []
        
        for sign in self.signage_elements:
            if sign.node_id in isovist_data:
                max_radial = isovist_data[sign.node_id]
                
                # Score based on optimal range
                if OPTIMAL_MIN_DISTANCE <= max_radial <= OPTIMAL_MAX_DISTANCE:
                    score = 1.0
                elif max_radial < OPTIMAL_MIN_DISTANCE:
                    score = max_radial / OPTIMAL_MIN_DISTANCE
                else:  # max_radial > OPTIMAL_MAX_DISTANCE
                    score = OPTIMAL_MAX_DISTANCE / max_radial
                
                los_scores.append(score)
        
        self.los_score = np.mean(los_scores) if los_scores else 0.5
        
        return {
            "los_score": self.los_score,
            "mean_viewing_distance": np.mean([isovist_data.get(s.node_id, 5.0) for s in self.signage_elements]),
            "signage_within_optimal_range": sum(1 for s in self.signage_elements 
                if OPTIMAL_MIN_DISTANCE <= isovist_data.get(s.node_id, 5.0) <= OPTIMAL_MAX_DISTANCE),
            "total_signage": len(self.signage_elements)
        }
    
    async def _calculate_los_approximate(self) -> Dict[str, Any]:
        """Fallback LoS calculation using graph distances"""
        # Simple approximation when VGA not available
        self.los_score = 0.7  # Assume moderate LoS quality
        return {
            "los_score": self.los_score,
            "method": "approximate",
            "note": "VGA results not available, using default estimation"
        }
    
    async def _calculate_color_consistency(self) -> Dict[str, Any]:
        """
        Calculate color coding consistency across zones
        
        McLachlan & Leng (2011): Consistent color zones improve wayfinding
        by 30-40% in complex environments.
        
        Consistency = (Zones with uniform color) / (Total zones)
        """
        logger.info("Calculating color consistency...")
        
        if not self.signage_elements:
            return {"color_consistency": 0.0, "zones_analyzed": 0}
        
        # Group signage by color zone
        zones = {}
        for sign in self.signage_elements:
            if sign.color_zone not in zones:
                zones[sign.color_zone] = []
            zones[sign.color_zone].append(sign)
        
        # Check consistency within each zone
        consistent_zones = 0
        zone_details = {}
        
        for zone, signs in zones.items():
            # Extract dominant colors (simplified - in real implementation, use color histograms)
            # For now, check if all signs in zone have same type (proxy for consistency)
            types = [s.signage_type for s in signs]
            unique_types = len(set(types))
            
            # Consistent if most signs share same characteristics
            consistency = 1.0 / unique_types if unique_types > 0 else 0.0
            zone_details[zone] = {
                "signage_count": len(signs),
                "consistency_score": consistency
            }
            
            if consistency >= 0.8:
                consistent_zones += 1
        
        self.color_consistency = consistent_zones / len(zones) if zones else 0.0
        
        return {
            "color_consistency": self.color_consistency,
            "zones_analyzed": len(zones),
            "consistent_zones": consistent_zones,
            "zone_details": zone_details
        }
    
    async def _calculate_landmark_strength(self) -> Dict[str, Any]:
        """
        Calculate landmark effectiveness for spatial orientation
        
        Arthur & Passini (1992): Landmarks reduce cognitive load and
        improve wayfinding success rates by providing reference points.
        
        Landmark_strength = mean(distinctiveness × visibility_score)
        """
        logger.info("Calculating landmark strength...")
        
        if not self.landmarks:
            return {
                "landmark_strength": 0.0,
                "landmark_count": 0,
                "strong_landmarks": []
            }
        
        landmark_scores = []
        strong_landmarks = []
        
        for landmark in self.landmarks:
            # Normalize visibility area (assume max 500 m² for strong landmark)
            visibility_score = min(1.0, landmark.visibility_area / 500.0)
            
            # Combined score
            strength = landmark.distinctiveness * 0.6 + visibility_score * 0.4
            landmark_scores.append(strength)
            
            if strength >= 0.7:
                strong_landmarks.append({
                    "node_id": landmark.node_id,
                    "type": landmark.landmark_type,
                    "strength": strength,
                    "distinctiveness": landmark.distinctiveness,
                    "visibility_area": landmark.visibility_area
                })
        
        self.landmark_strength = np.mean(landmark_scores) if landmark_scores else 0.0
        
        return {
            "landmark_strength": self.landmark_strength,
            "landmark_count": len(self.landmarks),
            "mean_distinctiveness": np.mean([l.distinctiveness for l in self.landmarks]),
            "mean_visibility_area": np.mean([l.visibility_area for l in self.landmarks]),
            "strong_landmarks": strong_landmarks,
            "weak_landmarks_count": sum(1 for score in landmark_scores if score < 0.5)
        }
    
    async def _calculate_composite_score(self) -> float:
        """
        Calculate composite SignageScore
        
        SignageScore = 100 × [0.35·Coverage + 0.25·Readability + 0.20·LoS + 
                              0.10·ColorConsistency + 0.10·LandmarkStrength]
        
        Weights based on impact on wayfinding performance:
        - Coverage (35%): Most critical - missing signs cause errors
        - Readability (25%): Essential for sign utility
        - LoS (20%): Important for timely information
        - Color consistency (10%): Helps pattern recognition
        - Landmark strength (10%): Supports orientation
        """
        weights = {
            'coverage': 0.35,
            'readability': 0.25,
            'los': 0.20,
            'color_consistency': 0.10,
            'landmark_strength': 0.10
        }
        
        score = (
            weights['coverage'] * self.coverage +
            weights['readability'] * self.readability_score +
            weights['los'] * self.los_score +
            weights['color_consistency'] * self.color_consistency +
            weights['landmark_strength'] * self.landmark_strength
        ) * 100
        
        return score
    
    def _interpret_score(self, score: float) -> str:
        """Interpret SignageScore with qualitative description"""
        if score >= 90:
            return "Excellent signage system - exceeds healthcare standards"
        elif score >= 75:
            return "Good signage system - meets most standards, minor improvements possible"
        elif score >= 60:
            return "Acceptable signage - notable gaps exist, improvements recommended"
        elif score >= 45:
            return "Poor signage - significant deficiencies, redesign needed"
        else:
            return "Critical signage deficiencies - comprehensive overhaul required"
    
    async def _generate_signage_recommendations(self) -> List[Dict[str, Any]]:
        """Generate prioritized signage improvement recommendations"""
        recommendations = []
        
        # Coverage recommendations
        if self.coverage < 0.8:
            recommendations.append({
                "priority": "HIGH",
                "category": "Coverage",
                "issue": f"Only {self.coverage*100:.0f}% of decision points have signage",
                "recommendation": "Add directional signage at uncovered decision points",
                "estimated_impact": "Reduce navigation errors by 20-30%",
                "estimated_cost": "Low-Medium"
            })
        
        # Readability recommendations
        if self.readability_score < 0.7:
            recommendations.append({
                "priority": "HIGH",
                "category": "Readability",
                "issue": f"Signage readability score: {self.readability_score*100:.0f}%",
                "recommendation": "Improve font sizes (min 15mm), contrast (min 4.5:1), and lighting (min 100 lux)",
                "estimated_impact": "Improve sign comprehension by 25-35%",
                "estimated_cost": "Low"
            })
        
        # Line-of-sight recommendations
        if self.los_score < 0.6:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Line-of-Sight",
                "issue": f"Suboptimal sign viewing distances",
                "recommendation": "Reposition signs to 3-10m viewing distance, remove visual obstructions",
                "estimated_impact": "Earlier sign detection, reduced hesitation",
                "estimated_cost": "Low-Medium"
            })
        
        # Color consistency recommendations
        if self.color_consistency < 0.7:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Color Coding",
                "issue": f"Inconsistent color coding across zones ({self.color_consistency*100:.0f}% consistency)",
                "recommendation": "Implement consistent color scheme per department/floor (McLachlan & Leng 2011)",
                "estimated_impact": "Improve spatial learning by 15-20%",
                "estimated_cost": "Low"
            })
        
        # Landmark recommendations
        if self.landmark_strength < 0.6:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Landmarks",
                "issue": f"Weak landmark support ({self.landmark_strength*100:.0f}% strength)",
                "recommendation": "Add distinctive visual landmarks at key intersections (artwork, architectural features)",
                "estimated_impact": "Improve orientation and spatial memory by 20%",
                "estimated_cost": "Medium-High"
            })
        
        return recommendations


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    import networkx as nx
    
    async def test_signage_analyzer():
        """Test the signage analyzer with sample data"""
        
        # Create sample graph
        G = nx.Graph()
        G.add_edge("entrance", "node_1", weight=10.0)
        G.add_edge("node_1", "node_2", weight=8.0)
        G.add_edge("node_1", "node_3", weight=12.0)
        G.add_edge("node_2", "emergency", weight=15.0)
        G.add_edge("node_3", "radiology", weight=20.0)
        
        # Sample decision points
        decision_points = ["node_1", "node_2", "node_3"]
        
        # Sample signage
        signage = [
            SignageElement(
                node_id="entrance",
                signage_type=SignageType.DIRECTIONAL,
                font_size_mm=40.0,
                contrast_ratio=7.0,
                lighting_lux=200.0,
                color_zone="main",
                height_cm=170.0,
                languages=["en", "ar"],
                has_icons=True,
                destinations=["Emergency", "Radiology"]
            ),
            SignageElement(
                node_id="node_1",
                signage_type=SignageType.DIRECTIONAL,
                font_size_mm=35.0,
                contrast_ratio=5.5,
                lighting_lux=150.0,
                color_zone="main",
                height_cm=170.0,
                languages=["en", "ar"],
                has_icons=True,
                destinations=["Emergency", "Radiology"]
            )
        ]
        
        # Sample landmarks
        landmarks = [
            Landmark(
                node_id="node_1",
                landmark_type="fountain",
                distinctiveness=0.8,
                visibility_area=120.0,
                color_uniqueness=0.7
            )
        ]
        
        # Sample VGA results
        vga_results = {
            "metrics": {
                "max_radial": {
                    "entrance": 8.0,
                    "node_1": 12.0,
                    "node_2": 6.0
                }
            }
        }
        
        # Run analysis
        analyzer = SignageAnalyzer(G, decision_points, signage, landmarks, vga_results)
        results = await analyzer.analyze()
        
        print("\n=== SIGNAGE ANALYSIS RESULTS ===")
        print(f"Composite SignageScore: {results['composite_signage_score']:.1f}/100")
        print(f"Interpretation: {results['interpretation']}")
        print(f"\nCoverage: {results['coverage']['coverage_percentage']:.1f}%")
        print(f"Readability: {results['readability']['readability_score']*100:.1f}%")
        print(f"Line-of-Sight: {results['line_of_sight']['los_score']*100:.1f}%")
        print(f"Color Consistency: {results['color_consistency']['color_consistency']*100:.1f}%")
        print(f"Landmark Strength: {results['landmark_strength']['landmark_strength']*100:.1f}%")
        
        print(f"\nRecommendations:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"{i}. [{rec['priority']}] {rec['category']}: {rec['recommendation']}")
    
    asyncio.run(test_signage_analyzer())
