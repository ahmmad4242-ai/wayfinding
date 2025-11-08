"""
Agent-Based Simulation - محاكاة سلوك المستخدم
Based on: Huang et al. (2017), Hölscher et al. (2006)
"""
import numpy as np
import networkx as nx
from typing import Dict, List, Any, Tuple, Optional
from loguru import logger
from dataclasses import dataclass
from enum import Enum


class AgentType(Enum):
    """أنواع المستخدمين"""
    FAMILIAR = "familiar"  # معتاد
    FIRST_TIME = "first_time"  # زائر لأول مرة
    ELDERLY = "elderly"  # كبار السن
    MOBILITY_IMPAIRED = "mobility_impaired"  # محدود الحركة


@dataclass
class Agent:
    """وكيل يمثل مستخدم"""
    id: str
    agent_type: AgentType
    current_position: Tuple[float, float]
    target_position: Tuple[float, float]
    path: List[Tuple[float, float]] = None
    errors: int = 0
    hesitations: int = 0
    sign_usages: int = 0
    time_elapsed: float = 0
    distance_traveled: float = 0
    success: bool = False


class AgentSimulator:
    """محاكي سلوك الوكلاء"""
    
    def __init__(self):
        self.graph = None
        self.signage_locations = []
        self.landmarks = []
        self.agents = []
    
    async def simulate(
        self,
        graph: nx.Graph,
        scenarios: List[Dict[str, Any]],
        n_agents_per_scenario: int = 100,
        signage_locations: List = None,
        landmarks: List = None
    ) -> Dict[str, Any]:
        """
        تشغيل محاكاة Agent-Based
        
        Args:
            graph: شبكة الحركة
            scenarios: سيناريوهات (مدخل → وجهة)
            n_agents_per_scenario: عدد الوكلاء لكل سيناريو
            signage_locations: مواقع الإشارات
            landmarks: المعالم البارزة
        
        Returns:
            نتائج المحاكاة
        """
        try:
            logger.info(f"🤖 Starting agent simulation with {len(scenarios)} scenarios...")
            
            self.graph = graph
            self.signage_locations = signage_locations or []
            self.landmarks = landmarks or []
            
            all_results = []
            
            for scenario in scenarios:
                origin = scenario.get("origin")
                destination = scenario.get("destination")
                scenario_name = scenario.get("name", f"{origin}->{destination}")
                
                logger.info(f"Simulating scenario: {scenario_name}")
                
                # تشغيل عدة وكلاء لنفس السيناريو
                scenario_results = await self._run_scenario(
                    origin,
                    destination,
                    n_agents_per_scenario
                )
                
                all_results.append({
                    "scenario": scenario_name,
                    "origin": origin,
                    "destination": destination,
                    **scenario_results
                })
            
            # حساب الإحصائيات الإجمالية
            overall_stats = await self._calculate_overall_stats(all_results)
            
            result = {
                "scenarios": all_results,
                "overall": overall_stats,
                "recommendations": await self._generate_recommendations(all_results)
            }
            
            logger.info("✅ Agent simulation completed")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in agent simulation: {str(e)}")
            raise
    
    async def _run_scenario(
        self,
        origin: str,
        destination: str,
        n_agents: int
    ) -> Dict[str, Any]:
        """
        تشغيل سيناريو واحد مع عدة وكلاء
        """
        agents = []
        
        # توزيع أنواع الوكلاء
        agent_types_dist = [
            (AgentType.FIRST_TIME, 0.6),
            (AgentType.FAMILIAR, 0.2),
            (AgentType.ELDERLY, 0.15),
            (AgentType.MOBILITY_IMPAIRED, 0.05)
        ]
        
        for i in range(n_agents):
            # اختيار نوع الوكيل
            agent_type = np.random.choice(
                [at for at, _ in agent_types_dist],
                p=[prob for _, prob in agent_types_dist]
            )
            
            # إنشاء وكيل
            agent = Agent(
                id=f"agent_{i}",
                agent_type=agent_type,
                current_position=self._get_node_position(origin),
                target_position=self._get_node_position(destination)
            )
            
            # تشغيل رحلة الوكيل
            await self._simulate_agent_journey(agent, origin, destination)
            
            agents.append(agent)
        
        # تجميع النتائج
        return await self._aggregate_scenario_results(agents)
    
    def _get_node_position(self, node: str) -> Tuple[float, float]:
        """الحصول على موقع عقدة"""
        if node in self.graph.nodes:
            return self.graph.nodes[node].get('pos', (0, 0))
        return (0, 0)
    
    async def _simulate_agent_journey(
        self,
        agent: Agent,
        origin: str,
        destination: str
    ):
        """
        محاكاة رحلة وكيل من الأصل للوجهة
        """
        try:
            # حساب أقصر مسار
            if origin not in self.graph or destination not in self.graph:
                agent.success = False
                return
            
            shortest_path = nx.shortest_path(
                self.graph, origin, destination, weight='weight'
            )
            
            # تطبيق قواعد اختيار المسار حسب نوع الوكيل
            actual_path = await self._apply_agent_strategy(
                agent,
                shortest_path,
                destination
            )
            
            # حساب المقاييس
            agent.path = actual_path
            agent.distance_traveled = await self._calculate_path_length(actual_path)
            agent.time_elapsed = await self._estimate_travel_time(agent, actual_path)
            agent.success = (actual_path[-1] == destination if actual_path else False)
            
        except Exception as e:
            logger.warning(f"Agent {agent.id} failed: {e}")
            agent.success = False
    
    async def _apply_agent_strategy(
        self,
        agent: Agent,
        optimal_path: List[str],
        destination: str
    ) -> List[str]:
        """
        تطبيق استراتيجية اختيار المسار حسب نوع الوكيل
        """
        actual_path = [optimal_path[0]]
        current = optimal_path[0]
        
        for i, next_node in enumerate(optimal_path[1:], 1):
            # احتمال الخطأ عند نقاط القرار
            error_prob = self._get_error_probability(agent, current)
            
            if np.random.random() < error_prob:
                # خطأ في الاختيار
                agent.errors += 1
                
                # اختيار عشوائي من الجيران
                neighbors = list(self.graph.neighbors(current))
                if neighbors:
                    wrong_choice = np.random.choice(neighbors)
                    actual_path.append(wrong_choice)
                    current = wrong_choice
                    
                    # محاولة التصحيح
                    if wrong_choice != next_node:
                        agent.hesitations += 1
                        try:
                            correction_path = nx.shortest_path(
                                self.graph, wrong_choice, destination, weight='weight'
                            )
                            actual_path.extend(correction_path[1:])
                            return actual_path
                        except:
                            return actual_path
            else:
                # اختيار صحيح
                # فحص استخدام الإشارات
                if self._signage_visible_at(current, next_node):
                    agent.sign_usages += 1
                
                actual_path.append(next_node)
                current = next_node
        
        return actual_path
    
    def _get_error_probability(self, agent: Agent, node: str) -> float:
        """
        حساب احتمال الخطأ عند عقدة
        """
        base_prob = {
            AgentType.FAMILIAR: 0.05,
            AgentType.FIRST_TIME: 0.25,
            AgentType.ELDERLY: 0.35,
            AgentType.MOBILITY_IMPAIRED: 0.30
        }
        
        prob = base_prob.get(agent.agent_type, 0.20)
        
        # زيادة الاحتمال عند عقد عالية الدرجة (تفرع كبير)
        degree = self.graph.degree(node)
        if degree >= 4:
            prob *= 1.5
        elif degree >= 3:
            prob *= 1.2
        
        # تقليل الاحتمال إذا كانت هناك إشارة
        if self._has_signage_at(node):
            prob *= 0.5
        
        # تقليل الاحتمال إذا كان هناك معلم بارز
        if self._has_landmark_at(node):
            prob *= 0.6
        
        return min(prob, 0.9)  # حد أقصى 90%
    
    def _signage_visible_at(self, current: str, next_node: str) -> bool:
        """فحص إذا كانت الإشارة مرئية"""
        # تبسيط: نفترض وجود إشارة إذا كانت في قائمة الإشارات
        return current in self.signage_locations or next_node in self.signage_locations
    
    def _has_signage_at(self, node: str) -> bool:
        """فحص وجود إشارة عند عقدة"""
        return node in self.signage_locations
    
    def _has_landmark_at(self, node: str) -> bool:
        """فحص وجود معلم عند عقدة"""
        return node in self.landmarks
    
    async def _calculate_path_length(self, path: List[str]) -> float:
        """حساب طول المسار"""
        if len(path) < 2:
            return 0
        
        total_length = 0
        for i in range(len(path) - 1):
            if path[i] in self.graph and path[i+1] in self.graph:
                if self.graph.has_edge(path[i], path[i+1]):
                    total_length += self.graph[path[i]][path[i+1]].get('weight', 1)
        
        return total_length
    
    async def _estimate_travel_time(
        self,
        agent: Agent,
        path: List[str]
    ) -> float:
        """
        تقدير زمن السفر (بالثواني)
        """
        distance = await self._calculate_path_length(path)
        
        # سرعة المشي (م/ث)
        walking_speed = {
            AgentType.FAMILIAR: 1.4,
            AgentType.FIRST_TIME: 1.0,
            AgentType.ELDERLY: 0.8,
            AgentType.MOBILITY_IMPAIRED: 0.6
        }
        
        speed = walking_speed.get(agent.agent_type, 1.0)
        
        # الزمن الأساسي
        base_time = distance / speed
        
        # إضافة زمن التوقف والتردد
        hesitation_time = agent.hesitations * 5  # 5 ثوانٍ لكل تردد
        error_time = agent.errors * 10  # 10 ثوانٍ لكل خطأ
        
        total_time = base_time + hesitation_time + error_time
        
        return total_time
    
    async def _aggregate_scenario_results(
        self,
        agents: List[Agent]
    ) -> Dict[str, Any]:
        """
        تجميع نتائج السيناريو
        """
        successful = [a for a in agents if a.success]
        
        if not agents:
            return {}
        
        return {
            "n_agents": len(agents),
            "success_rate": len(successful) / len(agents),
            "first_pass_success": sum(1 for a in agents if a.success and a.errors == 0) / len(agents),
            "mean_time": float(np.mean([a.time_elapsed for a in successful])) if successful else 0,
            "std_time": float(np.std([a.time_elapsed for a in successful])) if successful else 0,
            "mean_distance": float(np.mean([a.distance_traveled for a in successful])) if successful else 0,
            "mean_errors": float(np.mean([a.errors for a in agents])),
            "mean_hesitations": float(np.mean([a.hesitations for a in agents])),
            "mean_sign_usage": float(np.mean([a.sign_usages for a in agents])),
            "hesitation_rate": float(np.mean([
                a.hesitations / a.distance_traveled if a.distance_traveled > 0 else 0
                for a in agents
            ]))
        }
    
    async def _calculate_overall_stats(
        self,
        all_results: List[Dict]
    ) -> Dict[str, Any]:
        """
        حساب الإحصائيات الإجمالية
        """
        all_success_rates = [r.get("success_rate", 0) for r in all_results]
        all_times = [r.get("mean_time", 0) for r in all_results]
        all_errors = [r.get("mean_errors", 0) for r in all_results]
        
        return {
            "overall_success_rate": float(np.mean(all_success_rates)),
            "overall_mean_time": float(np.mean(all_times)),
            "overall_mean_errors": float(np.mean(all_errors)),
            "best_scenario": max(all_results, key=lambda x: x.get("success_rate", 0)).get("scenario"),
            "worst_scenario": min(all_results, key=lambda x: x.get("success_rate", 0)).get("scenario")
        }
    
    async def _generate_recommendations(
        self,
        all_results: List[Dict]
    ) -> List[str]:
        """
        توليد توصيات بناءً على نتائج المحاكاة
        """
        recommendations = []
        
        # السيناريوهات ذات معدل نجاح منخفض
        low_success = [r for r in all_results if r.get("success_rate", 1) < 0.7]
        if low_success:
            recommendations.append(
                f"تحسين مسارات: {', '.join([r['scenario'] for r in low_success[:3]])} "
                f"(معدل نجاح < 70%)"
            )
        
        # زمن سفر مرتفع
        high_time = [r for r in all_results if r.get("mean_time", 0) > 180]  # > 3 دقائق
        if high_time:
            recommendations.append(
                f"تقليل زمن السفر في: {', '.join([r['scenario'] for r in high_time[:3]])}"
            )
        
        # أخطاء متكررة
        high_errors = [r for r in all_results if r.get("mean_errors", 0) > 1.5]
        if high_errors:
            recommendations.append(
                f"إضافة إشارات عند: {', '.join([r['scenario'] for r in high_errors[:3]])}"
            )
        
        if not recommendations:
            recommendations.append("الأداء جيد بشكل عام - لا توصيات حرجة")
        
        return recommendations
