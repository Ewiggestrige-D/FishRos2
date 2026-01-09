import rclpy
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor

from chap4_interfaces.srv import FaceDetector
import cv2
from ament_index_python.packages import get_package_share_directory
import os
from cv_bridge import CvBridge


class FaceDetectClientNode(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.client = self.create_client(FaceDetector, 'face_detect')
        self.bridge = CvBridge()
        
        # 安全加载图像
        image_path = os.path.join(
            get_package_share_directory('demo_python_service'),
            'resource', 'Trump.png'
        )
        self.original_image = cv2.imread(image_path)
        if self.original_image is None:
            raise RuntimeError(f"Cannot load image: {image_path}")
        
        self.get_logger().info(f"Client node '{node_name}' initialized.")

    def send_request_sync(self):
        """同步方式发送请求（适用于一次性任务）"""
        if not self.client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error("Service not available after 5s")
            return False

        request = FaceDetector.Request()
        request.image = self.bridge.cv2_to_imgmsg(self.original_image, encoding='bgr8')

        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=10.0)

        if future.done():
            try:
                response = future.result()
                self._visualize_and_show(response)
                return True
            except Exception as e:
                self.get_logger().error(f"Service call failed: {e}")
        else:
            self.get_logger().error("Service call timed out")
        return False

    def _visualize_and_show(self, response):
        """绘制结果并显示（不修改原始图像）"""
        display_image = self.original_image.copy()  # 避免污染原图
        for i in range(response.num_face):
            t, r, b, l = response.top[i], response.right[i], response.bottom[i], response.left[i]
            cv2.rectangle(display_image, (l, t), (r, b), (255, 0, 0), 2)
        cv2.imshow('Detection Result', display_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def main(args=None):
    rclpy.init(args=args)
    node = FaceDetectClientNode("face_detect_client_node")
    
    # 使用独立执行器（更清晰的控制流）
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    
    try:
        success = node.send_request_sync()
        if not success:
            exit(1)
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()