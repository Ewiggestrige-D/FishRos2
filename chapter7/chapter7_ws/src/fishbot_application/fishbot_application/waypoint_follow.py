"""
Fish Bot2 7.4.4使用接口完成路点导航
核心需求：在单点导航基础上实现多个途径点的导航
"""
import rclpy
import time
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.duration import Duration
from tf_transformations import quaternion_from_euler


def create_pose(x, y, yaw, frame_id, clock):
    """工具函数：创建带四元数朝向的 PoseStamped"""
    pose = PoseStamped()
    pose.header.frame_id = frame_id
    pose.header.stamp = clock.now().to_msg()
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.position.z = 0.0
    q = quaternion_from_euler(0.0, 0.0, yaw)
    pose.pose.orientation.x = q[0]
    pose.pose.orientation.y = q[1]
    pose.pose.orientation.z = q[2]
    pose.pose.orientation.w = q[3]
    return pose


def main():
    rclpy.init()
    nav = BasicNavigator()

    # === 1. 设置初始位姿（必须！）===
    nav.waitUntilNav2Active()  

    # === 2. 批量定义途经点坐标（x, y, yaw）===
    waypoint_coords = [
        (2.0, 2.0, 0.0),      # 点1
        (3.0, 1.0, 0.0),      # 点2
        (1.0, 0.5, 1.57),     # 点3（朝上）
        (0.0, 0.0, 3.14),     # 点4（朝左）
    ]

    # === 3. 批量生成 PoseStamped 列表 ===
    goal_poses = [
        create_pose(x, y, yaw, "map", nav.get_clock())
        for x, y, yaw in waypoint_coords
    ]

    # === 4. 启动多点导航 ===
    nav.followWaypoints(goal_poses)

    # === 5. 监控任务进度 ===
    start_time = nav.get_clock().now()
    while not nav.isTaskComplete():
        feedback = nav.getFeedback()
        if feedback is not None:
            nav.get_logger().info(
                f"当前执行第 {feedback.current_waypoint + 1} 个点 ，共有 {len(goal_poses)} 个点"
            )
            
            # 超时判断（总时间）
            elapsed = nav.get_clock().now() - start_time
            if elapsed > Duration(seconds=600):  # 10分钟超时
                nav.cancelTask()
                nav.get_logger().warn("❌ 总导航超时，取消任务！")
                break
        
        time.sleep(0.2)

    # === 6. 检查每个点的结果 ===
    results = nav.getResult()
    if isinstance(results, list):  # followWaypoints 返回结果列表
        for i, res in enumerate(results):
            if res == TaskResult.SUCCEEDED:
                nav.get_logger().info(f"✅ 路点 {i+1} 成功")
            elif res == TaskResult.CANCELED:
                nav.get_logger().warn(f"⚠️ 路点 {i+1} 被取消")
            else:
                nav.get_logger().error(f"❌ 路点 {i+1} 失败")

    nav.lifecycleShutdown()
    rclpy.shutdown()


if __name__ == '__main__':
    main()