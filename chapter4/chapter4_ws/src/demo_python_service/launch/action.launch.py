"""
Fish ROS2 4.6.3
核心需求：launch使用进阶
"""
import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    """
    generate_launch_description 的 Docstring
    产生launch描述
    """
    action_declare_init_rqt = launch.actions.DeclareLaunchArgument(
        'init_rqt',default_value="False"
        )
    init_rqt = launch.substitutions.LaunchConfiguration('init_rqt',default="False")
    # 1.在这个launch中启动其他launch
    multisim_launch_path = [get_package_share_directory('turtlesim'),'/launch/','multisim.launch.py']
    action_include_launch = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            multisim_launch_path
        )
    )
    
    # 2.打印数据
    action_log_info = launch.actions.LogInfo(msg=str(multisim_launch_path))
    
    # 3.执行进程，即执行命令行
    action_topic_list = launch.actions.ExecuteProcess(
        cmd=['ros2','topic','list'],
        output = 'screen'
    )
    
    # 6.条件命令启动rqt
    # if init_rqt:
    #    run: rqt(in bash)
    actions_init_rqt = launch.actions.ExecuteProcess(
        condition = launch.conditions.IfCondition(init_rqt), 
        cmd=['rqt']

    )
    
    # 4.组合动作成组，把多个动作放到一组
    action_group = launch.actions.GroupAction([
        # 5.定时器,定时launch启动的时间
        launch.actions.TimerAction(period= 2.0,actions=[action_include_launch]),
        launch.actions.TimerAction(period= 4.0,actions=[action_log_info]),
        launch.actions.TimerAction(period= 5.0,actions=[actions_init_rqt])
    ])
    
    return launch.LaunchDescription([
        action_declare_init_rqt,
        action_log_info,
        action_group
    ])