"""
Fish ROS2 4.4.3 客户端请求修改其他节点的参数
优化点	                 好处
客户端复用	     减少资源开销，避免频繁创建/销毁连接
异常处理	     程序更健壮，不会因网络波动或服务崩溃而退出
日志更清晰	     明确打印哪个参数成功/失败
移除冗余 spin	 逻辑更清晰，符合“同步客户端”模型
服务名可配置	 后续可通过 declare_parameter('target_node', ...) 动态设置
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
        # 原有人脸检测服务客户端
        self.client_ = self.create_client(FaceDetector, 'face_detect')
        self.bridge_ = CvBridge()
        self.default_image_path = os.path.join(
            get_package_share_directory('demo_python_service'),
            'resource', 'Trump.png'
        )
        self.image = cv2.imread(self.default_image_path)
        
         # ✅ 优化1: 提前创建参数服务客户端（复用）
        self.target_node_name = 'face_detect_param'
        self.param_client = self.create_client(
            SetParameters,
            f'/{self.target_node_name}/set_parameters'
        )
        
    def call_set_parameter(self, parameters):
        # ✅ 优化2: 使用已创建的 param_client，不再重复 create_client
        while not self.param_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('等待参数服务上线...')

        request = SetParameters.Request()
        request.parameters = parameters

        future = self.param_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        # ✅ 优化3: 增加异常处理
        if future.exception() is not None:
            self.get_logger().error(f'服务调用异常: {future.exception()}')
            return None
        return future.result()
    
    def update_model_client(self, model='hog'):
        param = Parameter()
        param.name = 'model'

        param_value = ParameterValue()
        param_value.string_value = model
        param_value.type = ParameterType.PARAMETER_STRING
        param.value = param_value

        response = self.call_set_parameter([param])
        if response is not None:
            for i, result in enumerate(response.results):
                self.get_logger().info(
                    f"参数'{param.name}' 设置 {'成功' if result.successful else '失败'}: {result.reason}"
                )
        else:
            self.get_logger().error("未能获取参数设置响应")
            
            
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
    
    try:
        node.update_model_client('hog')
        node.send_request()
        node.update_model_client('cnn')
        node.send_request()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
    
