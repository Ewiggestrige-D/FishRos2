"""
Fish ROS2 3.2.1
下载一部小说文本 → 按行存入内存 → 每隔 5 秒（实际代码是 10 秒）通过 ROS 2 话题发布一行

这是一个典型的 “异步数据生产 + 定时发布” 场景。

第一步：分解任务 → 映射到 ROS 2 概念
需求子任务	           对应的 ROS 2 概念	      需要什么能力
. 成为一个 ROS 节点	        Node 类	       必须继承 rclpy.node.Node
. 能发布消息	          Publisher	       需要 create_publisher()
. 消息内容是一行文本	    消息类型	  使用 example_interfaces/msg/String
. 定时触发发布动作	         Timer	          需要 create_timer()
. 下载并解析小说	    普通 Python 逻辑	  requests + 字符串处理
. 缓存所有行，供定时器逐行取出	线程安全队列	queue.Queue（虽单线程，但结构清晰）


需求：下载小说 → 每5秒发布一行
│
├─ 成为 ROS 节点 → class NovelPubNode(Node)
├─ 发布文本 → create_publisher(String, 'novel', 10)
├─ 定时触发 → create_timer(5, timer_callback)
├─ 缓存行数据 → Queue()
├─ 下载解析 → download() + splitlines()
└─ 启动流程 → rclpy.init() → download() → spin()
"""
#所有的pkg根据需求导入 
import rclpy #ros2必须导入
from rclpy.node import Node #将文件节点化导入
import requests
from example_interfaces.msg import String
from queue import Queue

class NovelPubNode(Node):  # 所有 ROS 2 节点必须继承 Node，否则无法使用 create_publisher、get_logger 等方法。
    def __init__(self, node_name):
        super().__init__(node_name) # ← 调用父类 Node 的构造函数，实例化之后向 ROS 系统注册该节点
        self.get_logger().info(f'{node_name}原神，启动！')
        self.novels_queue_ = Queue() # ← 在这里给实例添加属性：创建队列 ，需要一个先进先出（FIFO） 的结构来暂存所有行。
        self.novel_publisher_ = self.create_publisher(String,'novel',10) #用于创建发布者，10 是队列深度（QoS history depth），防止发布太快时丢消息。
        # 为什么用 self.novel_publisher_ 而不是直接写 novel_publisher_？
        # 原因 1：novel_publisher_ 是 节点实例的属性（成员变量），可在类的其他方法中使用
        # 在 Python 类中，所有属于实例的变量都要用 self.attribute 来定义。
        # 这样才能在类的其他方法中访问到它（比如 timer_callback 中要调用 self.novel_publisher_.publish()）。
        # "在类中，用 self 调用方法，用 self 保存属性，这样类的实例才能拥有自己的状态和行为。" （很重要）
        self.create_timer(10,self.timer_callback) # timer_callback函数作为参数传回来作为回调函数
       
    #“初始化阶段做耗时事，回调函数只做轻量事”   
    #本设计的核心优势
    """
    1. 职责分离（Separation of Concerns）
        - `download()`：专注数据获取  
        - `timer_callback()`：专注消息发布  
        - `__init__()`：专注资源初始化  

    2. **符合 ROS 2 事件驱动模型**  
        - 所有回调均为非阻塞操作，确保事件循环流畅运行  
        - 避免因网络 I/O 导致节点“假死”

    3. **状态封装与可扩展性**  
        - 使用 `Queue` 作为内部缓冲，天然支持 FIFO 发布  
        - 若未来需支持多小说、暂停/恢复等功能，只需扩展 `download()` 或添加新方法，无需改动核心逻辑
    """
    
    
    def timer_callback(self):
        # self.novel_publisher_.publish()
        if self.novels_queue_.qsize() > 0:  #实例属性（instance attribute）属于整个实例，而不是某个方法。
            # 因此能跨方法访问 self.novels_queue_ 
            # 类中的任何方法都可以通过 self.novels_queue_ 访问它。
            line = self.novels_queue_.get() #每次 timer 触发，就从队列取一行（get() 自动移除）。
            msg = String()
            # 为什么不用 self.msg 
            # 1. 语义错误：混淆“状态”与“临时数据”
            # 实例属性（self.xxx）应该表示节点的持久状态或能力。
            # msg 只是一个一次性使用的中间对象，下一次回调会创建新的 msg。
            # 2. 线程/回调安全问题（潜在风险）
            # 如果写成 self.msg，会让人误以为“这个节点有一个固定的 msg 对象”，但实际上每次内容都不同。
            # 如果未来改用多线程执行器（multi-threaded executor）
            # 或者有多个 timer / callback 同时触发 self.msg 就可能被多个回调同时修改，导致数据竞争！
            # 而局部变量 msg 是每个回调调用栈私有的，天然线程安全。
            # 3. 不必要的内存占用 
            # self.msg 会让消息对象一直驻留在内存中，即使不使用。
            msg.data = line
            self.novel_publisher_.publish(msg)
            self.get_logger().info(f'{msg}鸣潮，启动！')
    
    # __init__、timer_callback、download 中的 self 指的是同一个对象实例。
    # 每个 NovelPubNode 的实例都拥有完整的类方法（包括 __init__、timer_callback、download），
    # 并且各自拥有独立的一套实例属性（如 A.novels_queue_ ， B.novels_queue_）。这是面向对象的核心——封装性 + 状态隔离。两个节点实例的队列是完全独立的！
            
         

    def download(self,url):
        # 阻塞操作（Blocking Operation） 是指：程序发起一个请求后，必须等待它完成才能继续执行下一行代码。
        # 这类 I/O 操作属于 同步阻塞 I/O（synchronous blocking I/O），会占用主线程直至完成。
        print(f'开始下载：{url}')
        # 为什么阻塞？
        response = requests.get(url) # 必须等服务器返回数据才能继续
        # 非阻塞操作（对比）：
        # 发送 UDP 包（不等回复）
        # 写入非阻塞 socket
        # 使用 asyncio 异步 I/O（高级话题）
        response.encoding = 'utf-8'
        text = response.text
        self.get_logger().info(f'下载{url},{len(text)}')
        for line in text.splitlines(): 
            self.novels_queue_.put(line)
        

