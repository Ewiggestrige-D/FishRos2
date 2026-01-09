ros2 run turtlesim turtlesim_node (ros2 run <package_name> <excutable_name> 启动节点指令)

ros2 node info /turtlesim  (ros2 node info /<node_name> 查看节点订阅和发布的信息)

ros2 topic echo /turtle1/pose (ros2 topic echo <package_name>/<topic_name> 实时查看话题的内容)

ros2 topic info /turtle1/cmd_vel -v 
(-v 表示 verbose（详细模式）)
(ros2 topic echo <package_name>/<topic_name> 实时查看话题的信息和信息的标准格式)

ros2 interface show geometry_msgs/msg/Twist 
(ros2 interface show <package_name>/<topic_name> 查看消息接口的类型和定义)

ros2 topic pub /turtle1/cmd_vel geomotry_msgs/msg/Twist "{linear: {x: 1.0}}" 
(ros2 topic pub <topic_name> <interface_name>   “YAML格式的内容的数据填充“)


# Fish ROS2 3.4.3  ROS 2 自定义消息接口（Python 可用）通用创建流程

> 适用版本：ROS 2 Humble / Iron / Rolling
>
>目标语言：Python（但接口需通过 CMake 构建）
>
>接口类型：仅 .msg（消息），若需 .srv 或 .action，步骤类似

## 第一步：创建工作空间和功能包

### 进入工作空间（若无则创建）

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
```

### 创建接口包（必须用 ament_cmake！）

```bash
ros2 pkg create --build-type ament_cmake my_interfaces --dependencies <dependent_name>  --license Apache-2.0
```

## 第二步：创建 .msg 文件

### 创建 msg 目录
```bash
mkdir -p ~/ros2_ws/src/my_interfaces/msg
```
### 创建消息文件（首字母大写，.msg 后缀）
```bash
nano ~/ros2_ws/src/my_interfaces/msg/MyCustomData.msg
```

### 消息文件编写规范（关键！）

```python
# MyCustomData.msg —— 示例（无中文注释！）
builtin_interfaces/Time timestamp
string device_id
float32 temperature      # in Celsius
float32 humidity         # in %
int32 count
bool is_active
```
不要使用中文注释	                  可能导致 rosidl 解析失败
字段名只能是 ASCII 字母、数字、下划线	不能有空格、中文、特殊符号
类型和字段名之间用单个空格分隔	        如 float32 temp，不能 float32    temp
每行一个字段	                     不能合并
标准类型参考	                      bool, byte, char, int8/16/32/64, uint8/16/32/64, float32, float64, string, Time, Duration

## 第三步：修改 package.xml
编辑 ~/ros2_ws/src/my_interfaces/package.xml，确保包含以下内容：

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>my_interfaces</name>
  <version>0.0.0</version>
  <description>Custom message definitions</description>
  <maintainer email="user@example.com">Your Name</maintainer>
  <license>Apache-2.0</license>

  <!-- 构建工具 -->
  <buildtool_depend>ament_cmake</buildtool_depend>

  <!-- 如果用了 builtin_interfaces/Time 或 Duration -->
  <depend>builtin_interfaces</depend>

  <!-- 核心：消息生成依赖 -->
  <build_depend>rosidl_default_generators</build_depend>
  <exec_depend>rosidl_default_runtime</exec_depend>
  <member_of_group>rosidl_interface_packages</member_of_group>

  <!-- 可选：测试依赖 -->
  <test_depend>ament_lint_auto</test_depend>
  <test_depend>ament_lint_common</test_depend>

  <!-- 声明构建类型 -->
  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>

```
*** <member_of_group>rosidl_interface_packages</member_of_group> 是让 ros2 interface 能发现该包的关键！***


##  第四步：修改 CMakeLists.txt
编辑 ~/ros2_ws/src/my_interfaces/CMakeLists.txt，替换为以下内容：
```python
cmake_minimum_required(VERSION 3.8)
project(my_interfaces)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 查找依赖
find_package(ament_cmake REQUIRED)
find_package(builtin_interfaces REQUIRED)        # 如果用了 Time/Duration
find_package(rosidl_default_generators REQUIRED)

# 生成接口（列出所有 .msg 文件）
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/MyCustomData.msg"
  # 可添加更多： "msg/Another.msg" "msg/Third.msg"
  DEPENDENCIES
    builtin_interfaces   # 与上面 find_package 对应
    # 其他依赖包（如 std_msgs, geometry_msgs 等）
)

# 测试（可选）
if(BUILD_TESTING)
  find_package(AMENT_LINT_AUTO REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
```
1. 路径必须是 "msg/xxx.msg"，区分大小写
2. 如果没用 builtin_interfaces，可删除相关行
3. 多个 .msg 文件用空格分隔在同一行或换行加引号

## 第五步：清理并编译

```bash
cd ~/ros2_ws

# 清理旧构建（强烈推荐！）
rm -rf build/my_interfaces install/my_interfaces log/my_interfaces

# 编译接口包
colcon build --packages-select my_interfaces --event-handlers console_direct+
```

1. 输出中包含 Generating Python code for msg 'MyCustomData'
2. 无 InvalidFieldDefinition 或 error 报错

## 第六步：激活环境

```bash
source install/setup.bash
```

## 第七步：验证接口是否可用

```bash
# 1. 检查包是否被识别
ros2 pkg list | grep my_interfaces

# 2. 列出所有接口
ros2 interface list | grep MyCustomData

# 3. 显示接口定义
ros2 interface show my_interfaces/msg/MyCustomData

# 4. 在 Python 中导入测试
python3 -c "from my_interfaces.msg import MyCustomData; print('Success!')"
```

## 总结
1. 接口包必须用 ament_cmake
2. .msg 文件：纯 ASCII，无中文，格式严格
3. package.xml 必须包含 rosidl_interface_packages 组
4. CMakeLists.txt 正确调用 rosidl_generate_interfaces
5. 清理 + 编译 + source 三连
6. Python 中直接 from pkg.msg import MsgType