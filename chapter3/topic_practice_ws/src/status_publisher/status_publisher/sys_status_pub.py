"""
Fish ROS2 3.4.3
核心需求：
1. 设计一个小工具，可以看到系统的实时状态信息，包括记录信息的时间，主机名称，CPU使用率，
内存使用率，内存总大小，剩余内存，网络接收数据量和网络发送数据量。
2. 要有一个简单的UI界面，可以将系统数据显示出来
3. 要能在局域网内其他主机上查看数据

需求：获取系统状态信息（psutils） → 展示界面(Qt) → 共享数据
│
├─ 成为 ROS 节点 → class SysStatusPub(Node)
├─ 自定义接口 → status_interfaces/msg/SystemStatus.msg
│   ├─ builtin_interfaces/Time stamp      # 时间戳
│   ├─ string host_name                   # 主机名
│   ├─ float32 cpu_percent                # CPU使用率
│   ├─ float32 memory_percent             # 内存使用率
│   ├─ float32 memory_total               # 内存总量 (MB)
│   ├─ float32 memory_available           # 可用内存 (MB)
│   ├─ float64 net_sent                   # 网络发送量 (MB)
│   └─ float64 net_recv                   # 网络接收量 (MB)
│
├─ 获取系统信息 → 
│   ├─ psutil.cpu_percent()               # CPU%
│   ├─ psutil.virtual_memory()            # 内存信息
│   └─ psutil.net_io_counters()           # 网络IO
│
├─ 定时器驱动 → self.create_timer(1.0, callback)  # 每秒采集一次
│
├─ 发布数据 → 
│   └─ self.create_publisher(SystemStatus, 'Sys_Status', 10)
│
└─ 启动流程 → 
    ├─ rclpy.init()
    ├─ node = SysStatusPub('sys_status_pub')
    └─ rclpy.spin(node) → 进入事件循环

接口定义
builtin_interfaces/Time_stamp       #记录时间戳
string host_name                    #系统名称
float32 cpu_percent                 #CPU使用率
float32 memory_percent              #内存使用率
float32 memoty_total                #内存总量
float32 memoty_available            #剩余有效内存
float64 net_sent                    #网络发送数据总量
float64 net_recv                    #网络接收数据总量
"""

import rclpy
from rclpy.node import Node

from status_interfaces.msg import SystemStatus

import psutil
import platform # 用于获取系统信息

class SysStatusPub(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.status_publisher_ = self.create_publisher(SystemStatus,'Sys_Status',10)
        self.timer_ = self.create_timer(1.0,self.timer_callback)
        
    
    
    def timer_callback(self):
        # 
        cpu_percent = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()
        net_io_counters = psutil.net_io_counters()
        
        #
        msg = SystemStatus()
        msg.timestamp = self.get_clock().now().to_msg()
        msg.host_name = platform.node()
        msg.cpu_percent = cpu_percent
        msg.memory_percent = memory_info.percent
        msg.memory_total = memory_info.total/1024 /1024
        msg.memory_available = memory_info.available/1024 /1024
        msg.net_sent = net_io_counters.bytes_sent/1024 /1024
        msg.net_recv = net_io_counters.bytes_recv/1024 /1024
        
        self.get_logger().info(f'发布.{str(msg)}')
        self.status_publisher_.publish(msg)
        
        
    
    
    
def main():
    rclpy.init()
    node = SysStatusPub('sys_status_pub')
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()