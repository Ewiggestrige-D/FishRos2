"""
Fish Bot2 7.4.3调用接口进行单点导航
核心需求：1. 单点导航：机器人能够根据指定的目标点进行导航。
2. 超时处理：如果导航超过设定的时间，则自动取消任务。
3. 反馈与日志记录：实时提供导航进度的反馈，并在导航完成后给出结果。
4. 资源管理：确保程序退出时正确关闭所有资源。

需求：单点导航→ 反馈与日志记录
│
├─ 创建 BasicNavigator 实例 → BasicNavigator()
├─ 创建 PoseStamped 对象 → goal_pose = PoseStamped()
├─ 设置目标点 → goal_pose.pose.position.x/y
├─ 发送目标点给导航器 → nav.goToPose(goal_pose)
├─ 获取反馈信息 → nav.get_logger()
└─ 最终结果判断 → result = nav.getResult()
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.duration import Duration
import time

def main():
    # 初始化 ROS 2 客户端
    rclpy.init()
    nav = BasicNavigator()

    # 等待 Nav2 全套系统就绪（包括 costmap、planner、controller 等）
    nav.waitUntilNav2Active()  # 设置最大等待时间

    # 设置目标点
    goal_pose = PoseStamped()
    goal_pose.header.frame_id = "map"  # 坐标系：map（全局地图坐标系）
    goal_pose.header.stamp = nav.get_clock().now().to_msg()
    goal_pose.pose.position.x = 2.0
    goal_pose.pose.position.y = 2.0
    goal_pose.pose.orientation.w = 1.0  # 朝向：四元数 (0,0,0,1) → 即 yaw=0（面向 x 轴正方向）

    # 发送目标点给导航器
    nav.goToPose(goal_pose)

    # 导航过程
    start_time = nav.get_clock().now()
    while not nav.isTaskComplete():
        feedback = nav.getFeedback()
        
        # 日志记录：剩余距离和预计剩余时间
        nav.get_logger().info(
            f'剩余距离：{feedback.distance_remaining:.2f}m, 预计剩余时间：{Duration.from_msg(feedback.estimated_time_remaining).nanoseconds / 1e9} s '
        )

        # 超时检查与取消任务
        current_time = nav.get_clock().now()
        elapsed_time = current_time - start_time
        if elapsed_time > Duration(seconds=300.0):  # 如果超过300秒（5分钟），则取消任务
            nav.cancelTask()
            nav.get_logger().warn('导航任务超时，已取消！')
            break

        # 休眠一段时间以避免CPU占用过高
        time.sleep(0.1)

    # 最终结果判断
    result = nav.getResult()
    if result == TaskResult.SUCCEEDED:
        nav.get_logger().info('导航结果：成功')
    elif result == TaskResult.CANCELED:
        nav.get_logger().warn('导航结果：被取消')
    elif result == TaskResult.FAILED:
        nav.get_logger().error('导航结果：失败')
    else:
        nav.get_logger().error('导航结果：返回状态无效')

    # 关闭 ROS 2 客户端
    nav.lifecycleShutdown()
    rclpy.shutdown()

if __name__ == '__main__':
    main()