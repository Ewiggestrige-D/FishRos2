# colcon build 进行构建，构建完成后，生成build install log 三个文件夹
# colcon 会构建当前及子目录下的所有功能包
# build 是构建过程中产生的中间文件
# install 是构建结果的文件夹
# 实际运行的不是主文件 demo_pyhton_pkg/demo_pyhton_pkg/python_node.py下的main函数
# 而是 build之后 install/demo_pyhton_pkg/lib/python3.10/site-packages/demo_pyhton_pkg/python_node.py 下的main函数
# 因此修改了主文件夹下的代码之后，需要重新colcon build，否则install文件夹下的内容没有更新，输出结果不会产生变化 
# 为什么使用这种复制的方式进行文件的构建呢，因为在ros2中，使用colcon build之后，python代码会以源码的形式暴露，但是cpp代码则会被编译成二进制代码进行储存
# 为什么没有 if __main__ 函数呢，if __main__函数的作用是用于调用pkg中间的功能
# 在ros2功能包里面会自动生成可执行文件，相当于把if __main__ 函数外化到setup文件里面
# ROS 2 通过 setup.py 中的 entry_points 机制，将程序的入口点从传统的 if __name__ == "__main__": 转移到了显式定义的函数（如 main()）上，使得 ROS 工具链（如 ros2 run）可以直接调用该函数，而无需依赖脚本是否被直接执行。

"""
为什么回调函数这个设计很强大？
1. 解耦（Decoupling）
Download 类不需要知道回调函数具体做什么
可以传入 Word_Count、SaveToFile、PrintLength 等任意函数
2. 灵活性
Python
编辑
# 不同用途，同一 Download 类
download.start_download(url, Word_Count)      # 统计字数
download.start_download(url, Save_To_File)    # 保存文件
download.start_download(url, Analyze_Content) # 分析内容
3. 符合“好莱坞原则”
“Don't call us, we'll call you.”

（别调用我们，我们会调用你）

Download 控制下载流程，但在适当时机回调你提供的函数。

"""

"""
在ros2框架下运行这个文件需要那些步骤
1. 将py文件以面向对象的方式编写，留下main函数调用
2. 将py文件导入到setup.py 中，声明可执行脚本的映射，做好main函数的映射
3. 在环境中colcon build，在pkg中编译包的内容
4. 使用source install/setup.bash命令 修改环境变量
4. 使用ros2 run demo_pkg_python(pkg名称) （中间需要空格） learn_thread(映射之后的可执行名)来运行py文件中的main函数
"""
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