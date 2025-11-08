"""
Space Syntax Analysis - تحليل بناء الفضاء
تطبيق نظرية Space Syntax لتحليل شبكة الحركة وحساب مؤشرات التكامل
Based on: Hillier & Hanson (1984), Turner (2001)
"""
import numpy as np
import networkx as nx
from typing import Dict, List, Any, Tuple, Optional
from loguru import logger
from collections import defaultdict


class SpaceSyntaxAnalyzer:
    """محلل Space Syntax المتقدم"""
    
    def __init__(self):
        self.graph = None
        self.metrics = {}
    
    async def analyze(self, graph: nx.Graph, weighted: bool = True) -> Dict[str, Any]:
        """
        تحليل Space Syntax الشامل
        
        Args:
            graph: شبكة الحركة
            weighted: استخدام الأوزان (المسافات) في الحساب
        
        Returns:
            جميع مؤشرات Space Syntax
        """
        try:
            logger.info("🔍 Starting Space Syntax analysis...")
            
            self.graph = graph
            
            # Basic metrics
            degree = await self._calculate_degree()
            closeness = await self._calculate_closeness(weighted)
            betweenness = await self._calculate_betweenness(weighted)
            
            # Space Syntax specific
            integration = await self._calculate_integration(weighted)
            choice = await self._calculate_choice(weighted)
            connectivity = await self._calculate_connectivity()
            depth = await self._calculate_depth()
            
            # Control measures
            control = await self._calculate_control()
            controllability = await self._calculate_controllability()
            
            self.metrics = {
                "degree": degree,
                "closeness": closeness,
                "betweenness": betweenness,
                "integration": integration,
                "choice": choice,
                "connectivity": connectivity,
                "depth": depth,
                "control": control,
                "controllability": controllability,
                "summary": await self._generate_summary()
            }
            
            logger.info("✅ Space Syntax analysis completed")
            return self.metrics
            
        except Exception as e:
            logger.error(f"❌ Error in Space Syntax analysis: {str(e)}")
            raise
    
    async def _calculate_degree(self) -> Dict[str, float]:
        """
        حساب درجة العقدة (Degree)
        عدد الاتصالات المباشرة
        """
        degree = {}
        for node in self.graph.nodes():
            degree[node] = self.graph.degree(node)
        return degree
    
    async def _calculate_closeness(self, weighted: bool = True) -> Dict[str, float]:
        """
        حساب القرب (Closeness Centrality)
        مؤشر سهولة الوصول من/إلى عقدة
        
        Closeness(v) = (n-1) / Σ d(v,u)
        """
        if weighted:
            closeness = nx.closeness_centrality(self.graph, distance='weight')
        else:
            closeness = nx.closeness_centrality(self.graph)
        return dict(closeness)
    
    async def _calculate_betweenness(self, weighted: bool = True) -> Dict[str, float]:
        """
        حساب الوسيطية (Betweenness Centrality)
        عدد أقصر المسارات التي تمر عبر العقدة
        
        Betweenness(v) = Σ σ(s,t|v) / σ(s,t)
        """
        if weighted:
            betweenness = nx.betweenness_centrality(self.graph, weight='weight')
        else:
            betweenness = nx.betweenness_centrality(self.graph)
        return dict(betweenness)
    
    async def _calculate_integration(self, weighted: bool = True) -> Dict[str, Any]:
        """
        حساب التكامل (Integration) - مؤشر Space Syntax الرئيسي
        
        RA (Real Asymmetry) = 2(MD - 1) / (k - 2)
        RRA (Relative Real Asymmetry) = RA / D_k
        Integration = 1 / RRA
        
        حيث:
        - MD = Mean Depth (متوسط العمق من العقدة)
        - k = عدد العقد في النظام
        - D_k = قيمة معيارية
        """
        integration = {}
        k = self.graph.number_of_nodes()
        
        # D_k values for normalization (من جداول Hillier)
        d_k = self._get_dk_value(k)
        
        for node in self.graph.nodes():
            # حساب متوسط العمق من العقدة
            if weighted:
                lengths = nx.single_source_dijkstra_path_length(
                    self.graph, node, weight='weight'
                )
            else:
                lengths = nx.single_source_shortest_path_length(self.graph, node)
            
            depths = list(lengths.values())
            if len(depths) > 1:
                md = np.mean(depths)  # Mean Depth
                
                # حساب RA و RRA
                if k > 2:
                    ra = 2 * (md - 1) / (k - 2)
                    rra = ra / d_k if d_k > 0 else ra
                    integ = 1 / rra if rra > 0 else 0
                else:
                    ra = rra = 0
                    integ = 0
                
                integration[node] = {
                    "value": float(integ),
                    "ra": float(ra),
                    "rra": float(rra),
                    "mean_depth": float(md)
                }
            else:
                integration[node] = {
                    "value": 0,
                    "ra": 0,
                    "rra": 0,
                    "mean_depth": 0
                }
        
        return integration
    
    def _get_dk_value(self, k: int) -> float:
        """
        الحصول على قيمة D_k المعيارية
        (من جداول Hillier للتطبيع)
        """
        # قيم تقريبية من الأدبيات
        if k < 3:
            return 1.0
        elif k <= 10:
            return k / 3
        elif k <= 100:
            return 2 * np.sqrt(k - 1)
        else:
            return 2 * np.log(k)
    
    async def _calculate_choice(self, weighted: bool = True) -> Dict[str, float]:
        """
        حساب الاختيار (Choice) - مرادف للوسيطية في Space Syntax
        يقيس احتمال المرور عبر عقدة في رحلة عشوائية
        """
        # Choice هو نفسه Betweenness في معظم الحالات
        return await self._calculate_betweenness(weighted)
    
    async def _calculate_connectivity(self) -> Dict[str, int]:
        """
        حساب الاتصالية (Connectivity)
        عدد الخطوات اللازمة للوصول من عقدة لأبعد عقدة
        """
        connectivity = {}
        for node in self.graph.nodes():
            try:
                eccentricity = nx.eccentricity(self.graph, node)
                connectivity[node] = eccentricity
            except:
                connectivity[node] = float('inf')
        return connectivity
    
    async def _calculate_depth(self) -> Dict[str, Dict[str, float]]:
        """
        حساب العمق (Depth) من عقد مرجعية (مداخل)
        Topological Depth = عدد الخطوات من المدخل
        """
        depth = {}
        
        # تحديد المداخل (عقد ذات درجة منخفضة أو محددة مسبقاً)
        entrances = await self._identify_entrances()
        
        for entrance in entrances:
            depths_from_entrance = nx.single_source_shortest_path_length(
                self.graph, entrance
            )
            
            for node, d in depths_from_entrance.items():
                if node not in depth:
                    depth[node] = {}
                depth[node][f"from_{entrance}"] = d
            
            # حساب متوسط العمق
            if entrances:
                for node in self.graph.nodes():
                    if node in depth:
                        avg_depth = np.mean(list(depth[node].values()))
                        depth[node]["average"] = float(avg_depth)
        
        return depth
    
    async def _identify_entrances(self) -> List[str]:
        """
        تحديد العقد التي تمثل مداخل
        (عقد ذات درجة منخفضة على الحواف)
        """
        entrances = []
        degrees = dict(self.graph.degree())
        
        # العقد ذات الدرجة 1 أو 2 على الأطراف
        for node, degree in degrees.items():
            if degree <= 2:
                # تحقق إذا كانت على الحافة (بعيدة عن المركز)
                pos = self.graph.nodes[node].get('pos', (0, 0))
                entrances.append(node)
        
        # إذا لم نجد مداخل، نأخذ عقدة عشوائية
        if not entrances and self.graph.number_of_nodes() > 0:
            entrances = [list(self.graph.nodes())[0]]
        
        return entrances[:5]  # حد أقصى 5 مداخل
    
    async def _calculate_control(self) -> Dict[str, float]:
        """
        حساب التحكم (Control)
        Control(v) = Σ 1/Degree(u) for all neighbors u of v
        
        يقيس مدى "تحكم" عقدة في جيرانها
        """
        control = {}
        
        for node in self.graph.nodes():
            control_value = 0
            neighbors = list(self.graph.neighbors(node))
            
            for neighbor in neighbors:
                neighbor_degree = self.graph.degree(neighbor)
                if neighbor_degree > 0:
                    control_value += 1.0 / neighbor_degree
            
            control[node] = float(control_value)
        
        return control
    
    async def _calculate_controllability(self) -> Dict[str, float]:
        """
        حساب القابلية للتحكم (Controllability)
        Controllability(v) = 1/n Σ 1/Degree(u)
        """
        controllability = {}
        
        for node in self.graph.nodes():
            neighbors = list(self.graph.neighbors(node))
            n = len(neighbors)
            
            if n > 0:
                total = sum(1.0 / self.graph.degree(u) for u in neighbors if self.graph.degree(u) > 0)
                controllability[node] = total / n
            else:
                controllability[node] = 0
        
        return controllability
    
    async def _generate_summary(self) -> Dict[str, Any]:
        """
        توليد ملخص الإحصائيات
        """
        summary = {}
        
        for metric_name in ["degree", "closeness", "betweenness"]:
            if metric_name in self.metrics:
                values = list(self.metrics[metric_name].values())
                if values:
                    summary[metric_name] = {
                        "mean": float(np.mean(values)),
                        "std": float(np.std(values)),
                        "min": float(np.min(values)),
                        "max": float(np.max(values)),
                        "median": float(np.median(values))
                    }
        
        # Integration summary
        if "integration" in self.metrics:
            integ_values = [v["value"] for v in self.metrics["integration"].values()]
            if integ_values:
                summary["integration"] = {
                    "mean": float(np.mean(integ_values)),
                    "std": float(np.std(integ_values)),
                    "min": float(np.min(integ_values)),
                    "max": float(np.max(integ_values))
                }
        
        return summary
    
    async def identify_critical_nodes(
        self,
        top_n: int = 10
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        تحديد العقد الحرجة بناءً على المؤشرات
        
        Returns:
            قائمة بأهم العقد لكل مؤشر
        """
        critical = {}
        
        # أعلى Betweenness (عنق الزجاجة)
        if "betweenness" in self.metrics:
            sorted_bet = sorted(
                self.metrics["betweenness"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            critical["high_betweenness"] = sorted_bet[:top_n]
        
        # أعلى Integration (سهولة الوصول)
        if "integration" in self.metrics:
            sorted_integ = sorted(
                self.metrics["integration"].items(),
                key=lambda x: x["value"],
                reverse=True
            )
            critical["high_integration"] = [
                (node, data["value"]) for node, data in sorted_integ[:top_n]
            ]
        
        # أعلى Degree (تفرع)
        if "degree" in self.metrics:
            sorted_deg = sorted(
                self.metrics["degree"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            critical["high_degree"] = sorted_deg[:top_n]
        
        return critical
    
    async def calculate_complexity_metrics(self) -> Dict[str, float]:
        """
        حساب مقاييس التعقيد المكاني
        """
        complexity = {}
        
        # متوسط درجة التفرع
        degrees = list(self.metrics.get("degree", {}).values())
        if degrees:
            complexity["mean_degree"] = float(np.mean(degrees))
            complexity["std_degree"] = float(np.std(degrees))
        
        # متوسط العمق
        if "depth" in self.metrics:
            all_depths = []
            for node_depths in self.metrics["depth"].values():
                if "average" in node_depths:
                    all_depths.append(node_depths["average"])
            
            if all_depths:
                complexity["mean_depth"] = float(np.mean(all_depths))
                complexity["max_depth"] = float(np.max(all_depths))
        
        # مؤشر التعقيد المركب
        # Complexity = w1·mean_degree + w2·max_depth + w3·(1/mean_integration)
        w1, w2, w3 = 0.4, 0.3, 0.3
        
        mean_deg = complexity.get("mean_degree", 0)
        max_dep = complexity.get("max_depth", 0)
        
        if "integration" in self.metrics:
            integ_values = [v["value"] for v in self.metrics["integration"].values()]
            mean_integ = np.mean(integ_values) if integ_values else 1
        else:
            mean_integ = 1
        
        complexity["composite_complexity"] = (
            w1 * mean_deg +
            w2 * max_dep +
            w3 * (1 / mean_integ if mean_integ > 0 else 0)
        )
        
        return complexity
