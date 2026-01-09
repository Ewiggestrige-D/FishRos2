"""
Fish Ros2 5.2 Python中的手眼坐标变换
核心需求：
- 相机固定在右上方的camera_link处
- 机械臂的底座固定在base_link处
- 从base_link到camera_link的位置是固定不变的，平移分量(0.5，0.3,0.6),旋转分量(180,0,0)
- 相机通过识别得到瓶子bottle_link的坐标,其中平移分量(0.2,0.3,0.5),旋转分量(0,0,0)

需求：确定base_link和camera_link的关系→ 使用平移和旋转操作进行坐标变换 → 广播坐标关系
│
├─ 创建静态广播节点 → self.static_broadcaster_ = StaticTransformBroadcaster(self)
├─ 发布静态TF → publish_tf_static
├─ 使用坐标转换消息接口 → TransformStamped()
├─ 静态坐标平移变换 → transform.transform.translation
├─ 欧拉角转四元数 → quaternion_from_euler(math.radians(180),0,0)
├─ 静态坐标旋转变换 → transform.transform.rotation
└─ 把静态坐标发布 → self.static_broadcaster_.sendTransform
"""
import rclpy
from rclpy.node import Node

from tf2_ros import StaticTransformBroadcaster # 静态坐标广播器

from geometry_msgs.msg import TransformStamped # 坐标转换消息接口

from tf_transformations import quaternion_from_euler # 从欧拉角转换为四元数

import math # 用于角度转弧度

class StaticTFBroadcaster(Node):
    def __init__(self,node_name= 'static_tf_broadcaster'):
        super().__init__(node_name = node_name)
        self.get_logger().info(f'{node_name}福禄寿，启动')
        self.static_broadcaster_ = StaticTransformBroadcaster(self) # 创建广播器，用节点来进行广播，因此需要传入node
        self.publish_tf_static()
        
    def publish_tf_static(self):
        """
        publish_tf_static 的 Docstring
        发布静态TF,从base_link (robotic arm) to camera_link的坐标关系
        :param self: 说明
        """
        transform = TransformStamped()
        transform.header.frame_id = 'base_link'
        transform.child_frame_id = 'camera_link'
        transform.header.stamp = self.get_clock().now().to_msg()
        
        # 平移 默认单位是米 m
        transform.transform.translation.x = 0.5
        transform.transform.translation.y = 0.3
        transform.transform.translation.z = 0.6
        
        # 欧拉角转四元数（返回值的顺序为xyzw）
        q = quaternion_from_euler(math.radians(180),0,0) # 角度转弧度，再从欧拉角转四元数，因此q现在是 tuple
        
        # 旋转 
        transform.transform.rotation.x = q[0]
        transform.transform.rotation.y = q[1]
        transform.transform.rotation.z = q[2]
        transform.transform.rotation.w = q[3]
        
        # 把静态坐标发布
        self.static_broadcaster_.sendTransform(transform)
        self.get_logger().info(f'静态坐标数据{transform}已经发布')
        
        
def main():
    rclpy.init()
    node = StaticTFBroadcaster()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()