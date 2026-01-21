"""
Fish Bot2 7.4.1使用话题初始化机器人位姿

核心需求：通过接口进行导航的调用和状态监测

通过接口配合yaml文件设置机器人多个途径点的代码，详见init_robot_pose & goal point.md
"""
import rclpy 
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped # 带时间戳和坐标系的位姿
from nav2_simple_commander.robot_navigator import BasicNavigator # Nav2 高级 API 封装

def main():
    rclpy.init()
    nav = BasicNavigator() 
    #BasicNavigator 是一个封装了 Nav2 动作客户端、服务客户端的 高层导航接口，它自身继承自 Node，因此可直接用于 rclpy.spin()
    init_pose = PoseStamped() #定义一个初始化点的对象，构造初始位姿（通常对应 AMCL 的初始猜测）
    init_pose.header.frame_id = "map" # 坐标系：map（全局地图坐标系）
    init_pose.header.stamp = nav.get_clock().now().to_msg()
    init_pose.pose.position.x = 0.0
    init_pose.pose.position.y = 0.0
    init_pose.pose.orientation.w = 1.0 # 朝向：四元数 (0,0,0,1) → 即 yaw=0（面向 x 轴正方向）
    nav.setInitialPose(init_pose)  # 发送初始位姿给 AMCL
    nav.waitUntilNav2Active()      # 等待 Nav2 全套系统就绪（包括 costmap、planner、controller 等）
    rclpy.spin(nav)
    rclpy.shutdown()