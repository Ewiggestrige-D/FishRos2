"""
Fish Ros2 8.1.4 编写插件测试程序
核心需求：1. 编写一个简易的测试程序用来测试spin_motion_controller是否已经成功编译
2. 编写一个轻量级加载器，做好类型检查

🚨 重要事实：ROS 2 Python 插件加载的现状
截至 ROS 2 Humble / Iron：
    - C++ 有完整的 pluginlib::ClassLoader
    - Python 没有官方等效的 pluginlib.Loader
    - 虽然可以通过 entry_points 注册插件，但没有标准库帮你自动加载
💡 这是一个长期存在的“半支持”状态。许多 ROS 2 Python 包（如 Nav2）自己实现了插件加载逻辑，而不是依赖 pluginlib 模块。

解决方案：手动实现插件加载
利用 pkg_resources 或 importlib.metadata（Python 3.8+）读取 entry_points写一个轻量级加载器。
"""

import sys
from typing import Type, TypeVar
from abc import ABC
from importlib.metadata import entry_points
from motion_control_system.motion_control_interface import MotionController

# 定义泛型类型变量，绑定到 ABC
T = TypeVar('T', bound=ABC)


def load_controller_plugin(plugin_name: str, base_class: Type[T]) -> T:
    """
    手动从 entry_points 加载 motion_control_system.MotionController 插件。
    
    Args:
        plugin_name: 插件名称（如 'spin_controller'）
        base_class: 基类（用于类型检查，可选）
    
    Returns:
        插件类的实例
    """
    # 仅支持 Python 3.10+
    eps = entry_points(group='motion_control_system.MotionController')
    
    for ep in eps:
        if ep.name == plugin_name:
            cls = ep.load()  # 返回具体的类（如 SpinMotionController）
            instance = cls()
            
            # 使用 type: ignore 忽略 mypy 对抽象基类的 isinstance 限制
            if not isinstance(instance, base_class):  # type: ignore[arg-type]
                raise TypeError(
                    f"Plugin '{plugin_name}' returns {type(instance)}, "
                    f"not a subclass of {base_class.__name__}"
                )
            return instance
    
    available = [ep.name for ep in eps]
    raise ValueError(f"Plugin '{plugin_name}' not found. Available: {available}")


def main() -> int:
    # 判断参数数量是否合法
    if len(sys.argv) != 2:
        print("Usage: test_motion_plugin <plugin_name>")
        print("Available plugins:")
        eps = entry_points(group='motion_control_system.MotionController')
        for ep in eps:
            print(f"  - {ep.name}")
        return 1
    # 通过命令行参数，选择要加载的插件,argv[0]是可执行文件名，argv[1]表示参数名
    plugin_name = sys.argv[1]
    # 1.通过功能包名称和基类名称创建控制器加载器
    # 3.调用插件的方法
    try:
        controller = load_controller_plugin(plugin_name, MotionController)  # type: ignore[type-abstract]
        controller.start()
        controller.stop()
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())