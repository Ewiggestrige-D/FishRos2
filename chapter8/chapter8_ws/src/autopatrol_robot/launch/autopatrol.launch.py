"""
Fish ROS2 7.5.3
核心需求：启动机器人巡检并进行语音播报，并使用launch文件一次性启动多个节点,robot_state_publisher 和 joint_state_publisher

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
    # 1.获取默认的autopatrol_robot路径
    autopatrol_robot_path = get_package_share_directory('autopatrol_robot')
    default_patrol_config_path = os.path.join(autopatrol_robot_path,'config','patrol_config.yaml')
    action_patrol_node = launch_ros.actions.Node(
        package='autopatrol_robot',
        executable='patrol_node',
        # executable='patrol_node_optimized',
        parameters=[default_patrol_config_path],
        output = 'screen',
    )
    
    action_speaker_node = launch_ros.actions.Node(
        package= 'autopatrol_robot',
        executable= 'speaker',
        output = 'screen',
    )
    
    return launch.LaunchDescription([
        # Actions 动作
       action_patrol_node,
       action_speaker_node
    ])