/*
引入了Esp32PcntEncoder库的头文件，接着创建了两个对象数组，
并在setup函数中使用init方法初始化编码器.
init方法的第一个参数是编码器编号，后面两个是编码器的引脚编号，引脚编号可以从FishBot驱动控制板原理图中查询。
最后在loop函数中，打印了编码器对脉冲的计数值。
*/

#include <Arduino.h> 
#include <Esp32PcntEncoder.h> 

/*
Esp32PcntEncoder encoders[4]; // 创建一个数组用于存储编码器


 void setup() 
 { // 1.初始化串口 
    Serial.begin(115200); // 初始化串口通信，设置通信速率为115200 
    // 2.设置编码器 
    encoders[0].init(0, 6, 7); 
    encoders[1].init(1, 18, 17); 
    encoders[2].init(2, 20, 19); 
    encoders[3].init(3, 11, 10); 
} 


void loop() 
{ 
    delay(10); // 等待10毫秒 
    // 读取并打印四个编码器的计数器数值 
    Serial.printf("tick1=%d,tick2=%d,tick3=%d,tick4=%d\n", 
        encoders[0].getTicks(), 
        encoders[1].getTicks(),
        encoders[2].getTicks(),
        encoders[3].getTicks()); 
}

*/