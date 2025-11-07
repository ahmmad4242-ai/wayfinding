"""
Pathfinder - محلل المسارات
تحليل مسارات الحركة والتوجيه
"""
import networkx as nx
import numpy as np
from typing import Dict, List, Any
from loguru import logger


class PathFinder:
    """محلل المسارات"""
    
    def __init__(self):
        self.graph = None
    
    async def analyze(self, elements: Dict, areas: Dict) -> Dict[str, Any]:
        """
        تحليل مسارات الحركة
        
        Args:
            elements: العناصر المكتشفة
            areas: بيانات المساحات
        
        Returns:
            تحليل المسارات
        """
        try:
            logger.info("🚶 Analyzing pathfinding...")
            
            # Build room graph
            self.graph = await self._build_graph(elements)
            
            # Calculate metrics
            metrics = await self._calculate_path_metrics()
            
            # Find decision points
            decision_points = await self._find_decision_points()
            
            result = {
                "avg_path_length": metrics.get("avg_path", 0),
                "avg_turns": metrics.get("avg_turns", 0),
                "decision_points": len(decision_points),
                "decision_locations": decision_points,
                "complexity_score": await self._calculate_complexity(),
                "connectivity": metrics.get("connectivity", 0)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error analyzing pathfinding: {str(e)}")
            return {}
    
    async def _build_graph(self, elements: Dict) -> nx.Graph:
        """بناء شبكة الغرف والممرات"""
        G = nx.Graph()
        
        # Add rooms as nodes
        rooms = elements.get("rooms", [])
        for room in rooms:
            G.add_node(
                room["id"],
                pos=(room["centroid"]["x"], room["centroid"]["y"]),
                area=room["area"]
            )
        
        # Add doors as edges
        doors = elements.get("doors", [])
        for door in doors:
            if door.get("from_room") and door.get("to_room"):
                G.add_edge(
                    door["from_room"],
                    door["to_room"],
                    weight=1.0
                )
        
        return G
    
    async def _calculate_path_metrics(self) -> Dict[str, float]:
        """حساب مقاييس المسارات"""
        if not self.graph or self.graph.number_of_nodes() < 2:
            return {}
        
        # Average shortest path
        try:
            avg_path = nx.average_shortest_path_length(self.graph)
        except:
            avg_path = 0
        
        # Connectivity
        connectivity = nx.node_connectivity(self.graph) if self.graph.number_of_nodes() > 1 else 0
        
        return {
            "avg_path": round(avg_path, 2),
            "avg_turns": round(avg_path * 0.7, 2),  # Simplified
            "connectivity": connectivity
        }
    
    async def _find_decision_points(self) -> List[Dict]:
        """إيجاد نقاط القرار (التقاطعات)"""
        if not self.graph:
            return []
        
        decision_points = []
        for node in self.graph.nodes():
            degree = self.graph.degree(node)
            if degree >= 3:  # 3+ connections = decision point
                pos = self.graph.nodes[node].get("pos", (0, 0))
                decision_points.append({
                    "node": node,
                    "location": {"x": pos[0], "y": pos[1]},
                    "connections": degree
                })
        
        return decision_points
    
    async def _calculate_complexity(self) -> float:
        """حساب درجة التعقيد"""
        if not self.graph:
            return 0.0
        
        n_nodes = self.graph.number_of_nodes()
        n_edges = self.graph.number_of_edges()
        
        # Complexity based on density and branching
        if n_nodes == 0:
            return 0.0
        
        density = n_edges / (n_nodes * (n_nodes - 1) / 2) if n_nodes > 1 else 0
        avg_degree = sum(dict(self.graph.degree()).values()) / n_nodes if n_nodes > 0 else 0
        
        complexity = (density * 0.5 + avg_degree / 10 * 0.5) * 100
        
        return round(min(complexity, 100), 2)
