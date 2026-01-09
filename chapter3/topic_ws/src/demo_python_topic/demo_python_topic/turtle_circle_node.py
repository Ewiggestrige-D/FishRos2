"""
Fish ROS2 3.3.1
核心需求：控制海龟模拟器中的小海龟按照固定半径画圆


需求：控制海龟模拟器中的小海龟 → 运动轨迹按照固定半径画圆
│
├─ 成为 ROS 节点 → class TurtleCirleNode(Node)
├─ 发布话题 → create_publisher(Twist,'/turtle1/cmd_vel',10)
├─ 定时发布 → create_timer(1, timer_callback)
├─ 运动控制 → msg.linear.x , msg.angular.z = 1.0
└─ 循环发布 → rclpy.init() → download() → spin()
"""
import rclpy
from rclpy.node import Node 

import geometry_msgs
from geometry_msgs.msg import Twist #被小海龟模拟器订阅，接受cmd_vel命令的消息接口


class TurtleCircleNode(Node):
    
    def __init__(self, node_name):
        super().__init__(node_name)
        self.get_logger().info(f'{node_name}恨海情天，启动！')
        self.turtle_circle_ = self.create_publisher(Twist,'/turtle1/cmd_vel',10) 
        # 此时创建发布者时，由于小海龟模拟器cmd_vel命令的消息接口的格式是Twist，
        # 因此发布者的消息接口也改为Twist，不再如上一章为String
        # 由于小海龟订阅的话题有限，因此我们只能在小海龟已经订阅的话题中进行发布，
        # 因此发布的话题名称为 ‘/turtle1/cmd_vel’
        self.create_timer(1,self.timer_callback) # timer_callback函数作为参数传回来作为回调函数
        # 时器周期为 1 秒 → 每秒只发一次命令，会导致运动不连续、卡顿（理想应为 10~50 Hz）
        # 但是不影响业务完成度
        
        
    # “初始化阶段做耗时事，回调函数只做轻量事”  
    # __init__()函数定义了ros2 节点的框架逻辑
    # call_back函数定义了节点的业务逻辑
    def timer_callback(self):
        msg = Twist() # msg是内部临时消息的变量名，可任意定义，叫阿猫阿狗都可以
        msg.linear.x = 1.0
        msg.angular.z = 1.0 # 线速度和角速度比值为1, 画的是半径为1的单位圆
        self.turtle_circle_.publish(msg)
"""
 # 使用 lambda 表达式内联回调逻辑
from geometry_msgs.msg import Twist, Vector3
 
self.create_timer(1.0 , lambda: self.turtle_circle_.publish(
            Twist(linear=Vector3(x=1.0), angular=Vector3(z=1.0))
        ))
        
# Twist() 构造时可以直接通过关键字参数初始化其成员（如 linear 和 angular），
# 而它们的类型是 geometry_msgs.msg.Vector3。
# 因此我们使用 Vector3(x=1.0) 来构造线速度和角速度分量。

"""

def main():
    rclpy.init()                                           
    node = TurtleCircleNode('turtle_circle')   
    rclpy.spin(node)                   
    node.destroy_node()                                    
    rclpy.shutdown() 
    
    
"""
支持动态参数的海龟画圆节点
# 主要代码内容
class TurtleCircleNode(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        
        # === 声明参数（带默认值）===
        self.declare_parameter('linear_speed', 1.0)    # 默认线速度 1.0 m/s
        self.declare_parameter('angular_speed', 1.0)   # 默认角速度 1.0 rad/s
        
        # 从参数服务器获取当前值
        self.linear_speed = self.get_parameter('linear_speed').value
        self.angular_speed = self.get_parameter('angular_speed').value
        
        # 创建发布者（注意命名规范）
        self.cmd_vel_pub_ = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        
        # 创建定时器（10 Hz = 每0.1秒调用一次）
        self.timer = self.create_timer(0.1, self.timer_callback)
        
        self.get_logger().info(
            f'"{node_name}" 启动成功！\n'
            f'  线速度: {self.linear_speed} m/s\n'
            f'  角速度: {self.angular_speed} rad/s'
        )

    def timer_callback(self):
        定时回调函数：每0.1秒发布一次速度命令
        
        注意：
        - 这里直接使用 self.linear_speed 和 self.angular_speed
        - 这些值在 __init__ 中已从参数服务器读取
        - 如果需要支持"运行时动态修改参数"，需额外实现 on_parameter_event 回调
        msg = Twist()
        msg.linear.x = float(self.linear_speed)   # 确保是 float 类型
        msg.angular.z = float(self.angular_speed)
        self.cmd_vel_pub_.publish(msg)

默认参数（画单位圆）：
ros2 run your_package turtle_circle

自定义参数（画更大/更小的圆）：

# 画半径 = 2.0 / 0.5 = 4 的大圆
ros2 run your_package turtle_circle --ros-args -p linear_speed:=2.0 -p angular_speed:=0.5

# 原地旋转（线速度=0）
ros2 run your_package turtle_circle --ros-args -p linear_speed:=0.0 -p angular_speed:=1.0

# 直线前进（角速度=0）
ros2 run your_package turtle_circle --ros-args -p linear_speed:=1.0 -p angular_speed:=0.0
"""