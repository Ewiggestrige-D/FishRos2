"""
Fish ROS2 4.2.4 人脸检测客户端的实现
核心需求：
1. 创建服务客户端
2. 构造request，发送请求
3. 处理返回的response，绘制图片

需求：创建服务客户端 → 构造request，发送请求 → 处理异步的response，绘制图片
│
├─ 创建服务客户端 →  def create_client(srv_type: Any,srv_name: str)
├─ 构造request → FaceDetector.Request()
├─ 异步发送请求（非阻塞） → self.client_.call_async
├─ 等待异步操作完成 → spin_until_future_complete
├─ 在图像上绘制人脸框→ cv2.rectangle
├─ 绘制图片 →  cv2.imshow
└─ 启动服务和回调组 → node.send_request() → rclpy.spin(node)
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
        
        
    def send_request(self):
        # 1.判断服务器是否在线
        while self.client_.wait_for_service(timeout_sec = 3 ) is False:
            self.get_logger().warn(f'服务端未上线，等待上线！')
            
        # 2.构造Request
        request = FaceDetector.Request()
        request.image = self.bridge_.cv2_to_imgmsg(self.image)
        
        # 3. 异步发送请求（非阻塞）
        Future = self.client_.call_async(request) #现在的为future并没有包含响应结果，需要等待服务端处理完成才会把结果放到future对象中
        """“Future 是一个异步占位符，当服务端返回响应后，ROS 2 执行器会自动填充其结果。”"""
        # while not future.done() :
        #     time.sleep(1.0) #休眠当前线程，减轻CPU压力，等待结果完成 → 会造成当前线程无法再接收来自服务端的返回，导致永远没办法完成
        # 如果你在单线程执行器中手动轮询 future.done() + time.sleep()，会导致死锁（因为没有线程去处理回调）.
        
        rclpy.spin_until_future_complete(self,Future)
        # spin_until_future_complete 是 ROS 2 中等待异步操作完成的标准方式，它会持续处理底层通信（如接收服务响应），直到 Future 完成。
        response = Future.result()
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
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        
def main():
    rclpy.init()
    node = FaceDetectClientNode("face_detect_client_node")
    node.send_request()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()