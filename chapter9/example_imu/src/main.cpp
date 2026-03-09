/* Get tilt angles on X and Y, and rotation angle on Z
 * Angles are given in degrees
 * 
 * License: MIT
 */

#include "Wire.h" //引入wire库，用于I2C通信
//Wire.h 是 Arduino 官方提供的 I²C（Inter-Integrated Circuit）通信库。I²C 是一种两线制串行通信协议（SDA 数据线 + SCL 时钟线），常用于连接传感器、显示屏等外设。


#include <MPU6050_light.h> //引入MPU6050库，用于与MPU6050传感器通信
// MPU6050_light.h 并非官方库，而是第三方轻量级封装库（由 jarzebski 开发），它内部使用 Wire 实现 I²C 通信，并封装了角度计算（互补滤波）。
// 这个库比原始寄存器操作简单得多，适合初学者快速获取角度数据

MPU6050 mpu(Wire); //创建MPU6050对象，使用wire对象进行通信
// 这里通过构造函数将 Wire 对象传给 mpu，表示“使用 I²C 总线与 MPU6050 通信”。如果你用的是其他 I²C 接口（如 ESP32 的 Wire1），也可以传 Wire1

unsigned long timer = 0; //用于计时的变量
// millis() 返回从程序启动至今的毫秒数（最大约 49 天后溢出）。用 timer 记录上次打印时间，实现“每 10ms 打印一次”的节流效果，避免串口输出太快导致卡顿。


void setup() {
  Serial.begin(115200); //初始化串口通信，波特率115200
  Wire.begin(12,13); //初始化I2C总线，设置SDA引脚为12,SCL引脚为13
  //在 ESP32 上，Wire.begin(SDA, SCL) 允许自定义引脚（如 12=SDA, 13=SCL）。
  //但在 Arduino Uno/Nano 等 AVR 芯片上，I²C 引脚是固定的（Uno 是 A4=SDA, A5=SCL），不能随意改！

  
  byte status = mpu.begin(); //启动MPU6050传感器并获取状态
  Serial.print(F("MPU6050 status: "));
  Serial.println(status);
  while(status!=0){ } // stop everything if could not connect to MPU6050
  // “stop everything” 实际是死循环卡住，不是优雅退出。在嵌入式系统中常见，但应说明。
  // mpu.begin() 尝试与 MPU6050 通信（读取 WHO_AM_I 寄存器）。返回 0 表示成功，非 0 表示失败（如接线错误、设备未供电、I²C 地址不对）。
  // 1：I²C 通信失败（最常见）
  // 2：设备 ID 不匹配（可能不是 MPU6050）


  Serial.println(F("Calculating offsets, do not move MPU6050")); //MPU6050 的陀螺仪和加速度计存在零偏误差（bias）。即使静止不动，读数也可能不是 0。
  // calcOffsets() 会在几秒内采样平均值，将这些偏差记录下来，后续计算角度时自动减去，从而提高精度。
  delay(1000);
  // mpu.upsideDownMounting = true; // uncomment this line if the MPU6050 is mounted upside-down
  // upsideDownMounting = true 用于翻转坐标系（比如模块焊反了），一般不用。

  mpu.calcOffsets(); // gyro and accelero 计算陀螺仪和加速度计的偏移量
  // calcOffsets() 默认采样 1 秒（约 100 次），前面的 delay(1000) 是为了让人看到提示信息。实际采样在 calcOffsets() 内部完成。
  Serial.println("Done!\n");
}

void loop() {
  mpu.update(); //更新MPU6050传感器的数据
  // 每次循环必须调用 mpu.update()，它会：
  // 从 MPU6050 读取原始加速度和角速度数据
  // 使用互补滤波算法融合两者，计算出更稳定的倾角（X/Y）和 Z 轴旋转角
  // 更新内部角度变量（供 getAngleX() 等函数使用）
  if(millis() - timer > 1000){ // print data every second
    Serial.print(F("TEMPERATURE: "));Serial.println(mpu.getTemp());
    Serial.print(F("ACCELERO  X: "));Serial.print(mpu.getAccX());
    Serial.print("\tY: ");Serial.print(mpu.getAccY());
    Serial.print("\tZ: ");Serial.println(mpu.getAccZ());
  
    Serial.print(F("GYRO      X: "));Serial.print(mpu.getGyroX());
    Serial.print("\tY: ");Serial.print(mpu.getGyroY());
    Serial.print("\tZ: ");Serial.println(mpu.getGyroZ());
  
    Serial.print(F("ACC ANGLE X: "));Serial.print(mpu.getAccAngleX());
    Serial.print("\tY: ");Serial.println(mpu.getAccAngleY());
    
    Serial.print(F("ANGLE     X: "));Serial.print(mpu.getAngleX());
    Serial.print("\tY: ");Serial.print(mpu.getAngleY());
    Serial.print("\tZ: ");Serial.println(mpu.getAngleZ());
    Serial.println(F("=====================================================\n"));
    timer = millis();
  }
/*
  // ms（100Hz）对串口输出来说非常快！可能导致串口缓冲区溢出或电脑端显示卡顿。建议改为 >100（10Hz）用于调试。
  if((millis()-timer)>100){ // print data every 10ms
	Serial.print("X : ");
	Serial.print(mpu.getAngleX()); //打印X轴的倾斜角度
	Serial.print("\tY : ");
	Serial.print(mpu.getAngleY());//打印Y轴的倾斜角度
	Serial.print("\tZ : ");
	Serial.println(mpu.getAngleZ()); //打印Z轴的旋转角度
    // 绕 Z 轴的偏航角（yaw）——但注意！MPU6050 没有磁力计，Z 轴角度会随时间漂移，不可靠！
	timer = millis();  

  }
*/
}
