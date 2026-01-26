# src/nav2_custom_planner/planners/my_planner.py
"""
Fish Ros2 8.2.2 搭建规划器插件框架（下）
核心需求：1. 逐行对应 C++ 实现 CustomPlanner 的 Python 版本。
2. 
| C++ 行 | Python 实现 | 说明 |
|-------|------------|------|
| `costmap_ros->getCostmap()` | `_costmap_callback` + `_costmap` | 通过订阅获取地图 |
| `costmap_->worldToMap()` | `_world_to_map()` | 手动实现坐标转换 |
| `costmap_->getCost()` | `_get_cost()` | 查询栅格值 |
| `LETHAL_OBSTACLE` | `== 100` | ROS 2 中 100 表示致命障碍 |
| `declare_parameter_if_not_declared` | `declare_parameter` | Python 等效方法 |
| `throw PlannerException` | `raise PlannerException` | 需安装 `nav2_core` Python 包 |

Fish Ros2 8.2.3 实现自定义规划算法
核心需求：1. 实现直线路径规划算法
"""

from typing import Optional, List
import math
from geometry_msgs.msg import PoseStamped, Pose
from nav_msgs.msg import Path, OccupancyGrid
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile
from tf2_ros import Buffer
from rclpy.subscription import Subscription
# from nav2_core.exceptions import PlannerException  # 注意：需安装 nav2_core>=1.0.10

# 自定义 PlannerException（因 nav2_core.exceptions 可能不可用）
class PlannerException(Exception):
    """Navigation2 规划器异常的 Python 等效类"""
    pass


