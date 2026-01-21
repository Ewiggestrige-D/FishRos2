这是一个非常有洞察力的问题！你观察到当前参数声明方式是：

```python
self.declare_parameter('target_points', [0.0, 0.0, 0.0, 1.0, 1.0, 1.57])
# 表示两个点: (0,0,0) 和 (1,1,1.57)
```

而你希望的是更清晰的嵌套结构，比如：

```python
# 理想形式（但 ROS 2 参数不支持）
[
  [0.0, 0.0, 0.0],
  [1.0, 1.0, 1.57]
]
```

---

## ✅ 核心原因：**ROS 2 的 Parameter 系统不支持嵌套数组（nested arrays）**

### 📌 官方限制：
在 ROS 2（截至 Humble/Iron/Jazzy），**Parameter 只支持以下类型**：
- `bool`
- `int64`
- `double`
- `string`
- **一维数组**：`bool[]`, `int64[]`, `double[]`, `string[]`

> ❌ **不支持**：`double[][]`、`array of arrays`、`list of lists`、嵌套结构

这是由 **ROS 2 参数系统的底层设计（基于 YAML 1.0 子集 + DDS 限制）** 决定的。

---

## 🔍 验证：尝试声明嵌套数组会发生什么？

```python
# ❌ 这会报错！
self.declare_parameter('points', [[0.0, 0.0, 0.0], [1.0, 1.0, 1.57]])
```

错误信息类似：
```
TypeError: Invalid parameter type '<class 'list'>' for value '[...]'.
Only bool, int, float, str, list of bool/int/float/str are allowed.
```

即使你用 `rclpy.Parameter.Type.DOUBLE_ARRAY`，它也只接受 **一维列表**。

---

## ✅ 所以，为什么用“三个一组平铺”？

这是 **社区通用 workaround（变通方案）**，因为：

| 方案 | 是否可行 | 说明 |
|------|--------|------|
| `[[x,y,yaw], ...]` | ❌ 不支持 | ROS 2 参数系统拒绝嵌套 |
| `"[(0,0,0), (1,1,1.57)]"`（字符串）| ⚠️ 可行但麻烦 | 需要 `ast.literal_eval()` 解析，有安全风险 |
| **`[x1,y1,yaw1, x2,y2,yaw2, ...]`** | ✅ **推荐** | 简单、高效、无依赖 |

> 💡 **“三个一组平铺” 是 ROS 2 中表示多点坐标的事实标准**，Nav2 官方 launch 文件也这样用！

---

## ✅ 如何让代码更清晰？—— 封装解析逻辑

虽然参数必须平铺，但你可以在代码中 **立即转换为清晰的结构**：

```python
# 声明参数（平铺）
self.declare_parameter('target_points', [0.0, 0.0, 0.0, 1.0, 1.0, 1.57])

# 获取原始值
raw_points = self.get_parameter('target_points').value

# ✅ 转换为 [(x, y, yaw), ...] 结构（清晰！）
def parse_waypoints(flat_list):
    if len(flat_list) % 3 != 0:
        raise ValueError("target_points must be multiple of 3 (x, y, yaw)")
    return [
        (flat_list[i], flat_list[i+1], flat_list[i+2])
        for i in range(0, len(flat_list), 3)
    ]

self.waypoints_ = parse_waypoints(raw_points)
```

现在你在后续代码中就可以写：
```python
for x, y, yaw in self.waypoints_:
    pose = create_pose(x, y, yaw, "map", self.get_clock())
    goal_poses.append(pose)
```

> ✅ **既遵守了 ROS 2 限制，又保持了代码可读性！**

---

## 🛠 完整示例：清晰 + 兼容

```python
class PatrolNode(BasicNavigator):
    def __init__(self, node_name='patrol_robot', namespace=''):
        super().__init__(node_name, namespace)
        
        # 声明参数（必须平铺）
        self.declare_parameter('initial_point', [0.0, 0.0, 0.0])
        self.declare_parameter('target_points', [0.0, 0.0, 0.0, 1.0, 1.0, 1.57])
        
        # 解析初始点
        init_raw = self.get_parameter('initial_point').value
        self.initial_point_ = (init_raw[0], init_raw[1], init_raw[2])
        
        # 解析目标点列表
        targets_raw = self.get_parameter('target_points').value
        self.target_points_ = self._parse_waypoints(targets_raw)

    def _parse_waypoints(self, flat_list):
        """将 [x1,y1,y1, x2,y2,y2, ...] 转为 [(x1,y1,y1), (x2,y2,y2), ...]"""
        if len(flat_list) % 3 != 0:
            self.get_logger().error("target_points length must be divisible by 3!")
            raise ValueError("Invalid target_points format")
        return [
            (flat_list[i], flat_list[i+1], flat_list[i+2])
            for i in range(0, len(flat_list), 3)
        ]
```

---

## 📌 总结

| 问题 | 答案 |
|------|------|
| **为什么不能用嵌套数组？** | ❌ ROS 2 Parameter 系统**不支持嵌套数组**，仅支持一维数组 |
| **为什么用三个一组平铺？** | ✅ 这是**唯一可行的标准化 workaround**，被 Nav2 社区广泛采用 |
| **如何让代码清晰？** | ✅ **在获取参数后立即解析为结构化数据**（如 list of tuples） |

> 💡 **记住：参数声明受限于 ROS 2 接口，但你的内部代码可以（也应该）保持优雅和可读！**

这种“外部兼容、内部清晰”的模式，正是专业 ROS 2 开发的最佳实践。