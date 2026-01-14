# 导入必要的 Python 和 ROS 2 launch 相关模块
import os  # 用于路径拼接和文件系统操作
import launch  # ROS 2 核心 launch 模块，用于构建启动描述
import launch_ros  # ROS 2 的 launch 扩展，用于启动节点等
from ament_index_python.packages import get_package_share_directory  # 用于获取 ROS 2 包的共享目录路径
from launch.launch_description_sources import PythonLaunchDescriptionSource  # 用于包含其他 Python launch 文件


def generate_launch_description():
    """
    ROS 2 要求每个 launch 文件必须定义一个名为 `generate_launch_description` 的函数，
    该函数返回一个 `LaunchDescription` 对象，描述要启动的所有动作（actions）。
    """

    # ────────────────────────────────────────────────────────
    # 1. 获取相关 ROS 2 包的安装路径（share directory）
    # ────────────────────────────────────────────────────────

    # 获取本项目导航包 'fishbot_navigation2' 的 share 目录路径
    # 通常包含 maps/、config/ 等资源文件
    fishbot_navigation2_dir = get_package_share_directory('fishbot_navigation2')

    # 获取官方 nav2_bringup 包的 share 目录路径
    # nav2_bringup 提供了标准的 Nav2 启动脚本和 RViz 配置
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    # 拼接 RViz 配置文件的完整路径：使用 nav2_bringup 自带的默认配置
    rviz_config_dir = os.path.join(
        nav2_bringup_dir, 'rviz', 'nav2_default_view.rviz'
    )

    # ────────────────────────────────────────────────────────
    # 2. 定义 Launch 配置参数（可被外部覆盖）
    # ────────────────────────────────────────────────────────

    # 定义 'use_sim_time' 参数：决定是否使用仿真时钟（Gazebo 时间）
    # 默认值为 'true'，适用于仿真环境；实机应设为 'false'
    use_sim_time = launch.substitutions.LaunchConfiguration(
        'use_sim_time', default='true'
    )

    # 定义 'map' 参数：指定要加载的地图 YAML 文件路径
    # 默认使用本项目 maps 目录下的 room.yaml
    map_yaml_path = launch.substitutions.LaunchConfiguration(
        'map', default=os.path.join(fishbot_navigation2_dir, 'maps', 'room.yaml')
    )

    # 定义 'params_file' 参数：指定 Nav2 的参数配置文件路径
    # 默认使用本项目 config 目录下的 nav2_params.yaml
    nav2_param_path = launch.substitutions.LaunchConfiguration(
        'params_file', default=os.path.join(fishbot_navigation2_dir, 'config', 'nav2_params.yaml')
    )

    # ────────────────────────────────────────────────────────
    # 3. 构建并返回完整的 LaunchDescription
    # ────────────────────────────────────────────────────────
    return launch.LaunchDescription([
        # 声明 launch 参数，允许用户在命令行覆盖默认值
        # 例如: ros2 launch ... use_sim_time:=false map:=/my/map.yaml

        launch.actions.DeclareLaunchArgument(
            'use_sim_time',
            default_value=use_sim_time,
            description='Use simulation (Gazebo) clock if true'
        ),

        launch.actions.DeclareLaunchArgument(
            'map',
            default_value=map_yaml_path,
            description='Full path to map file to load'
        ),

        launch.actions.DeclareLaunchArgument(
            'params_file',
            default_value=nav2_param_path,
            description='Full path to param file to load'
        ),

        # ────────────────────────────────────────────────────
        # 包含 Nav2 官方的 bringup_launch.py 启动文件
        # 这是启动整个 Nav2 导航栈的标准方式
        # ────────────────────────────────────────────────────
        launch.actions.IncludeLaunchDescription(
            # 指定要包含的 launch 文件来源（Python 类型）
            PythonLaunchDescriptionSource(
                [nav2_bringup_dir, '/launch', '/bringup_launch.py']
            ),
            # 将本 launch 文件的参数传递给被包含的 launch 文件
            # 注意：.items() 将字典转为 key-value 元组列表，符合接口要求
            launch_arguments={
                'map': map_yaml_path,
                'use_sim_time': use_sim_time,
                'params_file': nav2_param_path
            }.items(),
        ),

        # ────────────────────────────────────────────────────
        # 启动 RViz2 可视化工具，并加载预设配置
        # ────────────────────────────────────────────────────
        launch_ros.actions.Node(
            package='rviz2',           # 节点所在包
            executable='rviz2',        # 可执行文件名
            name='rviz2',              # 节点名称（可重映射）
            arguments=['-d', rviz_config_dir],  # 启动参数：加载指定 RViz 配置
            parameters=[{'use_sim_time': use_sim_time}],  # 传递参数（与仿真时钟同步）
            output='screen'            # 将日志输出到终端
        ),
    ])