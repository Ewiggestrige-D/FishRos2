"""
FishRos2 7.5 导航实践之自动巡检机器人

FishRos2 7.5.1 机器人系统架构设计
核心需求：1. 巡检机器人能够在不同的目标点之间进行循环移动
2. 到达每个目标点时播放对应的语音提示
3. 到达目标点时，通过摄像头拍摄实时图像并保存到本地

实现：1. 实现不同目标点之间的移动只需要调用导航相关的接口，并通过参数通信灵活修改途径点；
2. 在服务端进行语音合成和通过订阅服务在客户端实时播报；
3. 订阅相机节点发布的话题，将订阅的消息转换成opencv能识别的格式并保存


FishRos2 7.5.2 编写巡检控制节点
核心需求: 1. 直接继承上一小节navigator和之前tf变换的代码实现小车的自动巡检

FishRos2 7.5.3 添加语音播报功能
核心需求: 1. 在patrol_node主程序中创建一个客户端，调用speaker中的语音合成服务

FishRos2 7.5.4 订阅图像并记录
核心需求: 1. 通过订阅相机的话题拿到相机的图像 Topic: /camera_sensor/image_raw
2. 利用CvBridge将图片转换为openCV的格式进行保存 （可参考第四章节人脸识别部分内容）
"""

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped, Pose
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.duration import Duration

from tf2_ros import TransformListener, Buffer
from tf_transformations import quaternion_from_euler, euler_from_quaternion

import time
from autopatrol_interfaces.srv import SpeechText


# 导入相机图像的相关接口
from sensor_msgs.msg import Image
from cv_bridge import CvBridge # 图像信息转换格式
import cv2 # 保存图像


