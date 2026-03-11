/*通过getTicks()获取编码器数值，通过millis()函数获取当前时间。
接着计算编码器数值差，然后乘上参数0.1051566获取距离，最后除上时间差就得到了单位为mm/ms的速度数据，换算单位后刚好是m/s，
同时为了方便查看，我们利用Esp32McpwmMotor将两个电机的速度设置为70 %。
*/

#include <Arduino.h>
#include <Esp32McpwmMotor.h>
#include <Esp32PcntEncoder.h> // 通过 MCPWM 外设 控制电机，支持正反转和 PWM 调速。
#include <PidController.h>    // 引入 PID 控制器头文件
#include <Kinematics.h>       // 引入运动学头文件

Kinematics kinematics;
Esp32PcntEncoder encoders[4];    // 是一个包含 4 个 Esp32PcntEncoder 对象的数组，分别对应 4 个电机的编码器。
Esp32McpwmMotor motor;           // 创建一个名为motor的对象，用于控制电机
PidController pid_controller[4]; // 创建 PID 控制器对象数组

int64_t last_ticks[4];  // 记录上一次读取的计数器数值
int32_t delta_ticks[4]; // 记录两次读取之间的计数器差值
// delta_ticks 用 int32_t 可能溢出（如果 dt 很小，Δticks 很大）
int64_t last_update_time; // 记录上一次更新时间
float current_speeds[4];  // 记录四个电机的速度

float target_linear_x_speed = 50.0; // 目标X方向线速度 毫米每秒
float target_linear_y_speed = 0.0;  // 目标Y方向线速度 毫米每秒
float target_angular_speed = 0.1f;  // 目标角速度 弧度每秒
float out_speed[4];                 // 用于存储运动学逆解后的速度

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
}

void loop()
{
    delay(200);           // 等待10毫秒
    motorSpeedControl(); // 
    Serial.printf("x=%f,y=%f,angle=%f\n", 
        kinematics.get_odom().x,
        kinematics.get_odom().y, 
        kinematics.get_odom().yaw); //不是angle
}