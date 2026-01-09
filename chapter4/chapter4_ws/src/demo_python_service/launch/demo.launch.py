"""
Fish ROS2 4.6.1 
Fish ROS2 4.6.2
核心需求：使用launch文件一次性启动多个节点,并传递参数

在setup.py中的data_files中添加
('share/' + package_name+ "/launch", glob('launch/*.launch.py')),
来保证launch文件拷贝到install目录下 
"""
import launch
import launch_ros


def generate_launch_description():
    """
    generate_launch_description 的 Docstring
    产生launch描述
    """
    # 1.手动声明一个launch的参数
    action_declare_args_background_g = launch.actions.DeclareLaunchArgument(
        'launch_arg_background_g',default_value="150"
        )
    """
    场景	                    参数名	           类型要求	                              原因
DeclareLaunchArgument(...)	default_value=	必须是字符串（str）	              因为 launch 参数在命令行中本质是字符串
LaunchConfiguration(...)	default=	    可以是任意类型（但通常也是 str）	它是 fallback 默认值，用于 launch 内部未声明时

- default_value（在 DeclareLaunchArgument 中）必须传字符串，即使你想表示数字。
- default（在 LaunchConfiguration 中）是备用默认值，类型灵活，但通常也用字符串保持一致。
- ROS 2 节点内部会自动将字符串 "150" 转换为整数 150（只要参数声明为 int）。

Launch 参数的来源是命令行：
```Bash
编辑
ros2 launch my_launch.py launch_arg_background_g:=200
```
- 命令行传入的 200 在 shell 中就是字符串。
- 为了统一处理，ROS 2 Launch 系统规定：所有 launch 参数的值在 launch 层面都是字符串。
- 即使你在代码中写 default_value=150（int），底层也会报错或行为未定义。
✅ 所以：default_value 必须是 str，这是设计约束。
    """
    # 2.把launch的参数手动传递给某个节点
    action_node_turtlesim_node= launch_ros.actions.Node(
        package='turtlesim',  # node所在功能包的名字
        executable='turtlesim_node', #可执行文件的名字
        parameters= [{'background_g' : launch.substitutions.LaunchConfiguration('launch_arg_background_g',default="150")}],
        # 从launch的参数中取得'launch_arg_background_g'的值，并将他转换为节点的参数进行赋值和替换substitution
        
        output = 'screen' # 日志输出的目的地
    )
    """
    为什么 LaunchConfiguration 用 default= 而不是 default_value=？

    原因：
    - LaunchConfiguration('name') 的作用是：“获取名为 name 的 launch 参数的值”。
    - 如果该参数未被声明或未传入，则使用 default= 作为回退值。
    - 这个 default 是 substitution 内部的 fallback，和 DeclareLaunchArgument 的 default_value 属于不同上下文，所以命名不同。
    
    📚 类比：
    DeclareLaunchArgument.default_value → “这个参数的默认值是什么？”
    LaunchConfiguration.default → “如果找不到这个参数，就用这个值代替”
    """
    
    action_node_turtle_control_service= launch_ros.actions.Node(
        package='demo_python_service',  # node所在功能包的名字
        executable='turtle_control_service', #可执行文件的名字
        output = 'log' # 日志输出的目的地
    )
    action_node_turtle_patrol_client= launch_ros.actions.Node(
        package='demo_python_service',  # node所在功能包的名字
        executable='turtle_patrol_client', #可执行文件的名字
        output = 'both' # 日志输出的目的地
    )
    return launch.LaunchDescription([
        # Actions 动作
        action_declare_args_background_g,
        action_node_turtlesim_node,
        action_node_turtle_control_service,
        action_node_turtle_patrol_client,
    ])