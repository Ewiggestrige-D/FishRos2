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



/*
## 🌟 一句话回答核心问题：

> **`public` 和 `private` 是 C++ 的“访问控制符”，用来规定“谁可以访问类的成员”。**
>
> **一个类中可以有多个 `public`/`private` 区块，这只是代码组织方式，功能上等价于合并成一个。**

下面详细展开。

---

## 🔐 一、`public` 和 `private` 到底是什么？有什么作用？

### ✅ 1. `private`（私有成员）
- **只有类内部的函数（成员函数）才能访问**
- **类外部（比如 `main()` 或其他类）不能直接读写**
- **作用**：**隐藏实现细节，保护数据安全**

### ✅ 2. `public`（公有成员）
- **任何地方都可以访问**（类内、类外、其他文件）
- **通常是提供给用户的“接口”**
- **作用**：**暴露可控的操作入口**

> 💡 这就是 **“封装（Encapsulation）”** —— OOP 三大特性之一！

---

### 🧩 举个生活例子：微波炉

| 微波炉部件 | 对应 C++ | 说明 |
|-----------|--------|------|
| **按钮、显示屏** | `public` 成员函数 | 用户可以按“加热30秒” |
| **内部电路、磁控管** | `private` 成员变量 | 用户不能直接碰，只能通过按钮间接控制 |

✅ 如果没有 `private`，用户可能：
- 直接改内部电压 → 烧毁
- 跳过安全检测 → 危险！

同样，在你的 `PidController` 中：
- 用户**只能通过 `update()` 获取输出**
- 不能直接改 `error_sum_`（否则积分会乱）

---

## 📂 二、为什么这个类中有**两个 `public`**？


这是**常见的代码组织习惯**：
1. **第一个 `public`**：放**构造函数和析构函数**（创建/销毁对象用）
2. **中间 `private`**：放**所有内部数据**（实现细节）
3. **第二个 `public`**：放**主要功能接口**（用户日常调用的方法）

> ✅ 这样写**逻辑清晰**：一眼看出“怎么创建对象” vs “怎么使用对象”。


### ⚖️ 两种写法对比

| 写法 | 优点 | 缺点 |
|------|------|------|
| **分两个 `public`** | 构造函数单独突出，结构层次清晰 | 多写一行 `public:` |
| **合一个 `public`** | 更紧凑，符合某些编码规范 | 构造函数淹没在方法列表中 |

> 📌 **C++ 标准不限制 `public`/`private` 出现次数**！  
*/