"""
Fishros 3.4.5 订阅数据并用Qt显示

核心需求：订阅系统状态并用Qt显示
│
├─ 成为 ROS 节点 → class SysStatusDisplay(Node)
│
├─ 订阅数据 → 
│   └─ self.create_subscription(SystemStatus, 'Sys_Status', sys_info_callback, 10)
│
├─ 展示界面 → 
│   ├─ 使用 PyQt5.QLabel 显示文本
│   └─ ❌ 直接在回调中调用 label.setText() 和 label.show()
│
├─ 多线程启动 → 
│   ├─ 主线程：QApplication.exec() → 运行Qt GUI
│   └─ 子线程：rclpy.spin(node) → 运行ROS节点
│       └─ ⚠️ 回调函数在子线程中直接操作主线程的GUI对象（不安全！）
│
└─ 启动流程 → 
    ├─ app = QApplication(sys.argv)
    ├─ rclpy.init()
    ├─ node = SysStatusDisplay(...)
    ├─ threading.Thread(target=rclpy.spin)
    └─ app.exec()

"""
import rclpy
from rclpy.node import Node

import status_interfaces
from status_interfaces.msg import SystemStatus

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout

import threading

class SysStatusDisplay(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.get_logger().info(f'{node_name}玄秘曲，启动！')
        self.sys_info_ = self.create_subscription(SystemStatus,'Sys_Status',self.sys_info_callback,10)
        # 创建QLabel对象
        self.label = QLabel()
        """
        为什么要在init函数里创建qlabel实例? 为什么不能再callback函数里创建或者在main函数里单独创建
        
        
         结论先行
        QLabel（以及所有 Qt GUI 控件）必须在主线程的 __init__（或窗口初始化阶段）创建，并作为类的成员变量保存。
        在 callback 或 main 中临时创建会导致：内存泄漏、界面闪烁、崩溃、无法更新等问题。
        
        为什么不能在 callback 函数里创建 QLabel？
        
        def sys_info_callback(self, msg):
            showStr = "..."
            label = QLabel(showStr)  # ← 每次回调都新建一个！
            label.show()             # ← 弹出新窗口！
            
           问题	    说明
        1. 内存泄漏	每秒创建一个 QLabel 对象，旧对象未被删除 → 内存持续增长
        2. 窗口爆炸	每次 label.show() 都会弹出一个独立无父窗口 → 屏幕上堆满窗口
        3. 无法更新	新建的 label 和之前的毫无关系 → 不是“更新内容”，而是“新建一个”
        4. 线程违规	如果 callback 在子线程（如 ROS 节点线程），直接创建 Qt 控件会崩溃（Qt 控件必须在主线程创建）
        
        实际效果：
        运行 5 秒后，屏幕上出现 5 个一模一样的小窗口，每个显示不同时间的数据，且无法关闭。
        
        
        为什么不能在 main 函数里单独创建 QLabel？
        
        def main():
            app = QApplication(sys.argv)
            label = QLabel("初始文本")  # ← 在 main 里创建
            label.show()

            rclpy.init()
            node = SysStatusDisplay('node', label)  # 试图传入 label

            # ... 启动线程 ...
            
         问题分析：
           问题	        说明
        1. 职责混乱	    GUI 创建逻辑散落在 main 和节点类中 → 难以维护
        2. 生命周期错配	 label 是局部变量，可能在 app.exec_() 前就被回收（尤其在复杂逻辑中）
        3. 无法封装	     如果未来要增加按钮、图表等控件，main 会变得臃肿
        4. 不符合 OOP	Qt 推荐将 UI 封装在 QWidget/QMainWindow 子类中
        📌 Qt 设计哲学：

        “UI 应该是一个自包含的对象（如 MainWindow），而不是一堆散落的控件。”
        
        
        为什么必须在 __init__ 中创建并保存为成员变量？
        
           优势	       说明
        1. 单一实例	    整个程序只有一个 QLabel，避免资源浪费
        2. 可持续更新	通过 setText() 修改内容，而非重建控件
        3. 生命周期可控	self.label 随节点对象存在，直到 destroy_node()
        4. 符合 Qt 规范	所有 Qt 示例和文档都采用此模式（如 Qt 官方教程）
        5. 支持布局管理	可将 self.label 加入 QVBoxLayout，实现自动排版
        
        
        
        工业级实践：更推荐的做法（封装到 MainWindow）
        虽然在 Node 的 __init__ 中创建 QLabel 能工作，但最佳实践是将 GUI 完全分离：
        
        class MainWindow(QWidget):
            def __init__(self):
                super().__init__()
                self.label = QLabel("等待数据...")
                layout = QVBoxLayout()
                layout.addWidget(self.label)
                self.setLayout(layout)

        class RosNode(Node):
            def __init__(self, window: MainWindow):
                super().__init__('node')
                self.window = window  # 保存对窗口的引用

            def callback(self, msg):
                self.window.label.setText(...)  # 安全更新（需配合信号机制）
        
        ✅ 这样做的好处：
            1. ROS 逻辑 和 GUI 逻辑 完全解耦
            2. MainWindow 可独立测试（无需启动 ROS）
            3. 更容易扩展（加按钮、图表等）
            
            
            GUI 控件是“状态持有者”，不是“一次性工具”。
            它们应该在程序初始化时创建，在整个运行期间被重复使用和更新，而不是反复新建。
        """
        
        
    def sys_info_callback(self,msg):
        
        # 组装要显示的函数
        # 通过 Python 的 f-string 多行字符串格式化 实现
        showStr = f"""  
        %====================系统状态====================%
        
        计算机时间：\t{msg.timestamp.sec} s
        主机名称：\t{msg.host_name} 
        CPU使用率: \t{msg.cpu_percent} %
        内存使用率：\t{msg.memory_percent} %
        内存总大小: \t{msg.memory_total}  MB
        剩余有效内存: \t{msg.memory_available} MB
        网络发送量: \t{msg.net_sent} MB
        网络接收量:  \t{ msg.net_recv} MB
        
        %===============================================%
        """
        # 显示数据
        self.get_logger().info(f'{showStr}')
        
        # label = Qlabel(showStr)
        self.label.setText(showStr)
        self.label.show()

        
def main():
    # 创建QApplication对象
    app = QApplication(sys.argv)
    
    """
    为什么在 main() 中创建 QApplication？它的作用是什么？
        ✅ 简短回答：
        QApplication 是 Qt GUI 程序的“心脏”和“唯一入口”，必须在主线程的 main() 中创建且全局唯一。

        🔍 深入解析：QApplication 的三大核心作用
        1. 管理 Qt 应用的全局状态
            1. 存储应用元信息（名称、版本、图标等）
            2. 管理所有窗口、控件、事件队列
            3. 提供跨平台抽象（Windows/macOS/Linux 统一接口）
        2. 启动主事件循环（Event Loop）
        python
        
        app = QApplication(sys.argv)  # ← 初始化
        # ... 创建窗口 ...
        app.exec_()                   # ← 启动事件循环（阻塞！）
        
        
        exec_() 是一个无限循环，负责：
            1. 监听鼠标/键盘事件
            2. 刷新界面
            3. 处理定时器、网络、信号槽等异步任务
        没有它，GUI 窗口会立即关闭！
        
        3. 资源协调与清理
            1. 自动管理所有 QWidget 子对象的内存（父对象销毁时自动清理子对象）
            2. 在程序退出时释放底层图形资源（如 OpenGL 上下文）
        
        ⚠️ 为什么必须在 main() 中创建？
          原因	                  说明
        主线程要求	Qt 规定：QApplication 必须在主线程创建（否则崩溃）
        全局唯一性	一个进程只能有一个 QApplication 实例
        生命周期匹配	它的生命周期 = 整个 GUI 程序的生命周期
    """
    """
    QApplication(sys.argv) 必须传入 sys.argv，这是 Qt 初始化其内部命令行解析系统所必需的。虽然在简单程序中“看似可省略”，但省略会导致：

        1. 无法处理 Qt 内置命令行参数
        2. 在某些平台/环境下行为异常
        3. 违反 Qt 官方规范，埋下兼容性隐患
        
    sys.argv 是 Python 的标准库变量，表示程序启动时的命令行参数列表
    
    为什么 QApplication 需要它？
    
    Qt 的设计哲学：“应用程序应能响应标准 GUI 命令行参数”
    Qt 内部会自动解析 argv 中的以下参数（无需你写代码）：

    参数	                     作用
    -style <style>	            强制使用特定 UI 风格（如 fusion, windows）
    -platform <plugin>	        指定图形后端（如 xcb for Linux, windows for Win）
    -qwindowgeometry WxH+X+Y	设置窗口初始位置和大小
    -qmljsdebugger=...	        启用 QML 调试器
    --help	                    显示 Qt 帮助信息
    
    💡 即使你的程序不处理这些参数，Qt 自己也需要它们！

    📌 关键机制：
    当你执行：

    python

    app = QApplication(sys.argv)
    
    Qt 会：

        1. 复制一份 argv
        2. 从中移除它自己能处理的参数
        3. 将剩余参数留给你的程序处理（如 ROS 2 的 --ros-args）

    工程实践中的正确写法
    python
    
    import sys
    from PyQt5.QtWidgets import QApplication

    def main():
        # 1. 创建 QApplication（必须传 sys.argv）
        app = QApplication(sys.argv)  # ← 这是唯一正确方式

        # 2. 初始化 ROS 2（也建议传 sys.argv）
        rclpy.init(args=sys.argv)     # ← 让 ROS 2 也能处理参数

        # ... 其他逻辑 ...

        exit_code = app.exec_()
        sys.exit(exit_code)
        
    ✅ 这样做的好处：
    优势	        说明
    兼容 Qt 参数	用户可用 -style fusion 改变 UI 风格
    兼容 ROS 2 参数	支持 --ros-args -p ...
    符合官方规范	 PyQt/PySide/ROS 2 文档一致要求
    未来-proof	   即使现在不用参数，未来扩展也不会出错
    """
    
    rclpy.init()
    node = SysStatusDisplay('sys_status_display')
    
    """
    为什么这样写？—— ROS 2 + Qt 的架构挑战

    1. ROS 2 节点：必须运行在 rclpy.spin() 循环中（阻塞式）
    2. Qt GUI 应用：必须运行在 QApplication.exec() 主事件循环中（也阻塞式）
    ❗ 两个“主循环”不能同时在一个线程中运行！
    """ 
    
    def ActivateNode():
        rclpy.spin(node)
 
    
    node_thread = threading.Thread(target= ActivateNode) #另一个线程开启节点
    node_thread.daemon = True #确保主线程退出时，子线程也会退出
    node_thread.start()
    
    # node.destroy_node()
    # rclpy.shutdown()
    
    app.exec()
    
"""
核心问题：程序无法正常到达资源清理代码

原因分析：

1. app.exec_() 是阻塞调用,它会一直运行直到用户关闭所有窗口,之后才会继续执行 main() 中的后续代码
2. 但原始代码没有处理“窗口关闭事件”,即使用户关闭了 QLabel 窗口，app.exec_() 可能仍不退出（因为 QLabel 不是主窗口）
导致程序永远卡在 app.exec_()
3. 即使退出，子线程仍在运行
    rclpy.spin(node) 在子线程中无限循环
    主线程退出后，Python 解释器会强制终止子线程（daemon=True）
    但 ROS 2 节点未被优雅关闭 → DDS 实体泄漏
    
    
⚠️ 后果：资源泄漏（虽然 Python 有 GC，但不够！）
资源类型	风险
DDS 实体	Fast DDS 会在共享内存中残留端口文件（需手动 rm /dev/shm/fastrtps_*）
网络套接字	未关闭的 UDP/TCP 连接可能占用端口
日志句柄	文件描述符未释放
"""