class CustomPlanner:
    """
    该类不继承任何基类（duck typing），但必须实现以下公有方法：
    - configure
    - cleanup
    - activate
    - deactivate
    - create_plan
    
    用于注册为 nav2_core.global_planner 插件。
    """

    def __init__(self) -> None:
        """初始化成员变量（对应 C++ 成员变量）"""
        self._node: Optional[Node] = None
        self._name: str = ""
        self._tf_buffer: Optional[Buffer] = None
        self._costmap: Optional[OccupancyGrid] = None
        self._global_frame: str = "map"
        self._interpolation_resolution: float = 0.1
        self._costmap_sub = None

    def configure(
        self,
        parent: Node,
        name: str,
        tf_buffer: Buffer,
        costmap_topic: str = "/global_costmap/costmap",
    ) -> None:
        """
        配置插件（对应 C++ configure 方法）。
        
        Args:
            parent: 父节点（LifecycleNode 的弱引用，在 Python 中直接传入 Node）
            name: 插件实例名称
            tf_buffer: TF2 坐标变换缓冲区（当前未使用，保留接口一致性）
            costmap_topic: 全局代价地图话题，默认为 "/global_costmap/costmap"
        """
        self._node = parent
        self._name = name
        self._tf_buffer = tf_buffer

        # 声明并获取 interpolation_resolution 参数,确保返回 float（对应 C++ declare_parameter_if_not_declared）
        param_resolution = f"{name}.interpolation_resolution"
        self._node.declare_parameter(param_resolution, 0.1)
        self._interpolation_resolution = float (
            self._node.get_parameter(param_resolution).value
        )

        # 订阅代价地图（替代 C++ 中的 costmap_ros->getCostmap()）
        qos = QoSProfile(
            depth=1,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL
        )
        self._costmap_sub = self._node.create_subscription(
            OccupancyGrid,
            costmap_topic,
            self._costmap_callback,
            qos
        )

        self._node.get_logger().info(
            f"Configured plugin {self._name} with interpolation_resolution={self._interpolation_resolution}"
        )

    def _costmap_callback(self, msg: OccupancyGrid) -> None:
        """缓存最新的代价地图（对应 C++ costmap_ros->getCostmap()）"""
        self._costmap = msg
        self._global_frame = msg.header.frame_id

    def cleanup(self) -> None:
        """清理资源（对应 C++ cleanup）"""
        if self._costmap_sub:
            self._node.destroy_subscription(self._costmap_sub)
        self._node.get_logger().info(
            f"正在清理类型为 MyPlanner 的插件 {self._name}"
        )

    def activate(self) -> None:
        """激活插件（对应 C++ activate）"""
        self._node.get_logger().info(
            f"正在激活类型为 MyPlanner 的插件 {self._name}"
        )

    def deactivate(self) -> None:
        """停用插件（对应 C++ deactivate）"""
        self._node.get_logger().info(
            f"正在停用类型为 MyPlanner 的插件 {self._name}"
        )

    def _world_to_map(self, x: float, y: float) -> Optional[tuple[int, int]]:
        """
        将世界坐标 (x, y) 转换为栅格坐标 (i, j)。
        
        对应 C++ costmap_->worldToMap()。
        
        Returns:
            (i, j) 栅格坐标，若超出地图范围则返回 None。
        """
        if self._costmap is None:
            return None

        origin = self._costmap.info.origin
        resolution = self._costmap.info.resolution
        width = self._costmap.info.width
        height = self._costmap.info.height

        j = int((x - origin.position.x) / resolution)
        i = int((y - origin.position.y) / resolution)

        if 0 <= i < height and 0 <= j < width:
            return (i, j)
        else:
            return None

    def _get_cost(self, x: float, y: float) -> int:
        """
        获取世界坐标 (x, y) 处的代价值。
        
        对应 C++ costmap_->getCost(mx, my)。
        
        Returns:
            栅格值：-1=未知, 0=空闲, 1～100=占据（100=致命障碍物）
        """
        coord = self._world_to_map(x, y)
        if coord is None or self._costmap is None:
            return 100  # 超出地图视为致命障碍

        i, j = coord
        index = i * self._costmap.info.width + j
        return self._costmap.data[index]

    def create_plan(
        self,
        start: PoseStamped,
        goal: PoseStamped,
    ) -> Path:
        """
        生成从起点到目标点的路径（对应 C++ createPlan）。
        
        Args:
            start: 起始位姿
            goal: 目标位姿
        
        Returns:
            路径对象（即使失败也返回 Path，但可能为空）
            
        Raises:
            PlannerException: 当路径穿过致命障碍物时抛出（对应 C++ throw）
        """
        # 1. 声明并初始化 global_path
        global_path = Path()
        global_path.header.stamp = self._node.get_clock().now().to_msg()
        global_path.header.frame_id = self._global_frame
        global_path.poses = [] 

        # 2. 检查坐标系是否在全局坐标系中
        if start.header.frame_id != self._global_frame:
            self._node.get_logger().error(
                f"规划器仅接受来自 {self._global_frame} 坐标系的起始位置"
            )
            return global_path

        if goal.header.frame_id != self._global_frame:
            self._node.get_logger().info(
                f"规划器仅接受来自 {self._global_frame} 坐标系的目标位置"
            )
            return global_path

        # 3. 计算当前插值分辨率 interpolation_resolution_ 下的循环次数和步进值
        dx = goal.pose.position.x - start.pose.position.x
        dy = goal.pose.position.y - start.pose.position.y
        distance = math.hypot(dx, dy)

        if distance < 1e-6:
            # 起点与终点重合
            global_path.poses.append(goal)
            return global_path

        total_number_of_loop = max(1, int(distance / self._interpolation_resolution))
        x_increment = dx / total_number_of_loop
        y_increment = dy / total_number_of_loop

        # 4. 生成路径点
        for i in range(total_number_of_loop):
            pose = PoseStamped()
            pose.header.stamp = self._node.get_clock().now().to_msg()
            pose.header.frame_id = self._global_frame
            pose.pose.position.x = start.pose.position.x + x_increment * i
            pose.pose.position.y = start.pose.position.y + y_increment * i
            pose.pose.position.z = 0.0
            pose.pose.orientation = start.pose.orientation
            # 将该点放到路径中
            global_path.poses.append(pose)

        # 5. 检查路径是否经过致命障碍物（值 == 100）
        for pose in global_path.poses:
            # 将点的坐标转换为栅格坐标下的cost
            cost = self._get_cost(pose.pose.position.x, pose.pose.position.y)
            if cost == 100:  # LETHAL_OBSTACLE
                msg = f"在({pose.pose.position.x:.2f},{pose.pose.position.y:.2f})检测到致命障碍物，规划失败。"
                self._node.get_logger().warn(msg)
                raise PlannerException(
                    f"无法创建目标规划: {goal.pose.position.x}, {goal.pose.position.y}"
                )

        # 6. 收尾，将目标点作为路径的最后一个点并返回路径
        goal_pose = PoseStamped()
        goal_pose.header.stamp = self._node.get_clock().now().to_msg()
        goal_pose.header.frame_id = self._global_frame
        goal_pose.pose = goal.pose
        global_path.poses.append(goal_pose)

        return global_path