import rclpy
from rclpy.node import Node  
  
# class PersonNode:
# 注意将PersonNode从py文件改造为ros2 节点之后就需要改为下一列的写法，因为只有class PersonNode(Node):算是继承了rclpy库中的node节点的父类方法
class PersonNode(Node):
    def __init__(self,node_name:str,name_value:str,age_value:int) -> None :
        print('PresnNode __init__方法被调用了，添加了两个属性')
        super().__init__(node_name)
        self.name = name_value
        self.age = age_value
    
# self代表当前类的实例对象本身
# 当你创建一个类的实例（比如 p = PersonNode("Alice")），Python 会自动把该实例作为第一个参数传给每个实例方法（包括 __init__）。
    def eat(self, food_name:str):
        """
        eat 的 Docstring
        方法 吃东西
        :param self: 说明
        :param food_name: 说明
        :type food_name: str 食物名字
        """
        print(f"{self.name}今年{self.age}岁，爱吃{food_name}")
        self.get_logger().info(f"{self.name}今年{self.age}岁，爱吃{food_name}")
        
        
def main():
    rclpy.init()
    node = PersonNode('Node_zhangsan','法外狂徒张三',18) #注意节点名称不要使用中文
    node.eat('鱼香肉丝')
    rclpy.spin(node)
    rclpy.shutdown()
    
    
"""
要将一个普通的 Python 脚本改造为 ROS 2 节点（即“node 化”），需要遵循 ROS 2 的节点编程规范。
1.将核心逻辑封装进继承自rclpy.node.Node（注意大小写）的类中，并保留main()函数作为调用的入口。
    import rclpy 
    from rclpy.node import Node
    
    class function(Node)  # 原来的核心逻辑函数← 继承 Node
    
2.在main()中初始化ros2上下文并创建节点实例
    def main():
        rclpy.init() # 初始化节点
        ...... #main函数的核心逻辑
        
        rclpy.spin(node) # 启动node
        node.destroy_node() # 显式释放节点占用的底层资源（如句柄、内存、通信接口等）
        rclpy.shutdown() # 结束node
    
3.在setup.py中声明该脚本为可执行节点，映射main函数。 
在setup.py中的console_scripts中添加入口点
‘<node_name> = <package_name>.<py_file_name>:main<or other mapping name >’, (remember this comma)
    
4.在终端中使用colcon build指令编译整个ros2包，是的正常生成build install log三个新文件夹
（也可以使用 colcon build --package-selet demo_pkg_python<package_name> 指令进行制定性编译）
    
5.运行source install/setup.bash 指令重新激活环境变量，将新的映射添加进环境变量中
    
6.在同一终端中运行 ros2 run <package_name> <excutable_mapping_name>启动节点
    
"""