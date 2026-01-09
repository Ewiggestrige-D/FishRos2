import rclpy
from rclpy.node import Node 

def main():
    rclpy.init() # 初始化工作，分配资源
    node = Node('python_node') # 创建一个节点的实例对象，实例归属于Node类，名称叫做 python_node 
    node.get_logger().info('你好 ros2 节点') # 此处没有使用python常见的print函数，而是直接使用了ros2的功能函数，便于后续进行ros2功能的扩展和调用
    rclpy.spin(node) # 运行节点，如果不打断或者结束节点，这个node会一直运行
    rclpy.shutdown() # 关闭节点的运行


if __name__ =='__main__':
    main()

# 确保 main() 函数仅在脚本被直接运行时才执行
# 支持模块化和可测试性,可以安全地在其他测试文件中导入这个模块，而不用担心一导入就启动一个 ROS 节点。
# 如果不加这段，别人写了 import your_module，上面的代码会立刻执行，导致：

# ROS 被意外初始化
# 程序卡在 spin() 无法继续
# 无法进行单元测试或模块复用
