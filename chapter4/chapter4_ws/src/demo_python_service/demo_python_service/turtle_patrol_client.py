"""
Fish ROS2 4.3.3
核心需求：利用客户端让小海龟在模拟器中随机游走进行巡逻

需求：创建客户端和定时器 → 定时产生目标 → 请求服务端进行移动和巡逻
│
├─ 成为 ROS 节点 → class TurtleCirleNode(Node)
├─ 创建客户端 → self.create_client(Patrol,'patrol')
├─ 创建定时器 → self.create_timer(15.0,self.timer_callback)
├─ 定时器回调 → timer_callback(self)
├─ 重要！ 服务端请求初始化 → request = Patrol.Request()
├─ 重要！ 异步发送请求 → self.patrol_client_.call_async(request)
├─ 处理服务响应的回调 → fervice_response_callback
└─ 启动节点 →  executor.add_node(node)
"""
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor

import chap4_interfaces
from chap4_interfaces.srv import Patrol # 引入自定义的消息接口

import random # 用于产生随机数

class PatrolClient(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.get_logger().info(f'{node_name}BWV 478，启动！')
        self.patrol_client_ = self.create_client(Patrol,'patrol')
        self.timer_ = self.create_timer(15.0,self.timer_callback)
        
        
    def timer_callback(self):
        # def timer_callback(self, request, response):  # ❌ 错误！
        # Timer 回调函数只有 self 一个参数！
        # ROS 2 的 create_timer 回调是 无参函数（除 self 外）
        """定时器回调：生成随机点并请求巡逻"""
        
        # 1.检测服务端是否上线
        """每15秒触发：若服务在线则发送随机目标；否则跳过，等待下次"""
        # 检查全局关闭信号（如 Ctrl+C）
        if not rclpy.ok():
            self.get_logger().fatal('等待服务上线中，Rclpy挂了，我先退下了～～')
            return  # 外层 spin 会处理退出

        # 尝试快速检查服务是否可用（非阻塞，最多等0.5秒）
        if not self.patrol_client_.wait_for_service(timeout_sec=0.5):
            self.get_logger().warn("服务未上线，跳过本次巡逻（将在15秒后重试）")
            return  # 不做任何事，等待下一次 timer 触发        

        # 2.生成随机坐标的巡逻点位
        request = Patrol.Request()
        request.target_x = round(random.uniform(0, 11), 1)
        request.target_y = round(random.uniform(0, 11), 1)
        self.get_logger().info(f'生成随机目标点（{request.target_x},{request.target_y}），正在向目标进发巡逻！')
        
        # 3.异步发送请求（不阻塞）
        future = self.patrol_client_.call_async(request)

        # 4. 添加回调处理结果（避免嵌套 spin）
        future.add_done_callback(self.service_response_callback)
        """
        在回调中使用 rclpy.spin_until_future_complete(self, future)
        
        在已有 rclpy.spin(node) 的上下文中嵌套 spin_until_future_complete 会导致死锁！
        
        原因：spin() 已经在运行执行器，再次调用 spin_until... 会尝试“再开一个事件循环”，但单线程执行器不支持。
        
        表现为：第一次调用后程序卡死，后续定时器不再触发
        """
        
            
    def service_response_callback(self, future):
        """处理服务响应的回调（在另一个线程中执行）
        
        1.代码逻辑要求：ROS 2 的事件驱动模型
            - ROS 2 节点是事件驱动的：定时器、订阅、服务响应都是“事件”
            - 所有事件由执行器（Executor）调度，按顺序或并发执行
            - call_async() 只是“发起请求”，真正的响应处理必须通过回调注册
        
        2. 线程调用安全：避免竞态条件
            - 即使使用 MultiThreadedExecutor，多个回调也可能并发访问共享变量（如 self.target_x）
            - 将响应处理封装在独立回调中，逻辑边界清晰，便于加锁或设计无状态处理
    
        这样做的好处
        维度	    好处
        响应性	    主线程不阻塞，定时器准时触发
        健壮性	    服务端宕机不会导致客户端卡死
        可维护性	请求与响应逻辑分离，代码更清晰
        扩展性	    未来可轻松添加重试、超时、日志统计等逻辑
        
        
        
        是否所有异步 response 都该用 callback？
        
        ✅ 是的！这是 ROS 2 的标准实践。
        无论是：

        - 服务调用（Service）
        - 动作（Action）
        - 订阅（Subscription）—— 本身就是回调
        - 定时器（Timer）—— 也是回调
        都应使用回调函数处理结果。这是 ROS 2 异步、非阻塞、事件驱动架构的核心。

        📌 例外情况：仅在一次性脚本（如命令行工具）中可使用 spin_until_future_complete，因为这类脚本生命周期短，无需长期运行。
        
        
        “回调 vs 等待完成”哪个更好？
        场景	                              推荐方式	             原因
        长期运行节点（如你的巡逻客户端）	      ✅ 回调	           避免阻塞，保持响应性
        一次性脚本（如 ros2 service call 模拟）	⚠️ spin_until...	 简单直接，生命周期短
        多步骤依赖链	                       ✅ 回调 + 状态机	    避免嵌套阻塞
        💡 结论：在你的场景（长期运行、定时触发），回调是唯一正确选择。
        
        服务类通讯 所有的request和response的处理可不可以理解为：
        “request是一个客户端发送的一个事件 需要一个回调函数,response(尤其是异步返回的response)是另一个事件,最好放在另一个回调函数中处理“
        
        是的，你的理解完全正确且非常到位！
        我们可以从 ROS 2 的底层设计哲学出发，将服务通信中的 Request 和 Response 精准地抽象为
        两个独立的事件（events），并分别用回调函数来处理。
        
        下面我将结合你的观点，从事件驱动模型、异步通信机制、代码结构与线程安全等多个维度进行深入阐释，并辅以生活化类比，帮助你建立清晰的认知框架。

        ✅ 一、ROS 2 中的服务通信 = 两个事件 + 两个回调
        📌 核心观点：
        在 ROS 2 异步模型中：

        - request 是客户端主动触发的“发送事件”
        - response 是服务端返回后触发的“接收事件”
        两者在时间上解耦，在逻辑上分离，必须由不同的回调处理
        🔧 技术实现：
        ```python
        编辑
        # 1. 发送请求（触发“发送事件”）
        future = self.client.call_async(request)  # ← 非阻塞，立即返回
        
        # 2. 注册响应处理回调（绑定“接收事件”的处理器）
        future.add_done_callback(self.handle_response)
        ```
        - call_async() 只负责把请求放进消息队列，不等待结果 → 事件1完成
        - 当网络层收到服务端回复，ROS 2 内部会调度一个新事件 → 事件2发生
        - 执行器调用 handle_response(future) → 事件2被处理
        💡 这正是事件驱动架构（Event-Driven Architecture） 的典型体现。
        
        为什么所有异步 response 都必须用 callback？
        1. 架构一致性（ROS 2 设计原则）
        ROS 2 的整个通信栈（Topic、Service、Action）都基于 rcl（ROS Client Library） 的异步事件循环。

        无论是：

        - Subscription：消息到达 → 触发 callback(msg)
        - Timer：时间到 → 触发 callback()
        - Service Response：响应到达 → 触发 callback(future)
        - Action Feedback/Result：状态更新 → 触发对应回调
        → 统一使用回调，保持编程模型一致

        2. 线程模型要求
        - 默认 SingleThreadedExecutor：所有回调串行执行
        - 若你在 timer_callback 中同步等待 response：
        ```python

        # ❌ 危险！
        future = client.call_async(req)
        rclpy.spin_until_future_complete(node, future)  # ← 阻塞当前回调
        ```
        → 主事件循环被占用 → 其他事件（包括 response 回调本身）无法调度 → 死锁
        ✅ 回调机制天然避免了这种“自己等自己”的悖论。

        3. 资源与生命周期管理
        - 回调函数可以访问节点上下文（如 self.get_logger()、self.destroy_timer()）
        - finally 或异常处理可在回调内部完成
        - 避免在主逻辑中混杂“等待”和“业务”代码
        
        最佳实践总结
        原则	    实践
        事件分离	Request 和 Response 是两个独立事件
        回调专属	每个事件绑定专属回调函数
        永不阻塞	在长期运行节点中禁用 spin_until_future_complete
        多线程可选	用 MultiThreadedExecutor 提升并发性（非必需，但推荐）
        异常防护	在回调中使用 try-except 捕获 future.result() 异常
        """
        if future.cancelled():
            self.get_logger().warn("服务请求已被取消")
            return
    
        try:
            response = future.result()
            if response.result == Patrol.Response.SUCCESS:  # ✅ 双等号比较
                self.get_logger().info("✅ 巡逻目标点设置成功")
            else:
                self.get_logger().warn("❌ 巡逻目标点设置失败")
        except Exception as e:
            self.get_logger().error(f"服务调用异常: {e}")
    
def main(args=None):
    """
    args=None 的作用
    - args=None：定义函数参数的默认值
    - 当你从命令行启动节点时（如 ros2 run pkg node --ros-args -p rate:=10），ROS 2 会传入参数列表
    - rclpy.init(args=args) 将这些参数传递给 ROS 2 系统，用于：
        解析命名空间
        设置参数
        处理日志级别等
    
    🌰 生活例子：
    你开一家餐厅（main 函数）：

    def main() = 不管客人有什么特殊要求，一律上标准套餐
    def main(args=None) = 允许客人说“不要香菜”、“要微辣”，你根据要求调整菜品
    """
    
    rclpy.init(args=args)
    """
    左边 args 是 rclpy.init() 的形参名
    右边 args 是当前函数的局部变量
    两者名字相同是巧合，也可写成 rclpy.init(args=ros_args)
    """
    node = PatrolClient('patrol_client')

    # 使用多线程执行器，允许定时器和服务回调并发执行
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()  # 替代 rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
    """
    try: except: finally: 是什么？
    不是条件语句，而是异常处理机制，用于捕获和处理运行时错误（异常）
    
    结构含义：
    - try：尝试执行可能出错的代码
    - except：如果出错，执行这里的处理逻辑
    - finally：无论是否出错，都执行（用于清理资源）
    
    
    🆚 与 if else、while 的本质区别
    特性	   try-except-finally	  if-else	      while
    类型	    异常处理	            条件分支	     循环控制
    触发时机	运行时错误发生时	    条件为真/假时	条件为真时重复执行
    目的	    错误恢复、资源清理	     逻辑选择	      重复执行
    是否阻塞	    否	                  否	     是（若条件永真）
    是否导致死锁	 否	                   否	       可能（死循环）
    
    
    🌰 生活化类比
    结构	             生活场景
    try-except-finally	开车：尝试启动（try），如果没油了（异常），叫拖车（except），最后锁车（finally）
    if-else	            出门：如果下雨（if），带伞；否则（else），戴帽子
    while	            等电梯：只要电梯没到（while），就继续等
    
    ⚠️ 是否会造成阻塞或死锁？
    try-except-finally：不会造成阻塞或死锁
    → 它只是错误处理，不改变控制流逻辑
    
    if-else：不会造成阻塞或死锁
    → 只是单次判断
    
    while：可能造成死锁或死循环
    → 如果循环条件永远为真，且无退出机制
    
    
    如何预防阻塞和死锁？
    控制结构	           预防措施
    try-except-finally	总是用 finally 清理资源（如关闭文件、销毁节点）
    if-else	            避免复杂嵌套，使用卫语句（early return）
    	
                        确保循环变量会变化
    while               设置最大迭代次数
                        避免在循环中阻塞（如 time.sleep 应替换为定时器）
                        
    📌 在 ROS 2 中：
    
    - 永远不要在回调中写 while True
    - 永远不要在回调中用 spin_until_future_complete
    - 用定时器替代 time.sleep
    """

if __name__ == '__main__':
    main()