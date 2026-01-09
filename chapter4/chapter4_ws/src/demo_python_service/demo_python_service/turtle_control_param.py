"""
Fish ROS2 4.5.1
Fish ROS2 4.5.2
核心需求：显式参数化最大线速度和最大角速度
添加参数更新回调，当受到客户端setParam请求时自动调用该回调函数处理

Note：在使用外部工具如QRT或者terminal命令改变这个值之后，只是改变了ros2内部 节点参数表（parameter storage）上这个参数的值，
并没有把这个值修改并拷贝到这个参数的成员变量中来。 
在param通信中，只有调用get_parameters()函数才会每次调用都会从节点的参数存储中读取当前值。
这个过程不是“通信”，而是本地内存访问（参数存在节点内部，不是远程）。
更准确地说：成员变量是静态快照，而 get_parameter() 是动态查询。
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
from rcl_interfaces.msg import SetParametersResult

class TurtlecontrolNode(Node):
    
    def __init__(self, node_name):
        super().__init__(node_name)
        self.get_logger().info(f'{node_name}马里奥，启动！')
        self.control_service_ = self.create_service(Patrol,'patrol',self.service_callback)
        self.current_pose_ = self.create_subscription(Pose,'/turtle1/pose',self.on_pose_received,10) 
        # 注意订阅者的函数参数和发布者不完全相同，在qos策略之前需要添加“回调函数”，这个回调函数即主要的业务逻辑函数
        self.turtle_control_ =self.create_publisher(Twist,'/turtle1/cmd_vel',10)
        # 小海龟只监听 /turtle1/cmd_vel，因此想控制小海龟的运动，发布者发布的话题必须是 /turtle1/cmd_vel
        
        # self.target_x = 1.0
        # self.target_y = 1.0
        
        
   
        # === 速度限制 ===
        # self.linear_max = 3.0
        # self.angular_max = 1.5 # 当距离和角度相差过大时，用最大速度限制电机运动
        self.scale_coefficient = 1.0 # 比例控制器
        
        # === 使用ROS2参数（最标准做法）！声明和获取参数的初始值 ！===
        self.declare_parameter('linear_max', 3.0)
        self.declare_parameter('angular_max', 1.5)
        self.linear_max = self.get_parameter('linear_max').value
        self.angular_max = self.get_parameter('angular_max').value
        
        self.declare_parameter('target_x', 8.0)
        self.declare_parameter('target_y', 8.0)
        self.target_x = self.get_parameter('target_x').value
        self.target_y = self.get_parameter('target_y').value
        
        self.get_logger().info(f'前往目标点: ({self.target_x}, {self.target_y}),此时最大线速度为：{self.linear_max},最大角速度为：{self.angular_max}')
        
        self.add_on_set_parameters_callback(self.parameters_callback)
    
    def parameters_callback(self,parameters):
        for parameter in parameters:
            self.get_logger().info(f'{parameter.name}->{parameter.value}')
            if parameter.name == 'linear_max':
                self.linear_max = parameter.value
            if parameter.name == 'angular_max':
                self.angular_max = parameter.value
            if parameter.name == 'target_x':
                self.target_x = parameter.value
            if parameter.name == 'target_y':
                self.target_y = parameter.value
                
        return SetParametersResult(successful=True)    
    
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
    node = TurtlecontrolNode('turtle_control_param')   
    rclpy.spin(node)                   
    node.destroy_node()                                    
    rclpy.shutdown() 
    


