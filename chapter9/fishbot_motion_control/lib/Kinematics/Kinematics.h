#ifndef __KINEMATICS_H__ /* 防止头文件被多次包含 */
#define __KINEMATICS_H__

#include <Arduino.h> /* 包含 Arduino 核心库*/

// 定义一个结构体用于存储电机参数
typedef struct motor_param_t
{
    float per_pulse_distance;
    /* 单个脉冲对应轮子前进距离 */
    int16_t motor_speed;
    /* 当前电机速度 mm/s,计算时使用*/
    int64_t last_encoder_tick; /* 上次电机的编码器读数*/
};

/* 定义一个类用于处理机器人运动学 */
class Kinematics
{
public:
    /* 构造函数,默认实现 */
    Kinematics() = default;
    /* 析构函数,默认实现 */
    ~Kinematics() = default;

    /* 设置电机参数,包括编号和每个脉冲对应的轮子前进距离 */
    void set_motor_param(uint8_t id, float per_pulse_distance);
    /* 设置轮子间距*/
    void set_wheel_distance(float wheel_distance_a, float wheel_distance_b );

    /* 正运动学计算,将左右轮的速度转换为线速度和角速度*/
    void kinematic_forward(
        float wheel1_speed,
        float wheel2_speed,
        float wheel3_speed,
        float wheel4_speed,
        float &linear_x_speed,
        float &linear_y_speed,
        float &angular_speed);
    /* 逆运动学计算,将线速度和角速度转换为左右轮的速度*/
    void kinematic_inverse(
        float linear_x_speed,
        float linear_y_speed,
        float angular_speed,
        float &out_wheel1_speed,
        float &out_wheel2_speed,
        float &out_wheel3_speed,
        float &out_wheel4_speed);

    /* 更新电机速度和编码器数据*/
    void update_motor_speed(
        uint64_t current_time,
        int32_t motor_tick1,
        int32_t motor_tick2,
        int32_t motor_tick3, int32_t motor_tick4);
    /* 获取电机速度*/
    int16_t get_motor_speed(uint8_t id);

private:
    float wheel_distance_a_and_b_; // 轮子间距a和b方向
    float wheel_distance_a_;       // 轮子间距a方向
    float wheel_distance_b_;       // 轮子间距b方向
    motor_param_t motor_param_[4]; /* 存储四个电机的参数*/
    uint64_t last_update_time;
    /* 上次更新数据的时间,单位 ms*/
    float wheel_distance_;
    /* 轮子间距*/
};

#endif // __KINEMATICS_H__