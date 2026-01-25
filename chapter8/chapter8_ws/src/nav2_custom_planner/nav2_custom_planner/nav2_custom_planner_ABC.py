"""
Fish Ros2 8.2.2 搭建规划器插件框架（上）
核心需求： 1. 按照上一小节的方法搭建navigation2_custom_planner的插件抽象基类。
Python无法直接继承 nav2_core.GlobalPlanner（它没有 Python 绑定）

2. 在这个抽象基类中实现
    - configure: 插件配置
    - cleanup: 插件清理
    - activate: 插件激活
    - deactivate: 插件停用
    - createPlan: 创建路径
"""
from abc import ABC,abstractmethod
from typing import List,Optional
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path
import rclpy
from rclpy.node import Node
from tf2_ros import Buffer
# import nav2_costmap_2d   # 注意：nav2_costmap_2d 并没有官方提供的 Python 绑定

class GlobalPlanner(ABC):
    """
    自定义全局规划器的抽象基类。（模拟 nav2_core::GlobalPlanner 接口）
    
    所有自定义规划器必须继承此类，并实现以下方法。
    """
    @abstractmethod
    def configure(
        self,
        parent: Node,  # 实际是 LifecycleNode，但 Python 中视为普通 Node
        name: str,
        tf_buffer: Buffer,
        costmap_ros: str = "/global_costmap/costmap",
        interpolation_resolution: float = 0.1, 
    ) -> bool:
        """
        初始化规划器配置。
        
        Args:
            parent: 父节点（用于日志、参数）
            name: 插件名称
            tf_buffer: TF2 缓冲区
            costmap_ros: 全局代价地图。 由于 nav2_costmap_2d 无 Python 绑定，
                        改为订阅其发布的 /global_costmap/costmap 话题，
                        获取 nav_msgs/OccupancyGrid 消息，并自行解析。
            interpolation_resolution: 路径插值分辨率（单位：米），
                                    控制路径点之间的最大距离。
                                    默认值 0.1 表示每 10cm 一个点。
        
        Returns:
            True if success, False otherwise
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """清理资源（如订阅者、定时器）"""
        pass

    @abstractmethod
    def activate(self) -> None:
        """激活规划器（启动线程、订阅等）"""
        pass

    @abstractmethod
    def deactivate(self) -> None:
        """停用规划器"""
        pass

    @abstractmethod
    def create_plan(
        self,
        start: PoseStamped,
        goal: PoseStamped,
    ) -> Optional[Path]:
        """
        从起点到目标点生成路径。
        
        Args:
            start: 起始位姿
            goal: 目标位姿
        
        Returns:
            成功时返回 Path 对象，失败返回 None
            返回的 Path.header.frame_id 应为地图坐标系（如 "map"）。
        """
        pass