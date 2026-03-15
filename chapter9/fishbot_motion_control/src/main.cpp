/*通过getTicks()获取编码器数值，通过millis()函数获取当前时间。
接着计算编码器数值差，然后乘上参数0.1051566获取距离，最后除上时间差就得到了单位为mm/ms的速度数据，换算单位后刚好是m/s，
同时为了方便查看，我们利用Esp32McpwmMotor将两个电机的速度设置为70 %。
*/
/*核心修改点对比
|问题                  | 原因                                                     |   修复                       |
|按k不停车，来回震荡   |   error_sum_积累到2500，消退慢                           |   目标变化时立即清零积分     |
|转向切换响应迟钝      |   integral_up_=2500导致积分项最大贡献312，远超输出限幅   |   改为200，积分贡献最大25    |
|积分消退时间长        |   ki×integral_up = 312 >> 100                           |   调整后ki×integral_up = 25 |
最关键的改动是 update_target() 里检测目标变化时清零积分——这样按下 k 发出停止指令的瞬间，积分历史立刻清除，电机能立即响应新目标。*/
#include <Arduino.h>
#include <Esp32McpwmMotor.h>
#include <Esp32PcntEncoder.h> // 通过 MCPWM 外设 控制电机，支持正反转和 PWM 调速。
#include <PidController.h>    // 引入 PID 控制器头文件
#include <Kinematics.h>       // 引入运动学头文件

/*引入micro-ROS和WIFI相关的头文件*/
#include <WiFi.h>
#include <micro_ros_platformio.h>
#include <rcl/rcl.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>

/*添加速度话题的订阅者和回调函数*/
#include <geometry_msgs/msg/twist.h> //速度消息接口

/*添加发布者、进行时间同步和创建定时器*/
#include <nav_msgs/msg/odometry.h>                //里程计消息接口
#include <micro_ros_utilities/string_utilities.h> //为消息中的字符串分配空间和赋值

Kinematics kinematics;
Esp32PcntEncoder encoders[4];    // 是一个包含 4 个 Esp32PcntEncoder 对象的数组，分别对应 4 个电机的编码器。
Esp32McpwmMotor motor;           // 创建一个名为motor的对象，用于控制电机
PidController pid_controller[4]; // 创建 PID 控制器对象数组

int64_t last_ticks[4];  // 记录上一次读取的计数器数值
int32_t delta_ticks[4]; // 记录两次读取之间的计数器差值
// delta_ticks 用 int32_t 可能溢出（如果 dt 很小，Δticks 很大）
int64_t last_update_time; // 记录上一次更新时间
float current_speeds[4];  // 记录四个电机的速度

float target_linear_x_speed = 0.0; // 目标X方向线速度 毫米每秒,设置为0,防止小车一启动就开始运动
float target_linear_y_speed = 0.0; // 目标Y方向线速度 毫米每秒
float target_angular_speed = 0.0;  // 目标角速度 弧度每秒
float out_speed[4];                // 用于存储运动学逆解后的速度

/*声明结构体相关的对象*/
rcl_allocator_t allocator; // 内存分配器，用于动态内存分配管理
rclc_support_t support;    // 用于存储始终，内存分配器和上下艾提供支持
rclc_executor_t executor;  // 执行器，用于管理订阅和记事起回调的执行
rcl_node_t node;           // 节点

/*创建ros2中的订阅者与订阅消息的消息接口*/
rcl_subscription_t subscriber;     // 订阅者
geometry_msgs__msg__Twist sub_msg; // 储存订阅到的速度类型消息

/*创建ros2中的发布者与发布消息的消息接口*/
rcl_publisher_t odm_publisher;    // odom消息发布者
nav_msgs__msg__Odometry odom_msg; // 里程计消息
rcl_timer_t timer;                // 定时器，可以定时调用某个函数

/*定义接收到速度消息之后的回调函数
函数的主要功能是将twist格式的速度进行运动学逆解，得到小车具体的运动速度*/
void twist_callback(const void *msg_in)
{
    // 将接收到的消息指针转化为 gemometry_msgs_msg_Twist 类型
    const geometry_msgs__msg__Twist *twist_msg =
        (const geometry_msgs__msg__Twist *)msg_in;
    // ✅ 正确：在函数内部声明这些变量
    float out_wheel_speed1, out_wheel_speed2, out_wheel_speed3, out_wheel_speed4;
    // 运动学逆解并设置速度
    kinematics.kinematic_inverse(
        twist_msg->linear.x * 1000, // ros2订阅的速度是m/s,这里转变成mm/s
        twist_msg->linear.y * 1000, // 必须包含 linear_y_speed
        twist_msg->angular.z,
        out_wheel_speed1,
        out_wheel_speed2,
        out_wheel_speed3,
        out_wheel_speed4);
    pid_controller[0].update_target(out_wheel_speed1);
    pid_controller[1].update_target(out_wheel_speed2);
    pid_controller[2].update_target(out_wheel_speed3);
    pid_controller[3].update_target(out_wheel_speed4);
}

