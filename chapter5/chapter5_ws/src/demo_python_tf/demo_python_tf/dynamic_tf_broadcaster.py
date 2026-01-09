"""
Fish Ros2 5.2.2 通过Python发布动态TF
核心需求：
- 相机固定在右上方的camera_link处
- 机械臂的底座固定在base_link处
- 从base_link到camera_link的位置是固定不变的，平移分量(0.5，0.3,0.6),旋转分量(180,0,0)
- 相机通过识别得到瓶子bottle_link的坐标,其中平移分量(0.2,0.3,0.5),旋转分量(0,0,0)

需求：确定camera_link和bottle_link的关系→ 使用平移和旋转操作进行坐标变换 → 持续广播坐标关系
│
├─ 创建动态广播节点 → self.broadcaster_ = TransformBroadcaster(self)
├─ 发布动态TF → publish_tf
├─ 使用坐标转换消息接口 → TransformStamped()
├─ 静态坐标平移变换 → transform.transform.translation
├─ 欧拉角转四元数 → quaternion_from_euler(0,0,0)
├─ 坐标旋转变换 → transform.transform.rotation
└─ 把坐标持续发布 → self.timers_ = self.create_timer(1,self.publish_tf) → self.static_broadcaster_.sendTransform
"""
import rclpy
from rclpy.node import Node

from tf2_ros import StaticTransformBroadcaster # 静态坐标广播器
from tf2_ros import TransformBroadcaster # 动态坐标广播器

from geometry_msgs.msg import TransformStamped # 坐标转换消息接口

from tf_transformations import quaternion_from_euler # 从欧拉角转换为四元数

import math # 用于角度转弧度

class TFBroadcaster(Node):
    def __init__(self,node_name= 'tf_broadcaster'):
        super().__init__(node_name = node_name)
        self.get_logger().info(f'{node_name}四元数，启动')
        self.broadcaster_ = TransformBroadcaster(self) # 创建广播器，用节点来进行广播，因此需要传入node
        self.timers_ = self.create_timer(1,self.publish_tf)
        
    def publish_tf(self):
        """
        publish_tf_static 的 Docstring
        发布动态TF,从base_link (robotic arm) to camera_link的坐标关系
        :param self: 说明
        """
        transform = TransformStamped()
        transform.header.frame_id = 'camera_link'
        transform.child_frame_id = 'bottle_link'
        transform.header.stamp = self.get_clock().now().to_msg()
        
        # 平移 默认单位是米 m
        transform.transform.translation.x = 0.3
        transform.transform.translation.y = 0.2
        transform.transform.translation.z = 0.5
        
        # 欧拉角转四元数（返回值的顺序为xyzw）
        q = quaternion_from_euler(0,0,0) # 角度转弧度，再从欧拉角转四元数，因此q现在是 tuple
        
        # 旋转 
        transform.transform.rotation.x = q[0]
        transform.transform.rotation.y = q[1]
        transform.transform.rotation.z = q[2]
        transform.transform.rotation.w = q[3]
        
        # 把动态坐标发布
        self.broadcaster_.sendTransform(transform)
        self.get_logger().info(f'动态坐标数据{transform}已经发布')
        
        
def main():
    rclpy.init()
    node = TFBroadcaster()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()