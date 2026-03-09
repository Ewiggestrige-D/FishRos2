#include <Arduino.h>

// setup 函数，启动时调用一次
void setup()
{
    pinMode(48, OUTPUT); // 设置2号引脚模式为OUTPUT模式
}

// loop 函数，setup 后会被重复调用
void loop()
{
    digitalWrite(48, LOW); // 低电平，关闭LED灯 
    delay(1000); // 休眠1000ms 
    digitalWrite(48, HIGH); // 高电平，打开LED灯
    delay(1000); // 休眠1000ms 
}
