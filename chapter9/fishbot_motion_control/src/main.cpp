#include <Arduino.h> // Arduino.h 是 PlatformIO/Arduino 框架的核心头文件，提供 setup()、loop()、delay() 等基础函数。
#include <Esp32McpwmMotor.h> // 引入 ESP32 MCPWM 电机控制库
// ESP32 有专用的 MCPWM 模块（支持 2 个独立单元，每个单元可驱动 3 路电机），比普通软件 PWM 更稳定、频率更高

Esp32McpwmMotor motor; //创建一个名为motor的对象，用于控制电机
// 同时控制最多 6 个电机（MCPWM0: 3路 + MCPWM1: 3路）。
// 名字叫 motor 容易误解为单电机，其实它是“电机控制器”。
// 这是 C++ 的面向对象编程（OOP）：Esp32McpwmMotor 是一个类（Class），motor 是它的实例（Object）。
// 通过这个对象，你可以调用 .attachMotor()、.updateMotorSpeed() 等方法。
void setup(){
    motor.attachMotor(0,5,4);
    motor.attachMotor(1,15,16);
    motor.attachMotor(2,3,8);
    motor.attachMotor(3,46,9);

}

/* 函数原型 void attachMotor(uint8_t motorIndex, uint8_t pwmPin, uint8_t dirPin);

- motorIndex：电机编号（0~5），最多6个
- pwmPin：连接到电机驱动模块 PWM 输入引脚 的 ESP32 GPIO
- dirPin：连接到电机驱动模块 方向控制引脚 的 ESP32 GPIO

这段代码配置了 4 个电机，每个电机需要 2 个 GPIO：
- PWM 引脚：输出 PWM 信号，控制转速
- DIR（方向）引脚：高/低电平控制正反转
*/


void loop(){
    motor.updateMotorSpeed(0,70); //设置电机0的速度（占空比）为70%
    motor.updateMotorSpeed(1,70); //设置电机1的速度（占空比）为70%
    motor.updateMotorSpeed(2,70); //设置电机2的速度（占空比）为70%
    motor.updateMotorSpeed(3,70); //设置电机3的速度（占空比）为70%
    delay(2000); //延迟2s

    motor.updateMotorSpeed(0,-70); //设置电机0的速度（占空比）为-70%
    motor.updateMotorSpeed(1,-70); //设置电机1的速度（占空比）为-70%
    motor.updateMotorSpeed(2,-70); //设置电机2的速度（占空比）为-70%
    motor.updateMotorSpeed(3,-70); //设置电机3的速度（占空比）为-70%
    delay(2000);

    motor.updateMotorSpeed(0, 0); // 停止电机
    motor.updateMotorSpeed(1, 0); // 停止电机
    motor.updateMotorSpeed(2, 0); // 停止电机
    motor.updateMotorSpeed(3, 0); // 停止电机
    delay(5000);
}

/*
核心概念详解：PWM 占空比（Duty Cycle）

什么是 PWM？
**PWM（Pulse Width Modulation，脉冲宽度调制）** 是一种通过**快速开关数字信号**来模拟“模拟电压”的技术。

占空比（Duty Cycle）定义：
> **占空比 = 高电平时间 / 一个周期总时间 × 100%**

例如：
- 周期 = 20ms（频率 50Hz）
- 高电平 = 2ms → 占空比 = 2/20 = **10%**
- 高电平 = 10ms → 占空比 = 10/20 = **50%**
- 高电平 = 18ms → 占空比 = 18/20 = **90%**

在电机控制中的作用：
| 占空比 | 电机表现 |
|--------|--------|
| 0%     | 完全停止（无动力） |
| 50%    | 中等转速 |
| 100%   | 最大转速（全功率） |

> 【新手笔记】  
> - 电机驱动模块（如 L298N）接收 PWM 信号后，会按比例调节输出到电机的**平均电压**。  
> - 例如：5V 电源 + 70% 占空比 ≈ 输出 3.5V 到电机 → 转速约为最大值的 70%。  
> - **占空比 ≠ 转速线性关系**（受电机特性、负载影响），但大致成正比。

为什么用 MCPWM 而不用普通 PWM？
| 普通 PWM (`analogWrite`) | MCPWM（硬件 PWM） |
|------------------------|------------------|
| 软件模拟，占用 CPU       | 硬件外设，不占 CPU |
| 频率低（通常 < 1kHz）    | 频率高（可达 100kHz+） |
| 多路时可能不同步         | 多路严格同步       |
| 不适合电机控制           | 专为电机/电源设计   |

*/