class PatrolNode(BasicNavigator):
    def __init__(self, node_name='patrol_robot', namespace=''):
        """
        Namespace（命名空间）是一种用于组织和隔离节点、话题、服务、参数等资源的机制。
        本质：namespace 就像文件夹路径，把相关资源“打包”在一起，避免冲突。
        
        为什么 BasicNavigator.__init__() 需要 namespace 参数？
            因为BasicNavigator 内部会创建一个 rclpy.Node 实例（通过继承或组合），
            而 Node 的构造函数支持 namespace 参数
        当你调用： super().__init__(node_name, namespace)
        
        实际上是在初始化底层的 Node，并告诉 ROS 2：
        “请把这个节点及其所有资源（topic/service/param）放在 <namespace> 下”
        
        
        为什么你的巡逻机器人需要 namespace？
          场景 1️⃣：多机器人系统（Multi-Robot System）这是最典型的应用！
            假设你有 2 台 FishBot 同时运行：
            机器人 A：需要订阅 /robotA/scan，发布 /robotA/cmd_vel
            机器人 B：需要订阅 /robotB/scan，发布 /robotB/cmd_vel
          
          
          场景 2️⃣：模块化设计 & 避免命名冲突
            即使单机器人，也可能有多个导航相关节点：
            patrol_node（你的巡逻节点）
            emergency_stop_node
            map_server
          用 namespace 可以清晰分组：
          
          场景 3️⃣：与 Nav2 的 namespace 配置对齐
            Nav2 的 launch 文件通常支持 namespace 参数：
            ```xml
            <include file="nav2_bringup_launch.py">
              <arg name="namespace" value="robot1"/>
            </include>
            ```
            这会导致：
            - 所有 Nav2 节点（amcl, controller, planner...）都在 /robot1/ 下
            - 它们发布的 topic 如 /robot1/cmd_vel, /robot1/plan
            如果你的 PatrolNode 不设置相同的 namespace：
            - 它会尝试订阅 /cmd_vel（全局）
            - 但 Nav2 实际发布的是 /robot1/cmd_vel
              → 通信失败！
            ✅ 所以：你的节点 namespace 必须和 Nav2 的 namespace 一致！
        """
        super().__init__(node_name, namespace)
        self.get_logger().info(f'{node_name}六堡奶茶，启动')
        # 声明相关参数
        self.declare_parameter('initial_point',[0.0, 0.0, 0.0])
        self.declare_parameter('target_points',[0.0, 0.0, 0.0, 1.0, 1.0, 1.57])
        # 表示两个点: (0,0,0) 和 (1,1,1.57) （x,y,yaw）
        # 核心原因：ROS 2 的 Parameter 系统不支持嵌套数组（nested arrays） 
        # 因此需要三个一组，平行排列的方式，而不是内部再添加新的数组，
        self.initial_point_ = self.get_parameter('initial_point').value
        self.target_points_ = self.get_parameter('target_points').value
        self.speech_client_ = self.create_client(SpeechText,'speech_text')
        
        self.buffer_ = Buffer()
        self.listener_ = TransformListener(self.buffer_,self) # 创建监听器，用节点来进行监听，因此需要传入node
        
        # 将图像保存的路径定义为一个参数方便灵活修改,默认值为空即保存到当前的相对目录
        self.declare_parameter('image_save_path','') 
        self.image_save_path_ = self.get_parameter('image_save_path').value
        self.cv_bridge_ = CvBridge()
        self.latest_img_ = None
        self.img_sub_ = self.create_subscription(Image,'/camera_sensor/image_raw',self.img_callback,2)
        
    def get_pose_by_xyyaw(self,x,y,yaw):
        """
        get_pose_by_xyyaw 的 Docstring
        返回一个PoseStamped对象
        本函数是工具组，如果考虑高内聚低耦合的代码，是否应该将这段代码分离出主要业务代码？
        
        :param self: 说明
        :param x: 说明
        :param y: 说明
        :param yaw: 说明
        """
        pose = PoseStamped()
        quad = quaternion_from_euler(0,0,yaw) # 返回顺序为xyzw，如下所示
        pose.header.frame_id = 'map' # 位姿坐标系都是基于map的，因此frame_id 应该是map
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.orientation.x = quad[0]
        pose.pose.orientation.y = quad[1]
        pose.pose.orientation.z = quad[2]
        pose.pose.orientation.w = quad[3]
        
        return pose
        
    def init_robot_pose(self):
        """
        init_robot_pose 的 Docstring
        初始化机器人的位姿
        :param self: 说明
        """
        self.initial_point_ = self.get_parameter('initial_point').value
        init_pose = self.get_pose_by_xyyaw(
            self.initial_point_[0],
            self.initial_point_[1],
            self.initial_point_[2]
            )
        """
        通常不需要重复读取。但在特定场景下（如参数可动态重配置），保留它是更鲁棒的做法。
        是否保留，取决于你的设计目标：
        | 场景 | 是否需要重复读取？ | 原因 |
        |------|------------------|------|
        | 参数是静态的（启动时设定，永不改变） | ❌ 不需要 | `__init__` 读一次即可 |
        | 参数支持运行时动态更新（via `ros2 param set`） | ✅ 强烈建议保留 | 确保使用最新值 |

        为什么“可能”需要重复读取？
        1. ROS 2 参数默认支持动态重配置（Dynamic Reconfiguration）
        用户可以在节点运行时修改参数：
        ```bash
        ros2 param set /patrol_robot initial_point "[1.0, 2.0, 0.0]"
        ```
        如果你的节点 不监听参数变化，但又希望在每次调用 init_robot_pose() 时使用最新参数，
        → 就必须在方法内部重新读取！
        💡 即使你没显式写参数回调，用户仍可通过 CLI 修改参数值。
        
        2. init_robot_pose() 可能被多次调用
        比如：机器人迷路后需要重新初始化位姿
        如果参数在两次调用之间被修改（例如通过上层调度系统），
        → 使用缓存的 self.initial_point_ 会得到过期数据
        ✅ 重新读取 = 总是使用当前最新配置
        
        3. 代码鲁棒性 & 显式优于隐式（Explicit is better than implicit）
        在 init_robot_pose() 中直接读取参数，明确表达了“此操作依赖当前参数值”
        避免读者疑惑：“这个 self.initial_point_ 是什么时候设置的？会不会被其他方法改掉？”
        这符合 Python 之禅（Zen of Python）。

        """
        self.setInitialPose(init_pose)  # 发送初始位姿给 AMCL
        self.waitUntilNav2Active()
    
    def get_target_points(self):
        """
        get_target_points 的 Docstring
        通过参数的值来获取目标点的集合
        :param self: 说明
        """
        self.target_points_ = self.get_parameter('target_points').value
        
        if len(self.target_points_) % 3 != 0:
            self.get_logger().error("targets point must have a 3-value tuple [x, y, yaw]")
            return False
        
        points =[]
        
        for index in range(int(len(self.target_points_)/3)):
            x = self.target_points_[index*3]
            y = self.target_points_[index*3+1]
            yaw = self.target_points_[index*3+2]
            points.append([x,y,yaw])
            # 核心原因：ROS 2 的 Parameter 系统不支持嵌套数组
            self.get_logger().info(f'获取到目标点{index}->({x},{y},{yaw})')
        
        return points
            
    def nav_to_pose(self,target_point):
        """
        nav_to_pose 的 Docstring
        导航到目标点
        :param self: 说明
        :param target_point: 说明
        """
        self.goToPose(target_point)

        # 导航过程
        start_time = self.get_clock().now()
        while not self.isTaskComplete():
            feedback = self.getFeedback()

            # 日志记录：剩余距离和预计剩余时间
            self.get_logger().info(
                f'剩余距离：{feedback.distance_remaining:.2f}m, 预计剩余时间：{Duration.from_msg(feedback.estimated_time_remaining).nanoseconds / 1e9} s '
            )

            # 超时检查与取消任务
            current_time = self.get_clock().now()
            elapsed_time = current_time - start_time
            if elapsed_time > Duration(seconds=300.0):  # 如果超过300秒（5分钟），则取消任务
                self.cancelTask()
                self.get_logger().warn('导航任务超时，已取消！')
                break

            # 休眠一段时间以避免CPU占用过高
            time.sleep(0.1)

        # 最终结果判断
        result = self.getResult()
        if result == TaskResult.SUCCEEDED:
            self.get_logger().info('导航结果：成功')
        elif result == TaskResult.CANCELED:
            self.get_logger().warn('导航结果：被取消')
        elif result == TaskResult.FAILED:
            self.get_logger().error('导航结果：失败')
        else:
            self.get_logger().error('导航结果：返回状态无效')
        
            
        
    def get_current_pose(self):
        """
        get_current_pose 的 Docstring
        获取当前机器人的位姿
        :param self: 说明
        """
        while rclpy.ok():
            try:
                result = self.buffer_.lookup_transform(
                    'map','base_footprint',
                    rclpy.time.Time(seconds = 0.0),
                    rclpy.time.Duration(seconds = 1.0)
                    )
                transform = result.transform
                euler_angle = euler_from_quaternion([
                    transform.rotation.x,
                    transform.rotation.y,
                    transform.rotation.z,
                    transform.rotation.w
                ])
                self.get_logger().info(f'坐标系平移{transform.translation},坐标系旋转(in Quaternion){transform.rotation},坐标系旋转(RPY){euler_angle}')
                return transform
            except Exception as e:
                self.get_logger().warn(f'获取坐标变换失败，原因：{str(e)}')
    
    def speech_text(self,text):
        """
        speech_text 的 Docstring
        调用语音合成与播报的函数
        :param self: 说明
        """
        while not self.speech_client_.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(f'语音合成服务未上线，等待中...')
        
        request = SpeechText.Request()
        request.text = text
        future  = self.speech_client_.call_async(request)
        rclpy.spin_until_future_complete(self,future)
        
        if future.exception() is not None:
            self.get_logger().error(f'服务调用异常: {future.exception()}')
            return None
        
        if future.result() is not None:
            response = future.result()
            if response.result == True:
                self.get_logger().info(f'语音合成成功{text}')
            else :
                self.get_logger().error(f'语音合成失败{text}')
        else:
            self.get_logger().error(f'语音响应失败')
            
    def img_callback(self,msg):
        """
        img_callback 的 Docstring
        7.5.4订阅图像并记录
        获取相机图片信息之后的回调函数，将最新的数据放入lastet_img，使用时仅调用最新的数据
        默认保存目录为当前同级文件夹目录
        :param self: 说明
        """
        self.latest_img_ = msg 
        
    def record_img(self):
        """
        record_img 的 Docstring
        7.5.4订阅图像并记录
        用于转换成opencv可以保存的形式并保存图片到指定目录下
        :param self: 说明
        """    
        if self.latest_img_ is not None:
            pose = self.get_current_pose()
            cv_image = self.cv_bridge_.imgmsg_to_cv2(self.latest_img_) # 转换成opencv
            cv2.imwrite(
                f'{self.image_save_path_}img_{pose.translation.x:3.2f}_{pose.translation.y:3.2f}.png',
                cv_image
            )
        else:
            self.get_logger().error(f'暂时无法获取到最新图像')
        
        
        
        
    
def main():
    rclpy.init()
    patrol = PatrolNode()
    patrol.speech_text('正在准备初始化位姿')
    patrol.init_robot_pose()
    patrol.speech_text('位姿初始化完成')
    while rclpy.ok():
        points = patrol.get_target_points()
        
        for point in points:
            x,y,yaw = point[0],point[1],point[2]
            target_pose = patrol.get_pose_by_xyyaw(x,y,yaw)
            patrol.speech_text(f'正在准备前往{x},{y}目标点')
            patrol.nav_to_pose(target_pose)
            patrol.speech_text(f'已经到达{x},{y}目标点,相机正在准备保存图像')
            patrol.record_img()
            patrol.speech_text(f'图像保存完毕')
    rclpy.shutdown()

if __name__ == '__main__':
    main()