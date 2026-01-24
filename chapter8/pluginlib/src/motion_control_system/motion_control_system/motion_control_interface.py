"""
Fish Ros2 8.1 设计运动控制插件
核心需求： 1. 为机器人创建运动控制插件，运动控制器通过调用不同的插件来实现不同方式运动

Fish Ros2 8.1.2 定义插件抽象类
核心需求：1. 定义运动控制器的抽象方法，确保所有的子类控制器都必须实现MotionController的基本功能
"""

from abc import ABC, abstractmethod


class MotionController(ABC):
    """
    抽象运动控制器接口。
    
    所有具体的运动控制器插件必须继承此类并实现所有抽象方法。
    """

    @abstractmethod
    def start(self) -> None:
        """启动控制器。"""
        pass

    @abstractmethod
    def stop(self) -> None:
        """停止控制器。"""
        pass

    def __del__(self):
        # 可选：确保 stop 被调用（但不强制，因 Python 析构不可靠）
        pass