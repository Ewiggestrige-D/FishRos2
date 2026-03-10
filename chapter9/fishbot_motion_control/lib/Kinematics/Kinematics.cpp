#include "Kinematics.h"

void Kinematics::set_motor_param(uint8_t id, float per_pulse_distance)
{
    motor_param_[id].per_pulse_distance = per_pulse_distance;
    /* 电机每个脉冲前进距离*/
}

void Kinematics::set_wheel_distance(float wheel_distance_a, float wheel_distance_b)
{
    wheel_distance_a_ = wheel_distance_a;
    wheel_distance_b_ = wheel_distance_b;
    wheel_distance_a_and_b_ = (wheel_distance_a_ + wheel_distance_b_) / 2;
}

// 传入电机的编号 id 返回该编号电机的速度
int16_t Kinematics::get_motor_speed(uint8_t id)
{
    return motor_param_[id].motor_speed;
}

/**
 * @brief 更新电机速度和编码器数据
 * @param current_time 当前时间(单位:毫秒)
 * @param left_tick 左轮编码器读数
 * @param right_tick 右轮编码器读数
 */
void Kinematics::update_motor_speed(uint64_t current_time, int32_t motor_tick1, int32_t motor_tick2, int32_t motor_tick3, int32_t motor_tick4)
{
    // 计算出自上次更新以来经过的时间 dt
    uint32_t dt = current_time - last_update_time;
    last_update_time = current_time;
    // 计算电机 1 和电机 2 的编码器读数变化量 dtick1 和 dtick2。
    int32_t dtick1 = motor_tick1 - motor_param_[0].last_encoder_tick;
    int32_t dtick2 = motor_tick2 - motor_param_[1].last_encoder_tick;
    int32_t dtick3 = motor_tick3 - motor_param_[2].last_encoder_tick;
    int32_t dtick4 = motor_tick4 - motor_param_[3].last_encoder_tick;
    motor_param_[0].last_encoder_tick = motor_tick1;
    motor_param_[1].last_encoder_tick = motor_tick2;
    motor_param_[2].last_encoder_tick = motor_tick3;
    motor_param_[3].last_encoder_tick = motor_tick4;

    // 轮子速度计算
    motor_param_[0].motor_speed =
        float(dtick1 * motor_param_[0].per_pulse_distance) / dt * 1000;
    motor_param_[1].motor_speed =
        float(dtick2 * motor_param_[1].per_pulse_distance) / dt * 1000;
    motor_param_[2].motor_speed =
        float(dtick2 * motor_param_[2].per_pulse_distance) / dt * 1000;
    motor_param_[3].motor_speed =
        float(dtick2 * motor_param_[3].per_pulse_distance) / dt * 1000;
}

/**
 * @brief 正运动学计算,将左右轮的速度转换为线速度和角速度
 * @param left_speed 左轮速度(单位:毫米/秒)
 * @param right_speed 右轮速度(单位:毫米/秒)
 * @param[out] out_linear_speed 线速度(单位:毫米/秒)
 * @param[out] out_angle_speed 角速度(单位:弧度/秒)
 */
void Kinematics::kinematic_forward(
    float wheel1_speed,
    float wheel2_speed,
    float wheel3_speed,
    float wheel4_speed,
    float &linear_x_speed,
    float &linear_y_speed,
    float &angular_speed)
{
    linear_x_speed = (wheel1_speed + wheel2_speed + wheel3_speed + wheel4_speed) / 4.0f;
    linear_y_speed = (-wheel1_speed + wheel2_speed + wheel3_speed - wheel4_speed) / 4.0f;
    angular_speed = float(-wheel1_speed + wheel2_speed - wheel3_speed + wheel4_speed) / (4.0f * (wheel_distance_a_and_b_));
}
/**
 * @brief 逆运动学计算,将线速度和角速度转换为左右轮的速度
 * @param linear_speed 线速度(单位:毫米/秒)
 * @param angle_speed 角速度(单位:弧度/秒)
 * @param[out] out_left_speed 左轮速度(单位:毫米/秒)
 * @param[out] out_right_speed 右轮速度(单位:毫米/秒)
 */
void Kinematics::kinematic_inverse(
    float linear_x_speed,
    float linear_y_speed,
    float angular_speed,
    float &out_wheel_speed1,
    float &out_wheel_speed2,
    float &out_wheel_speed3,
    float &out_wheel_speed4)
{
    out_wheel_speed1 = linear_x_speed - linear_y_speed - angular_speed * (wheel_distance_a_and_b_);
    out_wheel_speed2 = linear_x_speed + linear_y_speed + angular_speed * (wheel_distance_a_and_b_);
    out_wheel_speed3 = linear_x_speed + linear_y_speed - angular_speed * (wheel_distance_a_and_b_);
    out_wheel_speed4 = linear_x_speed - linear_y_speed + angular_speed * (wheel_distance_a_and_b_);
}