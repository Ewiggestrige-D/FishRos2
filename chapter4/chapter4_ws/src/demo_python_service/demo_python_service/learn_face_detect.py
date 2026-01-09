"""
Fish ROS2 4.2.2 Face Detection
核心需求：
1.将文件在从colcon build时自动复制到install目录下
2.从从install目录下获取 "/home/ros/chapter4/chapter4_ws/install/demo_python_service/share/demo_python_service/resource"
3,读取图片内容进行人脸识别
4.将识别之后的人脸用框框起来

需求：成功复制default image → 成功读取default image → 识别人脸 
│
├─ 成功复制default image → setup.py 的data_files 中添加  ('share/' + package_name + "/resource", ['resource/default.jpg']),
├─ 成功读取default image → get_package_share_directory
├─ 识别人脸 → face_recognition.face_locations(image, number_of_times_to_upsample=2,model='hog')
├─ 绘制矩形 → cv2.rectangle
└─ 显示结果 → cv2.imshow

"""
import rclpy 
from rclpy.node import Node

import face_recognition
import cv2
from ament_index_python.packages import get_package_share_directory #获取功能包share目录绝对路径

def main():
    # 获取图片的真实路径
    # 从install目录下获取 "/home/ros/chapter4/chapter4_ws/install/demo_python_service/share/demo_python_service/resource"
    default_image_path = get_package_share_directory('demo_python_service') + '/resource/default.jpg'
    print(f"图片的真实路径：{default_image_path}")
    
    #使用cv2加载图片
    image = cv2.imread(default_image_path)
    face_locations = face_recognition.face_locations(image, number_of_times_to_upsample=2,model='hog')
    # 根据函数提示，返回值为 A list of tuples of found face locations in css (top, right, bottom, left) order
    
    # 绘制人脸框
    for top,right,bottom,left in face_locations:
        cv2.rectangle(image,(left,top),(right,bottom),(255,0,0),4)
        # 注意opencv使用的是BGR 和常见的RGB正好相反
        
    # 显示结果
    cv2.imshow('Face Detect Result',image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()