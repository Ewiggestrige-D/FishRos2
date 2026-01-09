"""
Fish ROS2 3.2.2

课后优化作业：espeakng声音太难听了，接入百度或者讯飞的免费api优化声音。
"""

import rclpy
from rclpy.node import Node
from example_interfaces.msg import String
from queue import Queue
import espeakng # python 电子语音合成库
import threading    
import time

class NovelSubNode(Node):  
    def __init__(self, node_name):
        super().__init__(node_name) 
        self.get_logger().info(f'{node_name}锐刻，我是维新派！')
        self.novels_queue_ = Queue()
        self.novel_subscriber_ = self.create_subscription(String,'novel',self.novel_espeakng_callback,10) 
        #回调函数的本质： 回调函数 = “事件发生时自动执行的函数”
        # ROS 2 系统底层（DDS）收到网络消息后，
        # 自动调用你注册的回调函数（如 novel_espeakng_callback），
        # 并把消息对象作为参数传给你：
        
        # 为什么要用一个对象来接收这个属性，
        # 虽然当前代码中没有显式使用 self.novel_subscriber_，但将其保存为实例属性是一种良好的编程习惯，主要为了：
        # 1.确保订阅对象不被 Python 垃圾回收（GC）意外销毁
        # 在 Python 中，如果一个对象没有任何变量引用它，就会被垃圾回收器（GC）自动销毁。
        
        # 2.便于后续扩展（如动态取消订阅、修改 QoS 等）
        # 虽然你现在只是简单订阅，但未来可能需要：
        # 动态取消订阅：self.destroy_subscription(self.novel_subscriber_)
        # 修改 QoS 策略（高级用法）
        # 查询订阅状态（调试）
        # 如果没有保存这个对象，这些操作都无法实现。
        
        # 3.符合 ROS 2 官方推荐的资源管理规范
        # 查看 ROS 2 官方教程 的 Python 示例，你会发现所有 create_publisher / create_subscription 的返回值都被保存为实例属性，即使后续未使用。
        # 体现“资源显式管理”的工程思想
        
        self.speech_thread_ = threading.Thread(target=self.speaker_thread)
        self.speech_thread_.start()
    
    def novel_espeakng_callback(self,msg):
        self.novels_queue_.put(msg.data) #为什么这个地方是msg.data 这个地方写msg有什么区别，
        #msg 是 String 类型的对象（来自 example_interfaces/msg/String）
        # 它的定义是： string data
        # 所以 msg.data 才是真正的字符串内容
        # 如果你写 self.novels_queue_.put(msg)，队列里存的是整个消息对象，后续 speaker.say(msg) 会报错（因为 say() 需要字符串，不是对象）
        
    def speaker_thread(self):
        speaker = espeakng.Speaker()
        speaker.voice = 'zh'
        
        while rclpy.ok(): # 检测当前ros2上下文是否正常
            if self.novels_queue_.qsize()>0: 
                text = self.novels_queue_.get()
                self.get_logger().info(f'朗读:{text}')
                speaker.say(text)
                speaker.wait()
            else : #让当前的线程休眠
                time.sleep(1)
                
def main():
    rclpy.init()                                           
    node = NovelSubNode('novel_sub')   
    rclpy.spin(node)                   
    node.destroy_node()                                    
    rclpy.shutdown() 