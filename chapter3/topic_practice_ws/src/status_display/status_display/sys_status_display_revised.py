"""
Fishros 3.4.5 +千问AI  

订阅数据并用Qt显示

核心需求：订阅系统状态并用Qt显示（优化版）
│
├─ 核心原则：线程隔离 + 信号通信
│
├─ ROS 2 模块（运行于子线程）→ class SysStatusDisplay(Node)
│   ├─ 订阅 /Sys_Status 话题
│   └─ 收到消息后 → emit 信号（不碰GUI！）
│
├─ 通信桥梁 → class RosSignal(QObject)
│   └─ pyqtSignal(str) new_data  # 用于跨线程传递字符串
│
├─ Qt GUI 模块（运行于主线程）→ class MainWindow(QWidget)
│   ├─ QLabel 用于显示文本
│   └─ 接收 new_data 信号 → 更新 QLabel（安全！）
│
├─ 主控流程 → main()
│   ├─ 创建 QApplication（主线程）
│   ├─ 创建 MainWindow 并 show()
│   ├─ 连接信号：ros_signal.new_data → window.label.setText
│   ├─ 启动 ROS 节点线程（daemon=True）
│   │   └─ rclpy.spin(node) 在后台运行
│   ├─ app.exec_() 阻塞主线程（Qt事件循环）
│   └─ 退出时：destroy_node() + rclpy.shutdown()
│
└─ 数据流向：
    psutil → SystemStatus → DDS网络 → 
    ROS回调（子线程）→ emit信号 → 
    Qt槽函数（主线程）→ 更新GUI
    └─ app.exec()
    
✅ 优势：

    线程安全：GUI 操作仅在主线程
    职责分离：ROS / Qt / 通信解耦
    稳定可靠：符合 Qt 和 ROS 2 最佳实践

✅ 优化思路：

    GUI 创建和显示 → 主线程
    ROS 2 回调 → 通过信号/队列安全传递数据到主线程
    使用 QTimer 或信号机制更新 GUI


为什么这样优化？—— 工程原则
1. 遵守 Qt 线程规则
“Only the thread that created a widget can access it.”

—— Qt 官方文档

2. 单一职责原则（SRP）
    1. MainWindow：只负责显示
    2. SysStatusDisplay：只负责 ROS 订阅
    3. RosSignal：只负责线程间通信
    
3. 防御性编程
    1. 使用 daemon=True 防止子线程阻塞退出
    2. try-except 捕获中断信号
    3. 显式资源清理
    
🌐 实际工业应用场景
这种模式广泛用于：

机器人操作面板（如 UR 机械臂的 ROS 控制界面）
自动驾驶监控系统（显示车辆状态、传感器数据）
无人机地面站（实时显示飞行参数）

💡 关键价值：

将 ROS 2 的分布式数据能力与本地 GUI 的交互体验无缝结合。

✅ 总结
问题	           优化方案	                工程价值
跨线程GUI操作	用 pyqtSignal 中转	   避免崩溃，符合 Qt 规范
多窗口弹出	      单一 MainWindow	      用户体验友好
逻辑混杂	    分离 ROS / Qt / 通信	 代码可维护、可测试
资源泄漏	    显式 destroy_node()	     系统长期稳定运行


"""

import rclpy
from rclpy.node import Node

from status_interfaces.msg import SystemStatus

import sys
import threading

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import pyqtSignal, QObject, QTimer

