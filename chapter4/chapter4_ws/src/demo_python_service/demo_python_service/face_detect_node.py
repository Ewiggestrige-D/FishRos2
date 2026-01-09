"""
Fish ROS2 4.2.3 Face Detection Service
核心需求：
1. 将ros中的图片转换为opencv的格式
2. 使用回调组进行线程并发，避免线程阻塞
3. 读取图片内容进行人脸识别,如果没有图片传入则回到默认图片
4. 使用自定义的消息接口输出图片中的内容，和识别耗时

需求：转换为opencv的格式 → 读取图片内容进行人脸识别 → 输出response
│
├─ 创建服务 → self.service_ = self.create_service(srv_type: Any,srv_name: str,callback:,*,qos_profile: QoSProfile = qos_profile_services_default,callback_group: CallbackGroup | None = None)
├─ 转换为opencv的格式 → self.bridge_ = CvBridge()
├─ 线程并发 避免阻塞 → rclpy.callback_groups.MutuallyExclusiveCallbackGroup()
├─ 判断是否有图片传入 → if request.image.data:
├─ 识别人脸 → ace_recognition.face_locations(image, number_of_times_to_upsample=2,model='hog')
├─ 返回结果 → return response
└─ 启动服务和回调组 → executor = rclpy.executors.MultiThreadedExecutor() → rclpy.spin(node, executor=executor)
"""
import rclpy 
from rclpy.node import Node

import chap4_interfaces
from chap4_interfaces.srv import FaceDetector #自定义的接口格式


import face_recognition
import cv2
from ament_index_python.packages import get_package_share_directory #获取功能包share目录绝对路径
import os
import time

from cv_bridge import CvBridge


