"""
Fish Ros2 7.4.2 使用TF获取机器人的实时位置
核心需求：
- 实时获取仿真机器人在gazebo地图中的位置
- 监听base_footprint到map之间的坐标变换

需求：创建监听器→ 创建buffer（带时间戳的 TF 变换缓存区） → 监听坐标关系
│
├─ 创建监听器 → self.broadcaster_ = TransformBroadcaster(self)
├─ 发布动态TF → TransformListener(self.buffer_,self)
├─ 创建buffer → self.buffer_ = Buffer()
├─ 读取最新的tf数据 → self.buffer_.lookup_transform
├─ 封装tf数据 → result = self.buffer_.lookup_transform
├─ 封装坐标变换数据 → transform = result.transform
└─ 持续监听 → self.timers_ = self.create_timer(1,self.listen_tf)

"""
import rclpy
from rclpy.node import Node

from tf2_ros import StaticTransformBroadcaster # 静态坐标广播器
from tf2_ros import TransformBroadcaster # 动态坐标广播器
from tf2_ros import TransformListener,Buffer # 坐标变换监听器

from geometry_msgs.msg import TransformStamped # 坐标转换消息接口

from tf_transformations import quaternion_from_euler # 从欧拉角转换为四元数
from tf_transformations import euler_from_quaternion # 从四元数转换为欧拉角

import math # 用于角度转弧度


class TFListener(Node):
    def __init__(self,node_name= 'tf_listener'):
        super().__init__(node_name = node_name)
        self.get_logger().info(f'{node_name}aint no sunshine，启动')
        self.buffer_ = Buffer()
        self.listener_ = TransformListener(self.buffer_,self) # 创建监听器，用节点来进行监听，因此需要传入node
        self.timers_ = self.create_timer(1,self.listen_tf)
        
    def listen_tf(self):
        """
        listen_tf 的 Docstring
        定时获取坐标关系 Buffer_
        :param self: 说明
        """
        try:
            result = self.buffer_.lookup_transform(
                'map','base_footprint',
                rclpy.time.Time(seconds = 0.0),
                rclpy.time.Duration(seconds = 1.0)
                )
            transform = result.transform
            euler_angle = euler_from_quaternion([
                transform.rotation.x,
                transform.rotation.y,
                transform.rotation.z,
                transform.rotation.w
            ])
            self.get_logger().info(f'坐标系平移{transform.translation},坐标系旋转(in Quaternion){transform.rotation},坐标系旋转(RPY){euler_angle}')
        except Exception as e:
            self.get_logger().warn(f'获取坐标变换失败，原因：{str(e)}')
        
        
        
def main():
    rclpy.init()
    node = TFListener()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()