# === 1. 创建信号中转器（解决跨线程问题）===
class RosSignal(QObject):
    """用于从 ROS 线程向 Qt 主线程发送信号"""
    new_data = pyqtSignal(str)  # 定义一个携带字符串的信号
    
    """
    Q1: 为什么要单独创建 RosSignal？new_data 是什么？
    
    ✅ 为什么需要独立的信号中转器？
        1. Qt 信号只能在 QObject 子类中定义
            Qt 信号（pyqtSignal / Q_SIGNAL）只能在 QObject 子类中定义，
            因为信号机制依赖于 QObject 提供的“元对象系统”（Meta-Object System），
            而该系统通过 moc（元对象编译器）在编译期注入代码实现。
            
            QObject 是 Qt 所有具有“对象特性”的类的根基类，它提供了以下运行时基础设施：

            功能	                     说明
            信号与槽（Signals & Slots）	 跨对象通信的核心机制
            属性系统（Properties）	     支持动态读写（如 QML 绑定）
            事件系统（Events）	         鼠标、键盘、定时器等事件分发
            对象树（Object Tree）	     自动内存管理（父对象销毁时自动删子对象）
            元对象信息（Meta-Object）	  运行时获取类名、方法、信号列表等
            
            
        2. SysStatusDisplay(Node) 继承自 rclpy.Node，不是 QObject，不能直接定义 pyqtSignal
        3. 如果强行让 Node 继承 QObject → 多重继承冲突（Node 已有复杂基类）
    💡 设计模式：这是典型的 “适配器模式” —— 用一个轻量 QObject 桥接非 Qt 对象与 Qt 信号系统。

    ✅ new_data = pyqtSignal(str) 的含义
        这是一个 信号声明（signal declaration），不是普通变量
        pyqtSignal(str) 表示：
            1. 该信号携带一个参数
            2. 参数类型是 Python str,即 pyqtSignal(str) 是一个“声明”——
            
            它声明了一种通信契约：“当这个信号被 emit 时，会传递一个 str 类型的数据。”
            
            3. 当 emit("hello") 时，连接的槽函数会收到 "hello"
        📌 它不是一个“接口指向格式”，而是一个“类型安全的通信通道”。
            信号定义了 “传递什么类型的数据”，Qt 会在连接时检查类型是否匹配（例如 str 信号不能连到只接受 int 的槽）

            1. 接口类（Interface）
            接口定义“能做什么”
            子类提供“怎么做”
            
            2. Qt 信号（Signal）
            ```python
            class RosSignal(QObject):
                new_data = pyqtSignal(str)  # ← 只是声明：“我会发字符串”

            # 使用：
            signal = RosSignal()
            signal.new_data.connect(some_function)  # ← 绑定“谁来处理”
            signal.new_data.emit("hello")           # ← 触发事件
            ```
            信号不定义“如何显示”，只定义“我发什么”
            槽函数（some_function）才是“如何显示”的实现
            💡 关键区别：

            接口 是 “调用者主动调用”（displayer.show(text)）
            信号 是 “发布者被动通知”（emit(text) → 自动调用所有连接的槽）

    Qt 在运行时会检查信号与槽的参数是否匹配（虽然 Python 是动态类型，但 PyQt 仍做基本校验）。

    ✅ 好处总结：
    好处	说明
    解耦	ROS 节点无需知道 Qt GUI 存在
    安全	避免跨线程直接调用
    灵活	同一信号可连接多个槽（如同时更新 label 和日志）
    """

class SysStatusDisplay(Node):
    def __init__(self,node_name, ros_signal):
        super().__init__(node_name)
        self.ros_signal = ros_signal
        self.subscription = self.create_subscription(
            SystemStatus,
            'Sys_Status',
            self.sys_info_callback,
            10
        )

    def sys_info_callback(self, msg):
        # 2. 在 ROS 线程中：只负责发送信号（不碰 GUI！）
        show_str = f"""
%====================系统状态====================%
计算机时间：\t{msg.timestamp.sec} s
主机名称：\t{msg.host_name} 
CPU使用率:\t{msg.cpu_percent:.3f} %
内存使用率：\t{msg.memory_percent:.3f} %
内存总大小:\t{msg.memory_total:.3f} MB
剩余有效内存:\t{msg.memory_available:.3f} MB
网络发送量:\t{msg.net_sent:.3f} MB
网络接收量:\t{msg.net_recv:.3f} MB
%===============================================%
        """
        self.ros_signal.new_data.emit(show_str)  # 安全发送到主线程

