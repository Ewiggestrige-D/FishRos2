"""
FishRos2 7.5.2 编写巡检控制节点_优化
核心需求: 1. 将get_pose_by_xyyaw()写成工具组，满足“高内聚、低耦合”和“关注点分离（Separation of Concerns）”原则
2. 修复 get_target_points 逻辑错误
3. 支持 Ctrl+C 优雅退出
3. 所有参数可配置（frame_id、超时等）
4. 非阻塞式导航 + spin_once
5. 完善异常处理与资源清理
6. 标准化 Docstring 和日志
7. 预留扩展接口（如 on_waypoint_reached）


核心需求：1. 替换 spin_until_future_complete → spin_once 轮询
2. 添加统一超时机制
3. 使用 ~/speech_text 自动适配命名空间
4. 返回布尔值供上层逻辑判断
5. 移除阻塞式 while 循环
"""

import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from tf2_ros import TransformListener, Buffer
from tf_transformations import euler_from_quaternion

# 导入独立工具函数
from autopatrol_robot.utils.pose_utils import get_pose_stamped
from autopatrol_interfaces.srv import SpeechText

class PatrolNode(BasicNavigator):
    def __init__(self, node_name='patrol_robot', namespace=''):
        """初始化巡逻节点。

        Args:
            node_name: 节点名称
            namespace: ROS 2 命名空间，需与 Nav2 launch 配置一致
        """
        super().__init__(node_name, namespace)
        self.get_logger().info(f"{node_name} patrol node started in namespace '{namespace}'.")

        # 声明可配置参数
        self.declare_parameter('initial_point', [0.0, 0.0, 0.0])
        self.declare_parameter('target_points', [0.0, 0.0, 0.0, 1.0, 1.0, 1.57])
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('robot_base_frame', 'base_footprint')
        self.declare_parameter('navigation_timeout_sec', 300)
        self.declare_parameter('patrol_mode', 'loop')  # 'loop' or 'once'

        # 初始化 TF 监听器
        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self)
        
        # 自动适配命名空间的服务名
        # ROS 2 支持相对服务名，自动拼接 namespace
        self.speech_client_ = self.create_client(SpeechText, '~/speech_text')

    def init_robot_pose(self):
        """从参数读取初始位姿并设置给 AMCL。"""
        init_raw = self.get_parameter('initial_point').value
        if len(init_raw) != 3:
            self.get_logger().error("initial_point must be [x, y, yaw]")
            return False

        map_frame = self.get_parameter('map_frame').value
        init_pose = get_pose_stamped(
            x=init_raw[0],
            y=init_raw[1],
            yaw=init_raw[2],
            frame_id=map_frame
        )
        self.setInitialPose(init_pose)
        self.waitUntilNav2Active()
        return True

    def get_target_points(self):
        """从参数获取目标点列表，格式为 [(x, y, yaw), ...]。"""
        raw = self.get_parameter('target_points').value
        if len(raw) % 3 != 0:
            self.get_logger().error("target_points length must be a multiple of 3!")
            return []

        points = [(raw[i], raw[i+1], raw[i+2]) for i in range(0, len(raw), 3)]
        for i, (x, y, yaw) in enumerate(points):
            self.get_logger().info(f"Loaded waypoint {i}: ({x:.2f}, {y:.2f}, {yaw:.2f})")
        return points

    def nav_to_pose(self, target_pose, timeout_sec=None):
        """导航到指定 PoseStamped，支持中断和超时。

        Args:
            target_pose: geometry_msgs.msg.PoseStamped
            timeout_sec: 超时时间（秒），默认使用参数值

        Returns:
            TaskResult: SUCCEEDED / CANCELED / FAILED
        """
        if timeout_sec is None:
            timeout_sec = self.get_parameter('navigation_timeout_sec').value

        self.goToPose(target_pose)
        start_time = self.get_clock().now()

        while not self.isTaskComplete():
            if not rclpy.ok():
                self.cancelTask()
                return TaskResult.CANCELED

            feedback = self.getFeedback()
            if feedback:
                self.get_logger().info(
                    f"Remaining distance: {feedback.distance_remaining:.2f} m"
                )

            elapsed = self.get_clock().now() - start_time
            if elapsed > Duration(seconds=timeout_sec):
                self.cancelTask()
                self.get_logger().warn("Navigation timed out.")
                return TaskResult.FAILED

            rclpy.spin_once(self, timeout_sec=0.1)

        return self.getResult()

    def get_current_pose(self, timeout_sec=1.0):
        """获取当前机器人在 map 坐标系下的位姿。

        Returns:
            tuple: (Transform, euler_angles) 或 (None, None) if failed
        """
        try:
            trans = self._tf_buffer.lookup_transform(
                self.get_parameter('map_frame').value,
                self.get_parameter('robot_base_frame').value,
                rclpy.time.Time(),  # latest
                timeout=rclpy.duration.Duration(seconds=timeout_sec)
            )
            quat = trans.transform.rotation
            euler = euler_from_quaternion([quat.x, quat.y, quat.z, quat.w])
            return trans.transform, euler
        except Exception as e:
            self.get_logger().warn(f"Failed to get current pose: {e}")
            return None, None

    def speech_text(self, text: str, timeout_sec: float = 10.0) -> bool:
        """
        调用语音合成服务并等待结果（带超时）。

        Args:
            text: 要朗读的文本
            timeout_sec: 最大等待时间（秒）

        Returns:
            bool: True 表示成功，False 表示失败或超时
        """
        if not text.strip():
            self.get_logger().warn("Empty text, skipping speech.")
            return True

        

        # 等待服务上线（带超时）
        wait_start = self.get_clock().now()
        while not self.speech_client_.service_is_ready():
            if (self.get_clock().now() - wait_start) > Duration(seconds=timeout_sec):
                self.get_logger().error(f"Speech service '~/speech_text' not available after {timeout_sec}s")
                return False
            rclpy.spin_once(self, timeout_sec=0.1)
            if not rclpy.ok():
                return False

        # 发送请求
        request = SpeechText.Request()
        request.text = text
        future = self.speech_client_.call_async(request)

        # 等待结果（非阻塞轮询）
        start_time = self.get_clock().now()
        while not future.done():
            if not rclpy.ok():
                return False

            elapsed = self.get_clock().now() - start_time
            if elapsed > Duration(seconds=timeout_sec):
                self.get_logger().error(f"Speech service call timed out after {timeout_sec}s")
                return False

            rclpy.spin_once(self, timeout_sec=0.1)

        # 处理结果
        try:
            response = future.result()
            if response.result:
                self.get_logger().info("Speech synthesis succeeded.")
                return True
            else:
                self.get_logger().error("Speech synthesis failed (service returned false).")
                return False
        except Exception as e:
            self.get_logger().error(f"Speech service call failed with exception: {e}")
            return False
        
    def on_waypoint_reached(self, index: int, point: tuple):
        """钩子函数：到达目标点后触发（预留扩展点）。"""
        self.get_logger().info(f"Waypoint {index} reached: {point}")
        # TODO: 拍照、记录、触发其他行为

