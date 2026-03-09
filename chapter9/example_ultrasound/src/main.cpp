#include <Arduino.h>

// 使用宏定义引脚编号
#define TRIG 21 // 设定发送引脚
#define ECHO 47 // 设置接收引脚


// setup 函数，启动时调用一次
void setup()
{
    Serial.begin(115200); //设置监听串口的波特率
    pinMode(TRIG,OUTPUT); //设置输出模式
    pinMode(ECHO,INPUT); //设置输入模式
}

// loop 函数，setup 后会被重复调用
void loop()
{ //产生一个10us的高脉冲超声波来测量距离
    digitalWrite(TRIG,HIGH);
    delayMicroseconds(10); //延时10微秒
    digitalWrite(TRIG,LOW);

    double delta_time = pulseIn(ECHO,HIGH); //检测高电平持续时间，注意返回值是微秒us
    float detect_distance = delta_time * 0.0343/2; //计算距离，单位cm,声速0.0343cm/us
    Serial.printf("distance =%f cm\n",detect_distance); //打印距离
    delay(500);
}