/*在定时器回调函数中完成话题发布吗，
由于在ros2系统中的回调函数是事件驱动，
而发布消息必须是主动的，因此需要你额外添加定时器来触发发布消息的函数*/
void publisher_callback(rcl_timer_t *timer, int64_t last_call_time)
{
    odom_t odom = kinematics.get_odom();                                        // 获取里程计信息
    int64_t stamp = rmw_uros_epoch_millis();                                    // 获取当前时间
    odom_msg.header.stamp.sec = static_cast<int32_t>(stamp / 1000);             // 秒部分
    odom_msg.header.stamp.nanosec = static_cast<int32_t>((stamp % 1000) * 1e6); // 纳秒部分
    odom_msg.pose.pose.position.x = odom.x;
    odom_msg.pose.pose.position.y = odom.y;
    /*odom_msg对角度的表示使用的是四元数，所以我们根据欧拉角Yaw角转四元数的公式，调用正余弦将欧拉角转成四元数*/
    odom_msg.pose.pose.orientation.w = cos(odom.yaw * 0.5);
    odom_msg.pose.pose.orientation.x = 0;
    odom_msg.pose.pose.orientation.y = 0;
    odom_msg.pose.pose.orientation.z = sin(odom.yaw * 0.5);
    odom_msg.twist.twist.angular.z = odom.angular_speed;
    odom_msg.twist.twist.linear.x = odom.linear_x_speed;
    odom_msg.twist.twist.linear.y = odom.linear_y_speed;
    // 发布里程计
    if (rcl_publish(&odm_publisher, &odom_msg, NULL) != RCL_RET_OK)
    {
        Serial.printf("error: odom publisher failed!\n");
    }
}

/*单独创建一个任务运行micro-ROS,相当于一个新的线程*/
/*以下是一个完整的micro-ROS节点的编写方法，
要和Agent建立通信，需要确保WIFI账户信息、Agent地址和端口号正确，
另外需要注意的是ESP32仅支持2.4 GHz的WIFI信号。*/
void micro_ros_task(void *parameter)
{
    // 1.谁知传输协议并且掩饰等待设置完成
    IPAddress agent_ip;
    agent_ip.fromString("192.168.3.3");
    set_microros_wifi_transports("isaaclab", "Tara000728", agent_ip, 8888);
    delay(2000); // 等待wifi连接完成
    // 2.初始化内存分配器
    allocator = rcl_get_default_allocator();
    // 3.初始化support
    rclc_support_init(&support, 0, NULL, &allocator);
    // 4.初始化节点 fishbot_motion_control
    rclc_node_init_default(&node, "fishbot_motion_control", "", &support);
    // 5.初始化执行器
    unsigned int num_handles = 2; // 添加订阅者回调函数之后的句柄加一,添加定时器发布者之后再加一
    rclc_executor_init(&executor, &support.context, num_handles, &allocator);
    // 6.初始化订阅者并添加到执行器当中
    rclc_subscription_init_best_effort(                         // best_effort即最大努力发布数据，
        &subscriber,                                            // 里程计发布者指针
        &node,                                                  // 节点指针
        ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist), // 消息接口
        "/cmd_vel"                                              // 话题名称
    );
    rclc_executor_add_subscription(
        &executor,
        &subscriber,
        &sub_msg,
        &twist_callback,
        ON_NEW_DATA);
    // 7.初始化发布者和定时器
    odom_msg.header.frame_id = micro_ros_string_utilities_set(
        odom_msg.header.frame_id, "odom");
    odom_msg.child_frame_id = micro_ros_string_utilities_set(
        odom_msg.child_frame_id, "base_footprint");
    rclc_publisher_init_best_effort(
        &odm_publisher,
        &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(nav_msgs, msg, Odometry),
        "/odom");
    // 8.时间同步
    while (!rmw_uros_epoch_synchronized()) // 如果没有时间同步
    {
        rmw_uros_sync_session(1000); // 尝试进行时间同步
        delay(10);
    }
    // 9. 创建定时器，间隔 50 ms 发布调用一次 callback_publisher 发布里程计话题
    rclc_timer_init_default(
        &timer,
        &support,
        RCL_MS_TO_NS(50),
        publisher_callback);
    rclc_executor_add_timer(&executor, &timer);

    // 循环执行器
    rclc_executor_spin(&executor);
}

