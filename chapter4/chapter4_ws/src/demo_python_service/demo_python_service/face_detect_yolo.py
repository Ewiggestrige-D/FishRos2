"""
Fish ROS2 4.2.2 Face Detection_Yolo version
核心需求：
1.将文件在从colcon build时自动复制到install目录下
2.从从install目录下获取 "/home/ros/chapter4/chapter4_ws/install/demo_python_service/share/demo_python_service/resource"
3,读取图片内容,并且使用Yolo进行人脸识别
4.将识别之后的人脸用框框起来

需求：成功复制default image → 成功读取default image → 识别人脸 
│
├─ 成功复制default image → setup.py 的data_files 中添加  ('share/' + package_name + "/resource", ['resource/default.jpg']),
├─ 成功读取default image → get_package_share_directory
├─ 识别人脸 → ace_recognition.face_locations(image, number_of_times_to_upsample=2,model='hog')
├─ 绘制矩形 → cv2.rectangle
└─ 显示结果 → cv2.imshow
"""

import cv2
from ultralytics import YOLO
from ament_index_python.packages import get_package_share_directory

def main():
    # 获取图片路径
    image_path = get_package_share_directory('demo_python_service') + '/resource/default.jpg'
    
    # 加载图像（仍用 OpenCV！）
    image = cv2.imread(image_path)
    
    # 加载预训练 YOLOv8 模型（自动下载首次运行）
    model = YOLO('yolov8n.pt')  # n=nano, s=small, m=medium...
    
    # 执行推理
    results = model(image)  # 返回 Results 对象列表
    
    # 绘制结果（YOLO 自动调用 OpenCV）
    annotated_image = results[0].plot()  # 直接返回带框的图像
    
    # 显示
    cv2.imshow('YOLO Detection', annotated_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    """
    核心作用：
        - 释放 OpenCV 创建的 GUI 资源（窗口句柄、图形上下文）
        - 终止 OpenCV 内部 GUI 线程（如 HighGUI 后台线程）
        - 防止内存泄漏和句柄耗尽
        📌 关键事实：

        > OpenCV 的 imshow() 会启动一个后台 GUI 线程（即使你没显式创建线程！）

        如果不调用 destroyAllWindows()，该线程不会自动退出，导致：

        - 进程无法正常结束
        - 内存/GPU 资源泄漏
        - 下次运行可能因“窗口句柄耗尽”而崩溃
    """