class FaceDetectNode(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.get_logger().info(f'{node_name}减肥，启动！')
        self.detection_group = rclpy.callback_groups.MutuallyExclusiveCallbackGroup()
        """
        问题	                    优化方案	                         原因
        人脸检测阻塞主线程	使用 MultiThreadedExecutor + 回调组隔离	避免服务调用卡死整个节点
        未限制并发请求数	（可选）添加请求队列或限流	              防止 DoS（如高频调用耗尽 CPU）
        """
        self.service_ = self.create_service(
            FaceDetector,
            'face_detect',
            self.detect_face_callback,
            callback_group=self.detection_group
            )
        # 使用Cv bridge将ros的图片格式转换为opencv可以识别的格式
        self.bridge_ = CvBridge()
        # 将opencv中使用的参数提前作为node的一部分属性，方便后续调用修改
        # imgmsg_to_cv2() 可能抛出 CvBridgeError（如编码不支持、数据损坏）。
        # 必须捕获异常，否则服务会崩溃。
        self.number_of_times_to_upsample = 2
        self.model = 'hog'
        self.default_image_path = get_package_share_directory('demo_python_service') + '/resource/default.jpg'
        # 默认图像路径健壮性不足
        # 使用 get_package_share_directory 拼接路径，但未验证文件是否存在。
        # 若资源缺失，cv2.imread() 返回 None，后续操作会崩溃。
        print(f"图片的真实路径：{self.default_image_path}")
    """
    推荐最终架构

    class FaceDetectNode(Node):
        def __init__(self, node_name):
            super().__init__(node_name)
            # 声明参数
            self.declare_parameter('model', 'hog')
            self.declare_parameter('upsample', 2)
            # 创建服务（带回调组）
            self.detection_group = MutuallyExclusiveCallbackGroup()
            self.service_ = self.create_service(
                FaceDetector, 'face_detect', self.detect_face_callback,
                callback_group=self.detection_group
            )
            # 预加载默认图（带错误处理）
            # 初始化 CvBridge
    """



    def detect_face_callback(self,request,response):
        if request.image.data:
            cv_image = self.bridge_.imgmsg_to_cv2(request.image)
        else: 
            cv_image = cv2.imread(self.default_image_path) #已经是opencv格式的图像
            self.get_logger().warn(f'传入图像为空或传入失败，请检查！使用默认图像。')
            
        start_time = time.time()
        self.get_logger().info(f'开始识别，请稍等！')
        face_locations = face_recognition.face_locations(cv_image, self.number_of_times_to_upsample,self.model)
        # face_recognition.face_locations() 是 CPU 密集型操作，在 spin() 主线程中执行会阻塞整个节点（包括其他服务、订阅等）。
        # 高负载下会导致系统无响应。
        
        response.use_time = time.time() - start_time
        response.num_face = len(face_locations)
        self.get_logger().info(f'识别共耗时{response.use_time}秒')
        
        for top,right,bottom,left in face_locations:
            response.top.append(top)  
            response.right.append(right) 
            response.bottom.append(bottom) 
            response.left.append(left)  
            #这一段可以写成工具组
        return response # 必须返回response

    """
    为什么这些优化在工业场景至关重要？
    1. 可靠性：机器人系统 7×24 运行，不能因一张坏图崩溃。
    2. 实时性：人脸检测不应阻塞电机控制、SLAM 等关键任务。
    3. 可维护性：参数化配置让现场工程师无需改代码即可调优。
    4. 安全性：异常隔离防止局部故障扩散至整个系统。

    """
        
        
def main():
    rclpy.init()
    node = FaceDetectNode("face_detect_node")
    # 使用多线程执行器以支持并发回调
    executor = rclpy.executors.MultiThreadedExecutor()
    rclpy.spin(node, executor=executor)
    node.destroy_node()
    rclpy.shutdown()
    
    
    
    
    
    
"""
这是一个非常关键的**软件工程实践问题**！你提到的这段代码：

```python
for top, right, bottom, left in face_locations:
    response.top.append(top)  
    response.right.append(right) 
    response.bottom.append(bottom) 
    response.left.append(left)  
```

看似简单，但在真实工业级开发中，**绝不会以这种形式直接写在业务逻辑里**。下面我将从 **“什么是工具组” → “为什么需要它” → “如何实现” → “带来的工程价值”** 四个层面，为你彻底讲透。

---

## 🔧 一、什么是“工具组”（Utility Functions / Helper Module）？

> **工具组 = 一组与业务无关、可复用、高内聚的通用函数集合**

### 📌 特点：
- **无状态**：不依赖类成员变量，纯函数（输入 → 输出）
- **单一职责**：每个函数只做一件事（如“转换人脸框格式”）
- **跨模块复用**：可在多个节点、服务、包中调用
- **独立测试**：无需启动 ROS 节点即可单元测试

### 🌰 常见工具组示例：
- `image_utils.py`：图像裁剪、颜色转换、缩放
- `bbox_utils.py`：边界框格式转换（xywh ↔ tlbr）、IOU 计算
- `ros_msg_utils.py`：ROS 消息 ↔ Python 数据结构互转

---

## ❓ 二、为什么这段代码需要“工具化”？

### 当前代码的问题：
```python
# 问题1：硬编码字段名（top/right/bottom/left）
# 问题2：与特定消息类型（FaceDetector.Response）强耦合
# 问题3：无法复用于其他检测任务（如手部检测、车牌检测）
# 问题4：若消息定义变更（如改为 x/y/w/h），此处需重写
```

### 🎯 核心痛点：**违反“关注点分离”原则**
- **业务逻辑**（人脸检测）混杂了**数据格式转换逻辑**
- 导致代码难以维护、扩展、测试

---

## ✅ 三、如何将这段代码写成“工具函数”？

### 步骤 1：创建工具模块 `face_utils.py`
```python
# face_utils.py
from typing import List, Tuple

def face_locations_to_tlbr_lists(
    face_locations: List[Tuple[int, int, int, int]]
) -> Tuple[List[int], List[int], List[int], List[int]]:
    
    #将 face_recognition 的 face_locations 转换为四个独立列表。
    
    Args:
        face_locations: [(top, right, bottom, left), ...]
        
    Returns:
        (tops, rights, bottoms, lefts)
    
    if not face_locations:
        return [], [], [], []
    
    tops, rights, bottoms, lefts = zip(*face_locations)
    return list(tops), list(rights), list(bottoms), list(lefts)
```

### 步骤 2：在服务回调中调用
```python
# 在 detect_face_callback 中
from .face_utils import face_locations_to_tlbr_lists

# ...
tops, rights, bottoms, lefts = face_locations_to_tlbr_lists(face_locations)
response.top = tops
response.right = rights
response.bottom = bottoms
response.left = lefts
```

> 💡 注意：这里直接赋值 `response.top = tops`（而非 append），因为 `tops` 已是完整列表。

---

## 🌟 四、工具组带来的六大工程优势

| 维度  | 优化前（内联代码） | 优化后（工具函数） | 优势说明 |
|------|------------------|------------------|--------|
| **✅ 代码复用** | 仅用于人脸服务 | 可用于任何需要 tlbr 格式的模块 | 避免在手部检测、物体检测中重复写相同逻辑 |
| **✅ 代码规范** | 字段名散落在业务代码中 | 统一命名、文档化、类型提示 | 符合 PEP8，提升可读性 |
| **✅ 鲁棒性** | 无输入校验 | 可集中处理空列表、非法输入 | 如 `if not face_locations: return [],[],[],[]` |
| **✅ 业务逻辑清晰** | 混杂数据转换 | 业务只关注“检测→调用工具→返回” | 主流程更简洁，专注核心逻辑 |
| **✅ 可测试性** | 需启动 ROS 节点测试 | 纯函数，可独立单元测试 | `pytest test_face_utils.py` |
| **✅ 可维护性** | 消息格式变更需改多处 | 只需修改工具函数一处 | 如未来改为 `(x, y, w, h)`，只需重写工具函数 |

---

## 🏗️ 五、真实开发中何时使用工具组？

### ✅ 典型场景：
| 场景 | 工具组示例 |
|------|----------|
| **数据格式转换** | ROS msg ↔ OpenCV / NumPy / YOLO 格式 |
| **坐标系变换** | 像素坐标 ↔ 相机坐标 ↔ 世界坐标 |
| **几何计算** | 距离、角度、IOU、NMS（非极大值抑制） |
| **图像预处理** | 归一化、去畸变、ROI 裁剪 |
| **结果后处理** | 置信度过滤、类别映射、ID 跟踪 |

### ❌ 不适合工具组的场景：
- 高度依赖节点状态的逻辑（如访问 `self.e_stop`）
- 一次性、无复用价值的临时代码
---

## 📊 六、对比：内联 vs 工具组（代码演进视角）

### 假设需求变更：**新增“人脸中心点”字段**
#### 方案A：内联代码（灾难！）
```python
# 需要修改业务逻辑 + 修改消息定义 + 重新编译
centers_x = []
centers_y = []
for top, right, bottom, left in face_locations:
    response.top.append(top)
    # ... 其他 append
    centers_x.append((left + right) // 2)
    centers_y.append((top + bottom) // 2)
response.center_x = centers_x
response.center_y = centers_y
```

#### 方案B：工具组（优雅！）
```python
# 只需扩展工具函数
def face_locations_to_response_data(face_locations):
    tops, rights, bottoms, lefts = zip(*face_locations) if face_locations else ([], [], [], [])
    centers_x = [(l + r) // 2 for l, r in zip(lefts, rights)]
    centers_y = [(t + b) // 2 for t, b in zip(tops, bottoms)]
    return {
        'top': list(tops), 'right': list(rights),
        'bottom': list(bottoms), 'left': list(lefts),
        'center_x': centers_x, 'center_y': centers_y
    }

# 业务代码几乎不变
data = face_locations_to_response_data(face_locations)
for key, value in data.items():
    setattr(response, key, value)
```

> 💡 **这就是“开闭原则”（对扩展开放，对修改关闭）的体现！**

---

## ✅ 七、总结：工具组的核心价值

| 问题 | 答案 |
|------|------|
| **什么是工具组？** | 与业务解耦的通用函数集合 |
| **为什么用它？** | 避免重复、提升复用、增强鲁棒性 |
| **怎么写？** | 纯函数 + 类型提示 + 单元测试 |
| **何时用？** | 数据转换、几何计算、格式标准化等通用逻辑 |
| **工业价值？** | **降低 50%+ 重复代码，提升 3 倍维护效率** |

> 🌟 **终极心法**：  
> **“Don’t Repeat Yourself (DRY)” 不是一句口号，而是通过工具组落地的工程纪律。**  
> 在 ROS 2 大型项目中（如 Autoware、MoveIt），工具模块占比常超 30%——这正是专业与业余的分水岭。

"""