void motorSpeedControl()
{
    // 计算时间差
    uint64_t current_time = millis();

    //  一行搞定：编码器数据传给kinematics，内部自动算速度+更新里程计
    kinematics.update_motor_speed(
        current_time,
        encoders[0].getTicks(),
        encoders[1].getTicks(),
        encoders[2].getTicks(),
        encoders[3].getTicks());

    // 用kinematics内部速度驱动PID
    for (int i = 0; i < 4; i++)
    {
        // 根据当前速度,更新电机速度值
        motor.updateMotorSpeed(i,
                               pid_controller[i].update(kinematics.get_motor_speed(i)));
    }
}

/*
void motorSpeedControl()
{
    // 计算时间差
    uint64_t dt = millis() - last_update_time;

    // 使用循环处理所有 4 个电机
    for (int i = 0; i < 4; i++)
    {
        // 计算编码器差值
        delta_ticks[i] = encoders[i].getTicks() - last_ticks[i];
        // 距离比时间获取速度单位 mm/ms 乘 1000 转换为 mm/s,方便 PID 计算
        current_speeds[i] = float(delta_ticks[i] * 105.1566) / dt;
        // 更新上一次计数器数值
        last_ticks[i] = encoders[i].getTicks();
        // 根据当前速度,更新电机速度值
        motor.updateMotorSpeed(i,
                               pid_controller[i].update(current_speeds[i]));
    }

    // 更新上一次更新时间
    last_update_time = millis();
    // 打印所有电机的速度数据
    Serial.printf("speed1=%f mm/s, speed2=%f mm/s, speed3=%f mm/s,sspeed4 = % f mm / s\n ",
                  current_speeds[0],
                  current_speeds[1],
                  current_speeds[2],
                  current_speeds[3]);
}
*/
void setup()
{

    // 1.初始化串口
    Serial.begin(115200); // 初始化串口通信，设置通信速率为115200
    motor.attachMotor(0, 5, 4);
    motor.attachMotor(1, 15, 16);
    motor.attachMotor(2, 3, 8);
    motor.attachMotor(3, 46, 9);
    /*attachMotor(id, pwmPin, dirPin) 含义：
       - pwmPin：输出 PWM 信号（控制转速）
       - dirPin：输出高低电平（控制正反转）*/

    // 2.设置编码器  init(unit, pinA, pinB)：将 A/B 相接到指定 GPIO，PCNT 硬件会自动判断方向并计数
    encoders[0].init(0, 6, 7);
    encoders[1].init(1, 18, 17);
    encoders[2].init(2, 20, 19);
    encoders[3].init(3, 11, 10);

    // 设置电机速度
    for (int i = 0; i < 4; i++)
    {
        pid_controller[i].update_pid(0.625, 0.125, 0.0);
        pid_controller[i].out_limit(-100, 100);
    }
    kinematics.set_wheel_distance(216, 177);
    kinematics.set_motor_param(0, 0.1051566);
    kinematics.set_motor_param(1, 0.1051566);
    kinematics.set_motor_param(2, 0.1051566);
    kinematics.set_motor_param(3, 0.1051566);

    // 运动学逆解并设置速度
    kinematics.kinematic_inverse(
        target_linear_x_speed,
        target_linear_y_speed,
        target_angular_speed,
        out_speed[0],
        out_speed[1],
        out_speed[2],
        out_speed[3]);

    // 设置电机速度
    for (int i = 0; i < 4; i++)
    { // 初始化目标速度，单位 mm/s，使用毫米防止浮点运算丢失精度
        pid_controller[i].update_target(out_speed[i]);
    }

    // 创建惹怒为运行mirco_ros_task
    xTaskCreate(
        micro_ros_task, // 任务函数
        "micro_ros",    // 任务名称
        10240,          // 任务堆栈大小(bit)
        NULL,           // 传递给人物函数的参数
        1,              // 任务优先级
        NULL            // 人物句柄
    );
}

void loop()
{
    delay(200);          // 等待10毫秒
    motorSpeedControl(); //
    Serial.printf("x=%f,y=%f,angle=%f\n",
                  kinematics.get_odom().x,
                  kinematics.get_odom().y,
                  kinematics.get_odom().yaw); // 不是angle
}