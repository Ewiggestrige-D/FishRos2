"""
Fish Ros2 8.1.3 创建旋转运动控制器
核心需求：1. 继承运动控制器的基本方法，实现机器人的旋转运动

与c++不同的点：
1. ”.hpp“ 文件是一个类声明文件（header file），它的作用是：
    - 声明 SpinMotionController 类的结构；
    - 告诉编译器：“这个类存在，它继承自 MotionController，并实现了 start() 和 stop()”；
    - 不包含具体实现（那是 .cpp 的工作）；
  其他文件（如主程序、插件加载器）只需包含此头文件即可知道如何使用该类。
    💡 在 C++ 中，声明（declaration） 和 定义（definition） 是分离的。
       这是为了支持模块化编译和接口隐藏。 
       在 Python 中，不需要分离声明与实现。一个类在一个 .py 文件中完成定义。

2. ".cpp "文件是一个具体实现文件，它的作用是：
    - 实现头文件中声明的函数；
    - 注册该类为 pluginlib 插件，使其能被 ClassLoader 动态加载。
    🔑 关键点：最后两行是 pluginlib 插件注册的核心！
       Python如何注册插件？
       Python 没有宏，也不需要 dlopen。ROS 2 的 Python pluginlib 使用 entry_points 机制（来自 setuptools）。

3. Python 插件包 不需要“spin_motion_plugins.xml“文件
    1. 原因：C++ 和 Python 的插件发现机制完全不同
    
| 机制 | C++ (pluginlib) | Python (pluginlib) |
|------|------------------|---------------------|
| 插件注册方式 | XML 文件 + `PLUGINLIB_EXPORT_CLASS` 宏 | `setup.py`（或 `pyproject.toml`）中的 `entry_points` |
| 插件发现方式 | 扫描 `ament index` 中的 `plugin_description.xml` | 扫描 Python 包的 `entry_points` 元数据 |
| 动态加载方式 | `dlopen()` + 符号查找 | `importlib.import_module()` + `getattr()` |

    2. spin_motion_plugins.xml 的作用（C++）：
        - name：插件的唯一标识符（如 "motion_control_system/SpinMotionController"），供 ClassLoader 加载时使用。
        - type：C++ 完整类名（含命名空间）。
        - base_class_type：基类名，用于类型校验。
        - path：对应 libspin_motion_controller.so（去掉 lib 前缀和 .so 后缀）。
        - <description>：人类可读说明。
    ✅ 这个 XML 是 C++ pluginlib 的“插件目录”，告诉系统：“这个 .so 库里有哪些可用插件”。
    
    3. Python 中：
        - 类就是对象，模块就是库；
        - setup.py中的entry_points 已经直接指明了 插件名 → 模块路径:类名 的映射；
        - 不需要额外 XML 来描述“哪个 .so 包含哪个类”。

4. Python 包完全不需要"CMakeLists.txt"来编译插件本身。
    - Python 是解释型语言，没有“编译成动态链接库（.so）”这一步。
    - 你的 spin_motion_controller.py 就是源码，安装后直接被 import 使用。
    - ROS 2 的 ament_python 构建系统只负责：
        - 复制 .py 文件到安装目录；
        - 注册 entry_points；
        - 安装 package.xml 和资源文件。
        
    - Python 包的构建配置文件是：
        - setup.py（或现代的 pyproject.toml）
        - package.xml
    而不是 CMakeLists.txt。

5. 什么时候 Python 包会用到 CMake？
    只有当你：
        - 编写 C++ 节点（即使包主要是 Python）；
        - 使用 Cython / pybind11 编译 Python 扩展；
        - 需要安装非 Python 资源（如 launch 文件、config 文件）
          ——但这些也可以通过 setup.py 的 data_files 实现。
    
    对于纯 Python pluginlib 插件，标准做法是：
    
    motion_control_system/
    ├── setup.py                 ← 插件注册在这里（entry_points）
    ├── package.xml
    └── motion_control_system/
        ├── __init__.py
        ├── motion_control_interface.py
        └── spin_motion_controller.py
        
📌 Python 插件包结构 vs C++ 对比

| 功能 | C++ 包 | Python 包 |
|------|--------|----------|
| 抽象接口 | `include/motion_control_system/motion_control_interface.hpp` | `motion_control_system/motion_control_interface.py` |
| 具体插件实现 | `src/spin_motion_controller.cpp` | `motion_control_system/controllers/spin_motion_controller.py` |
| 插件注册 | `spin_motion_plugins.xml` + `PLUGINLIB_EXPORT_CLASS` | `setup.py` 中的 `entry_points` |
| 构建系统 | `CMakeLists.txt` | `setup.py` + `package.xml` |
| 安装产物 | `libspin_motion_controller.so` + XML | `.py` 文件 + entry_points 元数据 |



"""
# 引入抽象基类，实现继承
from motion_control_system.motion_control_interface import MotionController


class SpinMotionController(MotionController):
    """
    旋转运动控制器的具体实现。
    
    继承自 MotionController 抽象基类，并实现其所有抽象方法。
    """

    def start(self) -> None:
        """启动旋转控制逻辑。"""
        print("SpinMotionController::start")

    def stop(self) -> None:
        """停止旋转控制。"""
        print("SpinMotionController::stop")