def main():
    rclpy.init()
    patrol = None
    try:
        patrol = PatrolNode()
        if not patrol.init_robot_pose():
            patrol.get_logger().fatal("Failed to initialize robot pose. Exiting.")
            return
        
        patrol.speech_text("位姿初始化完成，开始巡检任务。")
        patrol_mode = patrol.get_parameter('patrol_mode').value
        loop_count = 0

        while rclpy.ok():
            points = patrol.get_target_points()
            if not points:
                patrol.get_logger().warn("No valid waypoints. Exiting.")
                patrol.speech_text("未检测到可用目标点")
                break

            patrol.get_logger().info(f"Starting patrol round {loop_count + 1}...")
            all_succeeded = True

            for i, (x, y, yaw) in enumerate(points):
                map_frame = patrol.get_parameter('map_frame').value
                target_pose = get_pose_stamped(x, y, yaw, frame_id=map_frame)
                patrol.speech_text(f"前往第 {i+1} 个目标点，坐标 {x:.1f}, {y:.1f}")
                result = patrol.nav_to_pose(target_pose)

                if result == TaskResult.SUCCEEDED:
                    patrol.on_waypoint_reached(i, (x, y, yaw))
                    patrol.speech_text(f"已到达第 {i+1} 个目标点。")
                else:
                    patrol.get_logger().error(f"Failed to reach waypoint {i}.")
                    patrol.speech_text("导航失败，任务中止。")
                    all_succeeded = False
                    break

            loop_count += 1
            if patrol_mode == 'once':
                break

    except KeyboardInterrupt:
        pass
    finally:
        if patrol:
            patrol.lifecycleShutdown()
        rclpy.shutdown()


if __name__ == '__main__':
    main()