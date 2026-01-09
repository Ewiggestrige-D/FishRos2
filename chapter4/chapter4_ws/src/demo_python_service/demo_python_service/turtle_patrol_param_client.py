"""
Fish ROS2 4.5.3
核心需求：通过 ROS 2 客户端，远程修改另一个节点（/turtle_control_param）的参数

使用标准 SetParameters 服务	   正确调用 /turtle_control_param/set_parameters
参数构造规范	               正确使用 Parameter + ParameterValue + 显式类型（PARAMETER_DOUBLE）
异步服务调用 + 回调处理	         call_async + add_done_callback 避免阻塞主线程
使用 MultiThreadedExecutor	  允许定时器和服务回调并发执行
定时器非阻塞检查服务可用性	      wait_for_service(timeout_sec=0.5) 不会长时间阻塞
"""
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor

import chap4_interfaces
from chap4_interfaces.srv import Patrol # 引入自定义的消息接口

import random # 用于产生随机数

from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter,ParameterValue,ParameterType

class PatrolClient(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.get_logger().info(f'{node_name}列宾，启动！')
        self.patrol_client_ = self.create_client(Patrol,'patrol')
        self.timer_ = self.create_timer(15.0,self.timer_callback)
        self.update_linear_max_client(3.0)
        
    def call_set_parameter(self,parameters):
        """
        调用服务，修改参数值
        
        :param self: 说明
        :param parameters: 说明
        """
        # 1. 创建一个客户端，等待服务上线
        update_param_client = self.create_client(SetParameters,'/turtle_control_param/set_parameters')  #服务类型：SetParameters（标准 ROS 2 参数设置服务）。
        while update_param_client.wait_for_service(timeout_sec = 1 ) is False:
            self.get_logger().info(f'等待参数更新服务端上线，！')
            
        # 2. 创建request
        request = SetParameters.Request()
        request.parameters = parameters
        
        # 3. 调用服务端更新参数
        future = update_param_client.call_async(request)
        rclpy.spin_until_future_complete(self,future)
        response = future.result()
        
        return response
    
    def update_linear_max_client(self,linear_max=3.0):
        """
        指定参数的更新。
        根据传入的目的model ，构造parameters，然后调用call_Set_parameter更新服务端的参数
        
        :param self: 说明
        :param model: 说明
        """
        # 1. 创建参数对象
        param = Parameter()
        param.name = 'linear_max' # 设置参数名：model。必须和服务端 declare_parameter('model', ...) 中的名字完全一致。
        
        # 2. 赋值  
        # 重点：根据Parameter消息接口定义，Parameter.value也是一个msg接口，
        # 因此也需要初始化才能对parameter value进行具体的赋值
        param_value = ParameterValue()
        param_value.double_value = linear_max
        param_value.type = ParameterType.PARAMETER_DOUBLE
        param.value = param_value
        #因为 model 是字符串，所以：
        # 赋值给 .string_value
        # 显式设置 .type = PARAMETER_STRING（这是必须的！ROS 2 需要知道数据类型）
        # 
        # 为什么不能直接 param.value = "hog"？
        # 因为 Parameter.value 是一个 union 类型（类似 C 的 union），必须通过 ParameterValue 明确指定字段和类型。
        
        
        # 3.请求更新参数
        response = self.call_set_parameter([param]) # 传入参数列表（即使只有一个参数，也需放入 list）。
        for result in response.results:
            self.get_logger().info(f'设置参数结果：{result.successful}{result.reason}')
        
    
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

        
            
    def service_response_callback(self, future):
        
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
    
    
    rclpy.init(args=args)
    node = PatrolClient('patrol_param_client')

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
    