def main():
    rclpy.init()                                           # ← 初始化 ROS 2 客户端库
    node = NovelPubNode('novel_pub')                       # ← 创建节点实例，根据Node要求，实例需要有name
    node.download('http://127.0.0.1:8000/episode1.txt')    # ← 阻塞式下载（此时还未进入 ROS 循环）且必须在 rclpy.spin() 前完成！因为 download 是阻塞的
    # 节点启动慢，但一旦开始工作，就完全响应、不卡顿
    # 如果 download() 在 spin() 之后（比如放在 timer_callback 中）
    # 节点看似“运行中”，实际 1 小时内完全失联
    # 这不是“启动慢”，而是 运行时崩溃式卡死
    # 对系统其他部分造成严重影响（比如依赖该节点的机器人会停摆）
    # 真正的问题是：
    # Python 主线程被 requests.get() 阻塞，而 ROS 2 的事件循环也在同一个线程中运行，所以整个事件循环被暂停了。
    # 因为你的程序只有一个线程，它在等网络返回，没空干别的
    
    rclpy.spin(node)                                       # ← 进入事件循环，timer 开始工作
    # rclpy.spin(node) 的本质：
    # 启动一个无限循环，不断检查是否有事件发生（如定时器到期、收到消息），
    # 如果有，就调用对应的回调函数。
    # 关键点：
    # 这个循环运行在主线程
    # 所有回调函数（包括 timer_callback）都在这个线程里被调用
    # 默认是单线程执行器（Single-threaded Executor）
    node.destroy_node()                                    # ← 清理资源
    rclpy.shutdown()                                       # ← 关闭 ROS 2 上下文

