import rclpy
from rclpy.node import Node

def main():
    rclpy.init()
    node = Node('python_node')
    node.get_logger.info('你好 ros2节点') #
    node.get_logger.warn('ros2节点警告') #
    rclpy.spin(node)
    rclpy.shutdown()


# colcon build 进行构建，构建完成后，生成build install log 三个文件夹
# colcon 会构建当前及子目录下的所有功能包
# build 是构建过程中产生的中间文件
# install 是构建结果的文件夹
# 实际运行的不是主文件 demo_pyhton_pkg/demo_pyhton_pkg/python_node.py下的main函数
# 而是 build之后 install/demo_pyhton_pkg/lib/python3.10/site-packages/demo_pyhton_pkg/python_node.py 下的main函数
# 因此修改了主文件夹下的代码之后，需要重新colcon build，否则install文件夹下的内容没有更新，输出结果不会产生变化 
# 为什么使用这种复制的方式进行文件的构建呢，因为在ros2中，使用colcon build之后，python代码会以源码的形式暴露，但是cpp代码则会被编译成二进制代码进行储存
# log 是