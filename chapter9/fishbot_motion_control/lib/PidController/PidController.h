/*定义了一个 PID 控制器类,其中成员函数 update 用于根据当前值计算下依次
输出值,update_target 函数用于设置目标值。*/

#ifndef __PIDCONTROLLER_H__ // 如果没有定义__PIDCONTROLLER_H__
#define __PIDCONTROLLER_H__ // 定义__PIDCONTROLLER_H__

class PidController
{ // 定义一个PID控制器类
public:
    PidController(/* args */) = default;         // 默认构造函数,不传参数也能创建对象
    PidController(float kp, float ki, float kd); // 带参构造函数.第二个构造函数允许你直接传入 PID 参数

private:
    float target_;  // 目标值
    float out_min_; // 输出下限
    float out_max_; // 输出上限
    float kp_;      // 比例系数
    float ki_;      // 积分系数
    float kd_;      // 微分系数

    // pid
    float error_sum_;          // 累计误差和
    float derror_;             // 误差变化率
    float error_last_;         // 上一次误差
    float error_pre_;          // 上上次误差
    float integral_up_ = 2500; // 积分上限

public:
    float update(float current);                   // 提供当前值，返回下次输出值
    void update_target(float target);              // 更新目标值
    void update_pid(float kp, float ki, float kd); // 更新PID系数
    void reset();                                  // 重置PID控制器
    void out_limit(float out_min, float out_max);  // 设置输出限制
};
#endif // __PIDCONTROLLER_H__结束条件
