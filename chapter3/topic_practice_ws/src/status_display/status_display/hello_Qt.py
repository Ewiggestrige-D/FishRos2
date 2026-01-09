import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout

def main(args=None):
    """
    ROS 2 兼容的主函数（args 参数可选，用于未来扩展）
    """
    app = QApplication(sys.argv)

    # 创建主窗口
    window = QWidget()
    window.setWindowTitle("我的第一个 Qt 程序")

    # 创建标签
    label = QLabel("Hello, Qt!")

    # 使用布局管理器把标签放进窗口
    layout = QVBoxLayout()
    layout.addWidget(label)
    window.setLayout(layout)

    # 显示窗口
    window.show()
    
    #将 sys.exit(app.exec()) 拆开，避免与 ROS 2 的 rclpy.shutdown() 冲突（虽然此处未用 rclpy，但保持良好习惯）
    exit_code = app.exec()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()