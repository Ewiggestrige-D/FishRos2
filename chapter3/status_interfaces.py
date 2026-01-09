"""
Fish ROS2 3.4.1
核心需求：
1. 设计一个小工具，可以看到系统的实时状态信息，包括记录信息的时间，主机名称，CPU使用率，
内存使用率，内存总大小，剩余内存，网络接收数据量和网络发送数据量。
2. 要有一个简单的UI界面，可以将系统数据显示出来
3. 要能在局域网内其他主机上查看数据

需求：获取系统状态信息（psutils） → 展示界面(Qt) → 共享数据
│
├─ 成为 ROS 节点 → class TurtleCirleNode(Node)
├─ 自定义接口 → 
├─ 获取系统信息 → 
├─ 展示界面 → 
├─ 发布数据→ 
├─  → 
└─ 启动 → rclpy.init() → rclpy.spin(node) 

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