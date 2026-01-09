"""
Fish ROS2 4.4.1 Parameter Declaration
Fish ROS2 4.4.2 Parameter Update Service
使用ros2 param list命令来获取已经声明的参数
ros2 param set </node_name> <param_name> <param_value>来设置参数的值
ros2 param get </node_name> <param_name>              来获取参数的值

根据add_on_set_parameters_callback的说明
修改完成参数之后需要返回一个结果来说明修改参数是否成功
因此需要在修改结果之后按照接口 返回return SetParametersResult(successful=True)

self.declare_parameter('number_of_times_to_upsample',1)
来声明参数可以被修改
"""
import rclpy 
from rclpy.node import Node

import chap4_interfaces
from chap4_interfaces.srv import FaceDetector #自定义的接口格式


import face_recognition
import cv2
from ament_index_python.packages import get_package_share_directory #获取功能包share目录绝对路径
import os
import time

from cv_bridge import CvBridge
from rcl_interfaces.msg import SetParametersResult

class FaceDetectNode(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.get_logger().info(f'{node_name}减肥，启动！')
        self.detection_group = rclpy.callback_groups.MutuallyExclusiveCallbackGroup()
     
        self.service_ = self.create_service(
            FaceDetector,
            'face_detect',
            self.detect_face_callback,
            callback_group=self.detection_group
            )
        # 使用Cv bridge将ros的图片格式转换为opencv可以识别的格式
        self.bridge_ = CvBridge()
        # 将opencv中使用的参数提前作为node的一部分属性，方便后续调用修改
        # imgmsg_to_cv2() 可能抛出 CvBridgeError（如编码不支持、数据损坏）。
        # 必须捕获异常，否则服务会崩溃。
        
        self.declare_parameter('number_of_times_to_upsample',1)
        self.declare_parameter('model','hog')
        self.number_of_times_to_upsample = self.get_parameter('number_of_times_to_upsample').value
        self.model = self.get_parameter('model').value
        self.default_image_path = get_package_share_directory('demo_python_service') + '/resource/default.jpg'
        # 默认图像路径健壮性不足
        # 使用 get_package_share_directory 拼接路径，但未验证文件是否存在。
        # 若资源缺失，cv2.imread() 返回 None，后续操作会崩溃。
        print(f"图片的真实路径：{self.default_image_path}")

        self.add_on_set_parameters_callback(self.parameters_callback)

    def parameters_callback(self,parameters):
        for parameter in parameters:
            self.get_logger().info(f'{parameter.name}->{parameter.value}')
            if parameter.name == 'number_of_times_to_upsample':
                self.number_of_times_to_upsample = parameter.value
            if parameter.name == 'model':
                self.model = parameter.value
                
        return SetParametersResult(successful=True)
        
        
    def detect_face_callback(self,request,response):
        if request.image.data:
            cv_image = self.bridge_.imgmsg_to_cv2(request.image)
        else: 
            cv_image = cv2.imread(self.default_image_path) #已经是opencv格式的图像
            self.get_logger().warn(f'传入图像为空或传入失败，请检查！使用默认图像。')
            
        start_time = time.time()
        self.get_logger().info(f'开始识别，请稍等！')
        face_locations = face_recognition.face_locations(cv_image, self.number_of_times_to_upsample,self.model)
        # face_recognition.face_locations() 是 CPU 密集型操作，在 spin() 主线程中执行会阻塞整个节点（包括其他服务、订阅等）。
        # 高负载下会导致系统无响应。
        
        response.use_time = time.time() - start_time
        response.num_face = len(face_locations)
        self.get_logger().info(f'识别共耗时{response.use_time}秒')
        
        for top,right,bottom,left in face_locations:
            response.top.append(top)  
            response.right.append(right) 
            response.bottom.append(bottom) 
            response.left.append(left)  
            #这一段可以写成工具组
        return response # 必须返回response
        
        
def main():
    rclpy.init()
    node = FaceDetectNode("face_detect_param")
    # 使用多线程执行器以支持并发回调
    executor = rclpy.executors.MultiThreadedExecutor()
    rclpy.spin(node, executor=executor)
    node.destroy_node()
    rclpy.shutdown()
    
    
    
    
    
    
