/*通过getTicks()获取编码器数值，通过millis()函数获取当前时间。
接着计算编码器数值差，然后乘上参数0.1051566获取距离，最后除上时间差就得到了单位为mm/ms的速度数据，换算单位后刚好是m/s，
同时为了方便查看，我们利用Esp32McpwmMotor将两个电机的速度设置为70 %。
*/

#include <Arduino.h> 
#include <Esp32McpwmMotor.h> 
#include <Esp32PcntEncoder.h> 


Esp32PcntEncoder encoders[4]; // 创建一个数组用于存储四个编码器 
Esp32McpwmMotor motor; // 创建一个名为motor的对象，用于控制电机 


int64_t last_ticks[4]; // 记录上一次读取的计数器数值 
int32_t delta_ticks[4]; // 记录两次读取之间的计数器差值 
int64_t last_update_time; // 记录上一次更新时间 
float current_speeds[4]; // 记录四个电机的速度 


void setup() 
{   
    // 1.初始化串口 
    Serial.begin(115200); // 初始化串口通信，设置通信速率为115200 
    motor.attachMotor(0, 5, 4); 
    motor.attachMotor(1, 15, 16); 
    motor.attachMotor(2, 3, 8); 
    motor.attachMotor(3, 46, 9); 
    
    
    // 2.设置编码器 
    encoders[0].init(0, 6, 7); 
    encoders[1].init(1, 18, 17); 
    encoders[2].init(2, 20, 19); 
    encoders[3].init(3, 11, 10);

    // 设置电机速度 
    for (int i = 0; i < 4; i++) 
    { 
        motor.updateMotorSpeed(i, 70);
    }
}

void loop() 
{ 
    delay(10); // 等待10毫秒 
    // 计算时间差 
    uint64_t dt = millis() - last_update_time; 
    

    // 使用for循环处理所有电机 
    for (int i = 0; i < 4; i++) { 
        // 计算编码器差值 
        delta_ticks[i] = encoders[i].getTicks() - last_ticks[i]; 
        // 距离比时间获取速度 单位 mm/ms 相当于 m/s 
        current_speeds[i] = float(delta_ticks[i] * 0.1051566) / dt; 
        // 更新上一次的计数器数值 
        last_ticks[i] = encoders[i].getTicks(); 
    } 
        
    
    // 更新数据 
    last_update_time = millis(); // 更新上一次更新时间 
    
    // 打印所有电机数据 
    Serial.printf("speeds: 1=%fm/s 2=%fm/s 3=%fm/s 4=%fm/s\n", 
        current_speeds[0], 
        current_speeds[1], 
        current_speeds[2], 
        current_speeds[3]); 

}