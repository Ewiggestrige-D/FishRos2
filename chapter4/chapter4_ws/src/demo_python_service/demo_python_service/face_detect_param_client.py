"""
Fish ROS2 4.4.3 客户端请求修改其他节点的参数
核心需求：通过 ROS 2 客户端，远程修改另一个节点（/face_detect_param）的参数 model 的值（如 'hog' 或 'cnn'）
1. 创建服务客户端
2. 调用参数，修改参数值
3. 指定参数的更新：根据传入的目的model ，构造parameters，然后调用call_Set_parameter更新服务端的参数

需求：创建服务客户端 → 调用参数，修改参数值 → 指定参数的更新：根据传入的目的model
│
├─ 创建服务客户端 →  def create_client(srv_type: Any,srv_name: str)
├─ 调用参数 → call_set_parameter(self,parameters):
├─ 异步发送请求（非阻塞） → self.client_.call_async
├─ 等待异步操作完成 → spin_until_future_complete
├─ 制定参数的更新→ update_model_client
├─ 设置参数 →  self.call_set_parameter([param])
└─ 启动服务和回调组 → node.send_request() → rclpy.spin(node)


在 ROS 2 中，每个节点都有一个内置的参数服务，路径为：

/<node_name>/set_parameters
该服务类型为 rcl_interfaces/srv/SetParameters，允许外部客户端动态修改其参数。

✅ 你的客户端正是通过调用这个标准服务来实现“远程改参”。
因此在之前一次调试中，即使直接修改/face_detect_node（这个节点中没有显式声明参数），也可以修改对应的参数
"""
import rclpy 
from rclpy.node import Node

import chap4_interfaces
from chap4_interfaces.srv import FaceDetector #自定义的接口格式


import face_recognition
import cv2
from ament_index_python.packages import get_package_share_directory # 获取功能包 share 目录绝对路径（跨平台安全）
import os
import time

from cv_bridge import CvBridge

from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter,ParameterValue,ParameterType

class FaceDetectClientNode(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.get_logger().info(f'{node_name}谪仙，启动！')
        # 创建服务客户端（需确保服务名与服务端一致）
        self.client_ = self.create_client(
            FaceDetector,
            'face_detect',
            )
        # 初始化 CvBridge 用于 OpenCV 与 ROS 图像格式互转
        self.bridge_ = CvBridge()
        # 构建默认图像路径（注意：应使用 os.path.join 保证跨平台兼容性）
        # self.default_image_path = get_package_share_directory('demo_python_service') + '/resource/Trump.png'
        self.default_image_path = os.path.join(
            get_package_share_directory('demo_python_service'),
            'resource', 'Trump.png'
        )
        print(f"图片的真实路径：{self.default_image_path}")
        self.image = cv2.imread(self.default_image_path)
        
    def call_set_parameter(self,parameters):
        """
        调用服务，修改参数值
        
        :param self: 说明
        :param parameters: 说明
        """
        # 1. 创建一个客户端，等待服务上线
        update_param_client = self.create_client(SetParameters,'/face_detect_param/set_parameters')  #服务类型：SetParameters（标准 ROS 2 参数设置服务）。
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
    
    def update_model_client(self,model='hog'):
        """
        指定参数的更新。
        根据传入的目的model ，构造parameters，然后调用call_Set_parameter更新服务端的参数
        
        :param self: 说明
        :param model: 说明
        """
        # 1. 创建参数对象
        param = Parameter()
        param.name = 'model' # 设置参数名：model。必须和服务端 declare_parameter('model', ...) 中的名字完全一致。
        
        # 2. 赋值  
        # 重点：根据Parameter消息接口定义，Parameter.value也是一个msg接口，
        # 因此也需要初始化才能对parameter value进行具体的赋值
        param_value = ParameterValue()
        param_value.string_value = model
        param_value.type = ParameterType.PARAMETER_STRING
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
        
    def send_request(self):
        # 1.判断服务器是否在线
        while self.client_.wait_for_service(timeout_sec = 3 ) is False:
            self.get_logger().warn(f'服务端未上线，等待上线！')
            
        # 2.构造Request
        request = FaceDetector.Request()
        request.image = self.bridge_.cv2_to_imgmsg(self.image)
        
        # 3. 异步发送请求（非阻塞）
        future = self.client_.call_async(request) 
        rclpy.spin_until_future_complete(self,future)
        # spin_until_future_complete 是 ROS 2 中等待异步操作完成的标准方式，它会持续处理底层通信（如接收服务响应），直到 Future 完成。
        response = future.result()
        self.get_logger().info(f'接收到响应，共识别人脸{response.num_face}张,共耗时{response.use_time}s')
        self.show_response(response)        
    
    def show_response(self,response):
        """在图像上绘制人脸框并显示（注意：GUI 环境依赖）"""
        for i in range(response.num_face):
            top = response.top[i]
            left = response.left[i]
            right = response.right[i]
            bottom = response.bottom[i]
            cv2.rectangle(self.image,(left,top),(right,bottom),(255,0,0),4)
        
        cv2.imshow('Face Detect Result',self.image)
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()
        
        
def main():
    rclpy.init()
    node = FaceDetectClientNode("face_detect_param_client")
    node.update_model_client('hog')
    node.send_request()
    node.update_model_client('cnn')
    node.send_request()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
    
    
"""
当前写法的问题（虽能运行，但有隐患）
问题	                           说明
1. 每次调用都新建客户端	   create_client 在 call_set_parameter 内部，每次改参都新建连接，效率低
2. 未处理异常	         如果 future.exception() 不为空，future.result() 会抛出异常导致崩溃
3. 服务名硬编码	          节点名写死为 face_detect_node，缺乏灵活性
4. main 中冗余 spin	      rclpy.spin(node) 在纯同步客户端中无意义
"""