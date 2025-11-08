"""
Heatmap Generator for Wayfinding Metrics Visualization

Generates visual heatmap overlays for:
- Betweenness Centrality (bottlenecks)
- Integration (spatial accessibility)
- Visual Integration (visibility quality)
- Error Hotspots (navigation difficulty)
"""

import numpy as np
import cv2
from typing import Dict, List, Any, Tuple
import logging
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
import matplotlib.cm as cm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HeatmapGenerator:
    """Generate heatmap visualizations for wayfinding metrics"""
    
    def __init__(self, floor_plan_image: np.ndarray, scale_px_per_meter: float):
        """
        Initialize heatmap generator
        
        Args:
            floor_plan_image: Base floor plan image
            scale_px_per_meter: Pixels per meter conversion
        """
        self.floor_plan = floor_plan_image
        self.scale = scale_px_per_meter
        self.height, self.width = floor_plan_image.shape[:2]
    
    async def generate_all_heatmaps(
        self,
        space_syntax_results: Dict,
        vga_results: Dict,
        agent_simulation_results: Dict,
        output_dir: str = "./heatmaps"
    ) -> Dict[str, str]:
        """Generate all heatmap types"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        heatmaps = {}
        
        # Betweenness heatmap
        logger.info("Generating betweenness heatmap...")
        betweenness_path = os.path.join(output_dir, "betweenness_heatmap.png")
        await self.generate_betweenness_heatmap(
            space_syntax_results.get('betweenness', {}),
            betweenness_path
        )
        heatmaps['betweenness'] = betweenness_path
        
        # Integration heatmap
        logger.info("Generating integration heatmap...")
        integration_path = os.path.join(output_dir, "integration_heatmap.png")
        await self.generate_integration_heatmap(
            space_syntax_results.get('integration', {}),
            integration_path
        )
        heatmaps['integration'] = integration_path
        
        # VGA heatmap
        logger.info("Generating VGA heatmap...")
        vga_path = os.path.join(output_dir, "vga_heatmap.png")
        await self.generate_vga_heatmap(
            vga_results.get('metrics', {}).get('visual_integration', {}),
            vga_path
        )
        heatmaps['vga'] = vga_path
        
        # Error hotspots
        logger.info("Generating error hotspots heatmap...")
        errors_path = os.path.join(output_dir, "error_hotspots.png")
        await self.generate_error_heatmap(
            agent_simulation_results,
            errors_path
        )
        heatmaps['errors'] = errors_path
        
        logger.info(f"All heatmaps generated in {output_dir}")
        return heatmaps
    
    async def generate_betweenness_heatmap(
        self,
        betweenness_data: Dict[str, float],
        output_path: str
    ):
        """Generate betweenness centrality heatmap (identifies bottlenecks)"""
        heatmap = await self._create_node_heatmap(
            betweenness_data,
            colormap='Reds',
            title='Betweenness Centrality (Bottlenecks)',
            label='High Traffic'
        )
        cv2.imwrite(output_path, heatmap)
    
    async def generate_integration_heatmap(
        self,
        integration_data: Dict,
        output_path: str
    ):
        """Generate integration heatmap (shows spatial accessibility)"""
        rra_data = integration_data.get('RRA', {})
        heatmap = await self._create_node_heatmap(
            rra_data,
            colormap='Greens',
            title='Integration (Spatial Accessibility)',
            label='Well Connected',
            invert=True  # Lower RRA = higher integration
        )
        cv2.imwrite(output_path, heatmap)
    
    async def generate_vga_heatmap(
        self,
        visual_integration_data: Dict[str, float],
        output_path: str
    ):
        """Generate visual integration heatmap"""
        heatmap = await self._create_point_heatmap(
            visual_integration_data,
            colormap='Blues',
            title='Visual Integration (Visibility Quality)',
            label='High Visibility'
        )
        cv2.imwrite(output_path, heatmap)
    
    async def generate_error_heatmap(
        self,
        agent_simulation_results: Dict,
        output_path: str
    ):
        """Generate error hotspots heatmap"""
        # Extract error locations from agent simulations
        error_locations = {}
        
        scenarios = agent_simulation_results.get('scenarios', {})
        for scenario_data in scenarios.values():
            for agent_result in scenario_data.get('agent_results', []):
                if agent_result.get('errors', 0) > 0:
                    path = agent_result.get('path', [])
                    for node in path:
                        error_locations[node] = error_locations.get(node, 0) + 1
        
        heatmap = await self._create_node_heatmap(
            error_locations,
            colormap='Oranges',
            title='Error Hotspots (Navigation Difficulty)',
            label='High Error Rate'
        )
        cv2.imwrite(output_path, heatmap)
    
    async def _create_node_heatmap(
        self,
        node_data: Dict[str, float],
        colormap: str = 'jet',
        title: str = '',
        label: str = '',
        invert: bool = False
    ) -> np.ndarray:
        """Create heatmap from node-based data"""
        # Create overlay
        overlay = self.floor_plan.copy()
        
        if not node_data:
            return overlay
        
        # Normalize values
        values = np.array(list(node_data.values()))
        if invert:
            values = 1.0 / (values + 0.01)
        
        vmin, vmax = values.min(), values.max()
        norm_values = (values - vmin) / (vmax - vmin + 1e-8)
        
        # Get colormap
        cmap = cm.get_cmap(colormap)
        
        # Draw colored circles at node positions
        for i, (node, value) in enumerate(node_data.items()):
            # Parse node position (assuming format "node_x_y")
            try:
                parts = node.split('_')
                if len(parts) >= 3:
                    x, y = int(parts[-2]), int(parts[-1])
                else:
                    continue
            except:
                continue
            
            # Get color
            color = cmap(norm_values[i])
            color_bgr = (int(color[2]*255), int(color[1]*255), int(color[0]*255))
            
            # Draw circle
            radius = max(10, int(norm_values[i] * 30))
            cv2.circle(overlay, (x, y), radius, color_bgr, -1)
        
        # Blend with original
        result = cv2.addWeighted(self.floor_plan, 0.6, overlay, 0.4, 0)
        
        # Add title
        if title:
            cv2.putText(result, title, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        
        return result
    
    async def _create_point_heatmap(
        self,
        point_data: Dict[str, float],
        colormap: str = 'jet',
        title: str = '',
        label: str = ''
    ) -> np.ndarray:
        """Create heatmap from point-based data (VGA)"""
        overlay = self.floor_plan.copy()
        
        if not point_data:
            return overlay
        
        # Extract points and values
        points = []
        values = []
        for point_id, value in point_data.items():
            try:
                parts = point_id.replace('point_', '').split('_')
                if len(parts) >= 2:
                    x, y = float(parts[0]), float(parts[1])
                    points.append([x, y])
                    values.append(value)
            except:
                continue
        
        if not points:
            return overlay
        
        points = np.array(points)
        values = np.array(values)
        
        # Create grid
        grid_x, grid_y = np.mgrid[0:self.width:100, 0:self.height:100]
        
        # Interpolate
        grid_z = griddata(points, values, (grid_x, grid_y), method='cubic', fill_value=0)
        
        # Normalize
        grid_z = (grid_z - grid_z.min()) / (grid_z.max() - grid_z.min() + 1e-8)
        
        # Apply colormap
        cmap = cm.get_cmap(colormap)
        colored = cmap(grid_z)
        colored = (colored[:, :, :3] * 255).astype(np.uint8)
        
        # Resize to match floor plan
        colored = cv2.resize(colored, (self.width, self.height))
        
        # Blend
        result = cv2.addWeighted(self.floor_plan, 0.6, colored, 0.4, 0)
        
        if title:
            cv2.putText(result, title, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        
        return result