# === 3. 主窗口类（纯 Qt，不包含 ROS 逻辑）===
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("系统状态监控")
        self.resize(600, 400)
        
        # 创建标签
        self.label = QLabel("等待数据...")
        self.label.setWordWrap(True)  # 自动换行
        
        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        """
        self.setLayout(QVBoxLayout())不能使用的原因：

        QVBoxLayout() 创建的是一个匿名临时对象，你无法保存引用，也就无法调用 addWidget()。

        所以必须先创建变量，添加控件，再设为窗口布局。
        """

def main():
    app = QApplication(sys.argv)
    
    # 1. 创建信号中转器
    ros_signal = RosSignal()
    
    # 2. 创建主窗口（主线程）
    window = MainWindow()
    window.show()
    """
    Q3:为什么先创建窗口，再启动 ROS 节点？顺序能否交换？
    功能上可能正常（因为线程独立）
        但用户体验差：
        程序启动后先初始化 ROS（可能耗时几百毫秒）
        用户看到黑屏或无响应，以为程序卡死
        不符合 GUI 应用启动规范：应尽快显示主窗口
    📌 GUI 黄金法则：
    
    “先显示界面，再加载数据” —— 让用户知道程序已启动。
    """
    
    # 3. 连接信号：当收到新数据时更新标签
    ros_signal.new_data.connect(window.label.setText)
    #                          ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
    #                          这就是槽函数！ 
    #                           槽函数可以是：
    #                           普通函数
    #                           类的方法
    #                           Lambda 表达式
    #                           任何可调用对象（callable）
    
    # 4. 启动 ROS 2 节点（子线程）
    rclpy.init(args=sys.argv) # ← 支持 --ros-args
    node = SysStatusDisplay('sys_status_display',ros_signal)
    """
    根本原因：rclpy.Node.__init__ 只接受位置参数（positional-only）
    在 ROS 2 的 rclpy 源码中（参考官方实现），Node.__init__ 的定义类似：

        python
        编辑
        def __init__(self, node_name: str, *, ...):
        ...
    但实际上，在 较早版本（如 Foxy、Humble）或某些构建方式下，node_name 被设计为 仅限位置参数（positional-only），这意味着：
    """
    def spin_ros():
        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            pass
    
    ros_thread = threading.Thread(target=spin_ros, daemon=True)
    ros_thread.start()
    
     # === 关键修正 2：监听 Qt 退出信号 ===
    def cleanup():
        try:
            node.destroy_node()
        except rclpy.exceptions.InvalidHandle:
            pass  # 节点可能已被销毁
        rclpy.shutdown()
    
    app.aboutToQuit.connect(cleanup)  # ← 窗口关闭时清理
    """
    Q4:app.aboutToQuit.connect(cleanup) 的作用？
    
    ✅ 作用：监听 Qt 应用即将退出的事件
        触发时机：
            用户点击窗口关闭按钮（×）
            调用 app.quit()
            系统请求关闭（如 macOS 强制退出）
        保证 cleanup() 在 Qt 退出前执行
        
    ✅ 为什么需要它？
        app.exec_() 是阻塞调用，只有退出后才继续执行后续代码
        但如果你依赖“app.exec_() 之后的代码”来清理：
        
            ```Python
            app.exec_()
            node.destroy_node()  # ← 如果用户 kill -9，这行永不执行！
            ```
    而 aboutToQuit 是事件驱动的，只要 Qt 开始退出流程就会触发
    
    💡 它是 Qt 应用生命周期管理的标准钩子，所有 Qt 文档都推荐使用。
    """
    
    # === 关键修正 3：捕获 Ctrl+C（可选但推荐）===
    import signal
    def sigint_handler(*args):
        app.quit()  # 触发 aboutToQuit
    
    signal.signal(signal.SIGINT, sigint_handler)
    
    # 让 Python 定期处理信号（避免 Qt 阻塞）
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)  # 每 100ms 唤醒一次
    
    exit_code = app.exec_()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()