"""
Fish ROS2 6.2.2
核心需求：在Rviz中显示仿真机器人，并使用launch文件一次性启动多个节点,robot_state_publisher 和 joint_state_publisher

在setup.py中的data_files中添加
('share/' + package_name+ "/launch", glob('launch/*.launch.py')),
来保证launch文件拷贝到install目录下 
"""
import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    """
    generate_launch_description 的 Docstring
    产生launch描述
    """
    # 1.获取功能包的share路径
    urdf_package_path = get_package_share_directory('fishbot_description')
    default_xacro_path = os.path.join(urdf_package_path,'urdf','fishbot/fishbot.urdf.xacro')
    #default_rviz2_model_path = os.path.join(urdf_package_path,'rviz_config','display_robot_model.rviz')
    #为了方便更换urdf模型文件，在launch中声明一个urdf目录的参数
    default_gazebo_world_path = os.path.join(urdf_package_path,'world','customer_room.world')
    action_declare_arg_model_path = launch.actions.DeclareLaunchArgument(
        name='model',
        default_value=str(default_xacro_path),
        description='加载的urdf模型文件路径'
    )
    
    # 通过文件路径获取内容，并转换成参数值对象，以供传入robot_state_publisher
    
    # 1. 使用bash命令，通过文件路径，获取文件内容
    # 注意此处xacro后面跟了一个空格，严格按照bash命令中的空格使用
    subsititutions_command_result = launch.substitutions.Command(['xacro ',launch.substitutions.LaunchConfiguration('model')])
    
    # 2.将文件内容转换为参数值对象
    robot_description_value = launch_ros.parameter_descriptions.ParameterValue(
        subsititutions_command_result,
        value_type=str
    )
    
    action_robot_state_publisher = launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description':robot_description_value}]
    )
    
    # gazebo中已经知道了各个关节的关系，因此不需要ros来发布
    action_launch_gazebo = launch.actions.IncludeLaunchDescription(
        launch.launch_description_sources.PythonLaunchDescriptionSource(
            [get_package_share_directory('gazebo_ros'),'/launch','/gazebo.launch.py']
        ),
        launch_arguments = [('world',default_gazebo_world_path),('verbose','true')]
    )
    
    action_spawn_entity = launch_ros.actions.Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic','/robot_description','-entity','fishbot']
    )
    # action_joint_state_publisher = launch_ros.actions.Node(
    #     package='joint_state_publisher',
    #     executable='joint_state_publisher',
    # )
    
    # action_rviz = launch_ros.actions.Node(
    #     package='rviz2',
    #     executable='rviz2',
    #     arguments=['-d' , default_rviz2_model_path]
    # )
    
    # 加载并激活 fishbot_joint_state_broadcaster 控制器
    actions_load_joint_state_controller = launch.actions.ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
            'fishbot_joint_state_broadcaster'],
        output='screen'
    )
    
     # 加载并激活 fishbot_effort_controller 控制器
    load_fishbot_effort_controller = launch.actions.ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active','fishbot_effort_controller'], 
        output='screen')
    load_fishbot_diff_drive_controller = launch.actions.ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active','fishbot_diff_drive_controller'], 
        output='screen')
    
    return launch.LaunchDescription([
        # Actions 动作
       action_declare_arg_model_path,
       action_robot_state_publisher,
       action_launch_gazebo,
       action_spawn_entity,
        # 事件动作，当加载机器人结束后执行   
       launch.actions.RegisterEventHandler(
           event_handler= launch.event_handlers.OnProcessExit(
               target_action = action_spawn_entity,
               on_exit = [actions_load_joint_state_controller],
           )
       ),
       # 事件动作，load_fishbot_diff_drive_controller
        launch.actions.RegisterEventHandler(
        event_handler=launch.event_handlers.OnProcessExit(
            target_action=actions_load_joint_state_controller,
            on_exit=[load_fishbot_diff_drive_controller],)
            ),
    ])