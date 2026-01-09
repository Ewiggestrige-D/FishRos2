"""
Fish ROS2 4.3.2
核心需求：让小海龟在模拟器中随机游走进行巡逻

需求：动态接收指令 → 随机游走 → 自动计算线速度和角速度移动到指定位置（控制策略的选择）
│
├─ 成为 ROS 节点 → class TurtleCirleNode(Node)
├─ 创建服务 → self.create_service(Pose,'/turtle1/pose',self.on_pose_received,10) 
├─ 接收自定义接口 → int8 SUCCESS = 1 ；int8 FAIL = 0
├─ service callbak → 判断条件 if
├─ 重要！ 返回结果 → response.result = Patrol.Response.SUCCESS 重要！
└─ 启动 → rclpy.init() → rclpy.spin(node) 
Patrol.srv 内容如下：
float32 target_x
float32 target_y
---
int8 SUCCESS=1
int8 FAIL=0
int8 result

ROS 2 的 rosidl 代码生成器会生成类似结构（Python）：

class Patrol:
    class Request:
        target_x: float
        target_y: float

    class Response:
        SUCCESS = 1   # ← 常量在这里！
        FAIL = 0      # ← 常量在这里！
        result: int
所以：
- Patrol 本身只是一个命名空间容器
- 常量只存在于 Patrol.Response（因为它们出现在响应部分）
"""
import rclpy
from rclpy.node import Node

import chap4_interfaces
from chap4_interfaces.srv import Patrol # 引入自定义的消息接口

import geometry_msgs 
from geometry_msgs.msg import Twist # 引入turtlrsim中的标准消息接口

import turtlesim
from turtlesim.msg import Pose # 引入turtlrsim中的标准消息接口

import math

class TurtlecontrolNode(Node):
    
    def __init__(self, node_name):
        super().__init__(node_name)
        self.get_logger().info(f'{node_name}BWV 478，启动！')
        self.control_service_ = self.create_service(Patrol,'patrol',self.service_callback)
        self.current_pose_ = self.create_subscription(Pose,'/turtle1/pose',self.on_pose_received,10) 
        # 注意订阅者的函数参数和发布者不完全相同，在qos策略之前需要添加“回调函数”，这个回调函数即主要的业务逻辑函数
        self.turtle_control_ =self.create_publisher(Twist,'/turtle1/cmd_vel',10)
        # 小海龟只监听 /turtle1/cmd_vel，因此想控制小海龟的运动，发布者发布的话题必须是 /turtle1/cmd_vel
        
        
        # === 手动设置目标位置 → 后续可轻松改为参数或服务 ===
        # self.target_x = 8.0
        # self.target_y = 8.0
        
        # === 使用ROS2参数（最标准做法），无需修改代码即可运行时设置目标点： ===
        self.declare_parameter('target_x', 8.0)
        self.declare_parameter('target_y', 8.0)
        self.target_x = self.get_parameter('target_x').value
        self.target_y = self.get_parameter('target_y').value
        
   
        # === 速度限制 ===
        self.linear_max = 3.0
        self.angular_max = 1.5 # 当距离和角度相差过大时，用最大速度限制电机运动
        self.scale_coefficient = 1.0 # 比例控制器
        
        
        
        self.get_logger().info(f'前往目标点: ({self.target_x}, {self.target_y})')
        
    def service_callback(self,request,response):
        # 使用链式比较，清晰表达范围约束
        is_valid = (0 <= request.target_x <= 11.0) and (0 <= request.target_y <= 11.0)

        if is_valid:
            self.target_x = request.target_x
            self.target_y = request.target_y
            response.result = Patrol.Response.SUCCESS
            self.get_logger().info(f'新目标点已设置: ({request.target_x:.2f}, {request.target_y:.2f})')
        else:
            response.result = Patrol.Response.FAIL
            self.get_logger().warn(f'无效目标点: ({request.target_x:.2f}, {request.target_y:.2f})，超出范围 (0,11)')


        return response
        
    def on_pose_received(self, msg): #ToDo
        # 1. 提取当前位置
        x = msg.x
        y = msg.y
        theta = msg.theta
        
        # 2. 计算到目标点的距离
        dx = self.target_x - x
        dy = self.target_y - y
        dist = math.sqrt(dx*dx + dy*dy)
        
        # 3. 如果已经到达，发布零速度并返回
        if dist < 0.1:
            cmd = Twist()
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0
            self.turtle_control_.publish(cmd)
            self.get_logger().info('🎯 已到达目标点！', throttle_duration_sec=1.0)
            # 使用 throttle_duration_sec 防止日志刷屏
            return
        
        # 4. 计算目标朝向和当前角度差
        target_angle = math.atan2(dy, dx)
        angle_error = target_angle - theta    
        
         # === 关键：归一化角度误差到 [-π, π] ===
        angle_error = math.atan2(math.sin(angle_error), math.cos(angle_error))
        
        # 5. 控制逻辑：先转后走，恒速前进
        cmd = Twist()
        if abs(angle_error) > 0.1:
            # 还没对齐角度 → 只旋转
            cmd.linear.x = 0.0
            cmd.angular.z = self.angular_max if angle_error > 0 else -self.angular_max
        else:
            # 角度已对齐 → 恒速前进
            cmd.linear.x = self.linear_max
            cmd.angular.z = 0.0
      
            
         # 6. 发布控制指令
        self.turtle_control_.publish(cmd)
        
def main():
    rclpy.init()                                           
    node = TurtlecontrolNode('turtle_control')   
    rclpy.spin(node)                   
    node.destroy_node()                                    
    rclpy.shutdown() 
    


