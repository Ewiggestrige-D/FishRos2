# **基础题**（定义与理解）：检验你对关键概念的准确掌握
# Q1. (阻塞操作的定义) 什么是“阻塞操作”？请举出两个 Python 中常见的阻塞操作例子，并说明为什么它们是阻塞的。

答：阻塞操作是指一个完全占用进程的操作,在单进程node中会导致node失联.常见的阻塞操作有download(), speaker.say()

A1：阻塞操作是指**在执行过程中会暂停当前线程的执行，直到操作完成的函数调用**。在ROS 2的单线程节点中，如果在回调函数中执行阻塞操作（如requests.get()、speaker.say()等），会**导致该线程被长时间占用，无法继续处理其他消息、定时器事件或其他回调，从而使整个节点"失去响应"**。例如，如果在novel_espeakng_callback中直接调用speaker.say(text)，语音合成需要几秒钟时间，这期间节点无法处理新消息，可能导致消息堆积甚至丢失。

# Q2. (回调函数运行线程) 在 ROS 2 的 rclpy.spin(node) 启动后，所有回调函数（如 timer、subscriber）默认在哪个线程中执行？为什么这会导致在回调中调用 requests.get() 会使整个节点“卡死”？

答：timer subscriber都在主线程中运行,在单线程node中再次调用requests.get()等阻塞操后,会导致线程在完成任务之前失去联系

评价：表述模糊，"失去联系"不专业，没有解释ROS 2事件循环机制。

A2：
在ROS 2的默认单线程执行器中，所有回调函数（包括定时器回调和订阅者回调）都在**同一个主线程**中执行。
如果在回调函数中调用阻塞操作（如requests.get()或speaker.say()），*该线程会一直被阻塞，直到操作完成*。
这意味着在阻塞期间，*ROS 2的事件循环无法处理其他消息*、定时器事件或回调，导致节点"**失去响应**"。
例如，如果在novel_espeakng_callback中调用speaker.say(text)，语音合成需要几秒钟，这期间节点无法处理其他消息，可能会导致消息堆积或丢失。

# Q3.(保存订阅对象为实例属性) 解释以下代码中 self.novel_publisher_ 的作用。如果不保存这个返回值（即只写 self.create_publisher(...)），可能会发生什么问题？

答：self.novel_subscriber_将创建订阅作为实例的属性,方便后续扩展和调用,同时防止长时间未调用被python的GC机制释放内存.

评价：表述不够精确，没有解释GC机制的具体工作原理。
A2：将create_subscription()的返回值保存为self.novel_subscriber_是必要的，因为：

1. 防止GC：如果只调用self.create_subscription(...)而不保存返回值，这个订阅对象将没有变量引用，可能会被Python的垃圾回收器（GC）意外销毁，导致订阅失效。
2. 资源管理：ROS 2需要知道订阅对象，以便在节点销毁时正确清理资源。
3. 未来扩展：如果需要在节点运行期间动态修改QoS或取消订阅，必须持有订阅对象的引用。

例如，如果未保存订阅对象，当节点的其他部分不再引用它时，GC可能会销毁它，导致节点无法接收消息。


[!NOTE]**Note:** 什么是“主线程”？
 在你的 main() 函数中：

```Python
def main():
    rclpy.init()
    node = NovelPubNode('novel_pub')
    rclpy.spin(node)   # ← 这一行所在的线程就是“主线程”
    ...
```
*rclpy.spin(node) 启动了 ROS 2 的事件循环（event loop） 这个事件循环运行在调用 spin() 的线程中 —— 也就是 主线程*
在默认情况下（即没有显式创建 MultiThreadedExecutor），**ROS 2 使用 SingleThreadedExecutor**
这个执行器会按顺序、在同一个线程（主线程）中调用所有回调函数：
定时器回调（timer_callback）
订阅者回调（msg_callback）
服务回调（srv_callback）
动作回调（action_callback）
所以：*所有回调都在主线程中串行执行。*
串行执行（Serial Execution） 指的是：

**多个任务按顺序一个接一个地执行，前一个任务必须完全结束后，后一个任务才能开始。**

# Q4.(QoS策略区别) QoS Profile 中的 ReliabilityPolicy.RELIABLE 和 BEST_EFFORT 有什么区别？分别适用于什么类型的 ROS 2 消息？
答：这个不知道 请详细解释

A4：RELIABLE和BEST_EFFORT是QoS中ReliabilityPolicy的两个选项，它们的区别在于消息传递的可靠性保证：

1. RELIABLE：**保证消息一定会被接收**。如果接收方没有确认收到消息，发布者会重传，直到消息被接收。这类似于TCP的可靠传输，适用于关键控制命令，如机器人运动控制。**缺点是可能引入延迟，因为需要等待确认和重传**。
2. BEST_EFFORT：**不保证消息一定会被接收**。如果网络问题导致消息丢失，发布者不会重传，接收者可能会丢失消息。这类似于UDP的传输，适用于传感器数据（如摄像头、激光雷达），因为**可以接受偶尔的丢帧，且对延迟要求高**。
使用场景：

RELIABLE：用于需要确保消息到达的场景，如机器人控制指令、配置更新。
BEST_EFFORT：用于*高频、可接受偶尔丢失的数据*，如传感器数据。


# Q5.(临时变量与实例属性) 在 Python 类中，为什么临时变量（如消息对象 msg）不应该定义为实例属性（如 self.msg）？请从语义、线程安全、内存三个角度简要说明。

答：语义上 msg是临时数据,每次获取的数据不一定完全相同,因此不应该定义为self的属性 线程安全上,作为self.mas可能会被全局调用,和反复修改导致线程被占用. self.msg也会导致内存一直被占用

评价：表述不准确，"self.mas"应为"self.msg"，"线程被占用"表述错误。

A5：
在ROS 2中，消息对象（如msg）是回调函数的参数，表示当前收到的消息。将消息对象保存为self.msg是不合适的，原因有：

1. 语义不清晰：self.msg暗示**这是节点的"当前消息"**，但实际上消息是**临时的**，每次回调都会收到新的消息。将它们保存为实例属性会导致"当前消息"被后续消息覆盖，无法保留历史消息。
2. 线程安全问题：虽然ROS 2的回调通常在单线程中执行，但未来可能使用多线程执行器，**如果多个线程同时访问self.msg，可能会导致数据竞争。**
3. 内存浪费：self.msg会一直持有最新消息的引用，即使消息已经处理完毕，也会占用内存。
4. 正确做法：在回调函数中处理消息后，将需要保留的数据（如msg.data）放入队列或进行其他处理，而不是保存整个消息对象。


# **应用题**（方法与实践）：测试你在真实代码场景中的判断力

# Q6.(download()函数的bug) 以下 download() 函数存在一个严重 bug，会导致程序崩溃。请指出并修复：
```python
def download(self, url):
    print(f'开始下载：{url}')
    response.encoding = 'utf-8'   # ← 问题在这里！
    text = response.text
    for line in text.splitlines():
        self.novels_queue_.put(line)

```
答：应该是self.response.encoding='utf-8',如果不加self那么就是函数的局内变量,,实例化之后不会被实例对象调用

评价：语法错误，self.response是错误的，response是局部变量。

A6：**代码中缺少对response的赋值**，正确的写法应该是：

```Python
response = requests.get(url)  # 先获取响应
response.encoding = 'utf-8'   # 设置编码
text = response.text
```
原代码的问题是response没有被定义（即没有response = requests.get(url)），所以response.encoding会抛出NameError。self.response是错误的，**因为response是函数内的局部变量，不是实例属性**。

# Q7.(高频传感器话题的QoS配置) 假设你有一个高频传感器话题 /imu（每秒 100 条消息），你只想处理最新的一条数据，且允许偶尔丢帧。请写出合适的 QoS 配置用于订阅该话题。

答：
```python
qos = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,   # 可靠传输（类似 TCP）
    history=HistoryPolicy.KEEP_LAST,
    depth=100,                                 # 缓存最近 100条
    durability=DurabilityPolicy.TRANSIENT_LOCAL    # 不保存给后来者
)
```
评价：QoS配置与场景不匹配，RELIABLE和TRANSIENT_LOCAL与"允许偶尔丢帧"的场景不符。

A7：对于高频传感器数据（如每秒100条消息），应该使用BEST_EFFORT可靠性策略，不保存历史消息，因为：

1. 我们只需要最新的数据，不需要重传
2. 允许偶尔丢帧（因为数据是高频的，丢帧影响不大）
3. 不需要保存给后来的订阅者
正确的QoS配置应该是：
```Python

from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

qos = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,  # 不保证消息到达
    history=HistoryPolicy.KEEP_LAST,           # 只保留最新消息
    depth=1,                                   # 只保留最新1条消息
    durability=DurabilityPolicy.VOLATILE       # 不保存给后来者,
    # 新订阅者是否需要历史？	→ 不需要！ IMU 数据是瞬时的，5秒前的加速度对现在没意义
)
```
高频 + **实时性要求高** → 通常不需要给后来者（用 VOLATILE）
低频 + **状态/配置类** → 通常需要给后来者（用 TRANSIENT_LOCAL）


# Q8.(队列线程安全性) 你的 timer_callback 如下所示。请问这段代码是否安全？为什么？如果将来你改用多线程执行器（multi-threaded executor），会有什么风险？
```python
def timer_callback(self):
    if not self.novels_queue_.empty():
        line = self.novels_queue_.get()
        msg = String()
        msg.data = line
        self.publisher_.publish(msg)
```

答：对于Queue的线程安全性和其他数据结构都不是很了解

A8：queue.Queue是*线程安全*的，**因为它是Python标准库中专门为多线程环境设计的线程安全队列**。它**内部使用锁**来确保在多线程环境中对队列的访问是安全的。这意味着：

1. put()和get()方法都是原子操作，不会发生数据竞争
2. 不需要额外的锁来保护队列操作
例如，在sub_node中，self.novels_queue_.put(line)和self.novels_queue_.get()是线程安全的，可以安全地在多个线程中调用。

但是，如果使用其他数据结构（如list），则需要额外的锁来保证线程安全。例如，使用list时：

```Python
# 不安全的写法
self.novels_list.append(line)  # 可能被多个线程同时访问，导致数据不一致

# 安全的写法
with self.lock:
    self.novels_list.append(line)
```


# Q9.(ROS功能架构) 你在 sub_node 中使用了子线程 speaker_thread 来朗读文本。为什么不能直接在 novel_espeakng_callback 中调用 speaker.say(text)？这样做会违反 ROS 2 的哪条黄金法则？

答：违反了单一功能原则.每个函数应该只负责一个单一功能,方便扩展调用或者在子类进行方法的重写或者调用多种回调函数

评价：表述不准确，这不是单一功能原则的问题。

A9：在ROS 2的回调函数中直接调用speaker.say(text)是违反了ROS 2的**非阻塞原则**。ROS 2的回调函数应该快速返回，不能执行长时间阻塞的操作。原因如下：

1. 节点失联：如果在回调中执行阻塞操作（如语音合成），该线程会一直被占用，无法处理其他消息或定时器事件，导致节点失去响应。
2. 消息堆积：如果消息到达速度比处理速度快，会导致消息堆积，可能使队列溢出。
正确的做法是**将阻塞操作放入单独的线程中**，如sub_node中的speaker_thread，*这样回调函数可以快速返回，保持节点响应*。


# Q10.(无法收到消息的原因) 你运行 ros2 topic echo /novel 却收不到任何消息，但 pub_node 显示正在发布。列出三种可能的原因（至少两种与 QoS 相关）。
答：
1. 环境变量没有激活(即没有使用source install/setup.bash命令)  
2. 发布者发布的接口不是novel
3. QoS策略为DurabilityPolicy.Volatile 对后来订阅者不可见  
4. reliability策略为best effort,出现了丢包
5. QoS历史消息策略为不保存历史消息或者保存历史消息深度depth为0

评价：表述不准确，"环境变量没有激活"与ROS 2通信问题无关。

优化答案：

无法收到消息的常见原因：

1. QoS策略不匹配：**发布者和订阅者的QoS策略必须兼容**。例如：
    1. 发布者使用RELIABLE，而订阅者使用BEST_EFFORT
    2. 发布者设置durability=DurabilityPolicy.TRANSIENT_LOCAL，而订阅者使用VOLATILE
2. topic名称不一致：发布者和订阅者使用的topic名称不一致，如发布者使用'novel'，订阅者使用'novel_topic'
3. QoS深度设置过小：发布者或订阅者的depth设置为0，导致没有缓存消息。
4. 节点启动顺序问题：如果订阅者在发布者之前启动，且发布者使用VOLATILE（默认），则订阅者可能收不到消息（因为发布者不保存消息给后来的订阅者）。

核心原则：**QoS 是“协商”而非“匹配”**
DDS 的设计哲学是：

“只要双方的 QoS 要求不冲突，就建立连接。”

这意味着：

1. 发布者声明：“我按这种方式发”
2. 订阅者声明：“我能接受这种方式收”
3. 只要订阅者的 QoS 不低于 发布者的要求（或在某些策略上更宽松），就能通信

 二、各 QoS 策略的兼容规则
1. Reliability（可靠性）
Pub \ Sub	RELIABLE	BEST_EFFORT
RELIABLE	✅ 兼容	    ❌ 不兼容
BEST_EFFORT	✅ 兼容	    ✅ 兼容
规则：

如果发布者是 BEST_EFFORT（尽力而为），订阅者无论是 RELIABLE 还是 BEST_EFFORT 都能收到消息（但无法获得可靠性保证）。
如果发布者是 RELIABLE（可靠传输），订阅者也必须是 RELIABLE，否则 *DDS 认为“你要求可靠但我只能尽力”，拒绝连接*。

2. Durability（持久性）
Pub \ Sub	     TRANSIENT_LOCAL	VOLATILE
TRANSIENT_LOCAL	  ✅ 兼容	        ✅ 兼容
VOLATILE	      ❌ 不兼容	        ✅ 兼容

规则：

如果发布者是 TRANSIENT_LOCAL（保存历史消息），订阅者无论是 VOLATILE 还是 TRANSIENT_LOCAL 都能连接。
VOLATILE 订阅者：只收新消息（忽略历史）
TRANSIENT_LOCAL 订阅者：收到所有历史 + 新消息
如果发布者是 VOLATILE（不保存历史），订阅者不能要求 TRANSIENT_LOCAL，因为发布者根本没存历史数据。

3. History + Depth
兼容性主要看 HistoryPolicy
KEEP_LAST vs KEEP_ALL：通常兼容
depth：取 min(pub.depth, sub.depth) 作为实际缓存深度

# **创新/拓展题**（综合与设计）：挑战你对系统设计和工程思维的理解

# Q11. 【设计题】(动态切换小说功能) 现在你需要支持“动态切换小说”功能：当收到一个服务请求（如 SetNovel）时，停止当前朗读，下载新小说并重新开始发布。请画出你设计的 NovelPubNode 类新增的组件（服务、状态标志等），并说明如何避免在服务回调中阻塞。

答：在speaker_thread(self)中加入while循环打断朗读  将原来的self.speech_thread_ = threading.Thread(target=self.speaker_thread)线程结束之后 用setnovel重新更换url地址然后重新下载
然后重新调用init 函数 回调novel_espeakng_callback函数进行朗读
具体代码怎么写不知道

A11：
要实现动态切换小说功能，我们需要：

1. 创建一个服务接口SetNovel，接收新URL
2. 在服务回调中，停止当前下载和朗读，开始下载新小说
3. 使用队列机制确保数据安全
以下是优化后的实现：

```Python
from rclpy.service import Service
from example_interfaces.srv import SetString

class NovelPubNode(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.novels_queue_ = Queue()
        self.novel_publisher_ = self.create_publisher(String, 'novel', 10)
        self.set_novel_service = self.create_service(SetString, 'set_novel', self.set_novel_callback)
        self.current_url = None
        self.download_thread = None

    def set_novel_callback(self, request, response):
        # 停止当前下载
        if self.download_thread and self.download_thread.is_alive():
            self.download_thread.join()  # 等待当前下载完成
        # 设置新URL
        self.current_url = request.data
        # 开始新下载
        self.download_thread = threading.Thread(target=self.download, args=(self.current_url,))
        self.download_thread.start()
        response.success = True
        return response

    def download(self, url):
        response = requests.get(url)
        response.encoding = 'utf-8'
        text = response.text
        for line in text.splitlines():
            self.novels_queue_.put(line)
        # 下载完成后，可以发送一个信号或设置标志
        # 例如：self.download_complete = True
```
实现思路：

1. 创建SetString服务，允许外部设置新URL
2. 在服务回调中，先停止当前下载（如果正在下载），然后开始新下载
3. 使用threading.Thread来执行下载，避免阻塞节点
4. 通过self.current_url跟踪当前URL，确保下载的是最新URL
5. 通过self.download_thread管理下载线程，确保不会同时进行多个下载


# Q12. 【优化题】(阻塞队列与时间通知机制) 当前 sub_node 使用 time.sleep(1) 轮询队列，导致朗读延迟最高达 1 秒。请提出一种更高效的方式（不使用 sleep）来实现“有数据就读，无数据就等”，并写出核心代码。  提示：可考虑 queue.Queue 的阻塞特性或事件通知机制。

答：对Queue的阻塞机制和时间通知机制不太了解,请详细解释 并给出详细的示例代码再额外举个例子来说明

A12:queue.Queue的阻塞机制是它的一个关键特性，**允许在队列为空时阻塞等待，而无需轮询。**

阻塞机制：
1. get()方法默认会阻塞，直到队列中有数据
2. 可以通过timeout参数设置超时时间，如果超时则返回None
示例代码：

```Python

def speaker_thread(self):
    speaker = espeakng.Speaker()
    speaker.voice = 'zh'
    while rclpy.ok():
        try:
            text = self.novels_queue_.get(timeout=1.0)  # 阻塞等待1秒
            self.get_logger().info(f'朗读: {text}')
            speaker.say(text)
            speaker.wait()
        except queue.Empty:
            # 队列为空，继续等待
            continue
```
解释：

1. get(timeout=1.0)会等待最多1秒，如果1秒内没有数据，会抛出queue.Empty异常
2. 这比使用time.sleep(1)更高效，因为不会浪费CPU资源等待
额外例子：
假设我们需要一个队列，当没有数据时等待最多2秒，然后退出：

```Python

def worker(self):
    while True:
        try:
            item = self.work_queue.get(timeout=2.0)
            # 处理item
        except queue.Empty:
            # 2秒内没有数据，退出
            break
```

# Q13. 【架构题】(保存所有消息的QoS配置) 如果要求“即使订阅者晚启动，也能收到小说的第一行”，你应该修改发布者的 QoS 策略。请写出完整的 QoS 配置，并解释 DurabilityPolicy.TRANSIENT_LOCAL 的作用。

答：qos = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,   # 可靠传输（类似 TCP）
    history=HistoryPolicy.KEEP_All, #保存所有记录,后来者访问全部 不会丢失
    depth=100,                                 # 缓存最近 100条
    durability=DurabilityPolicy.TRANSIENT_LOCAL    # 保存给后来者
)

评价：*depth=100与KEEP_ALL冲突，因为KEEP_ALL表示保留所有消息，depth参数不适用。*

A13：
如果需要确保新订阅者能收到所有历史消息，应该使用：

```Python
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

qos = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,  # 确保消息不丢失
    history=HistoryPolicy.KEEP_ALL,         # 保留所有消息
    durability=DurabilityPolicy.TRANSIENT_LOCAL  # 保存给后来的订阅者
)
```
说明：

1. KEEP_ALL表示发布者会保存所有消息，而不是只保留最近的N条
2. TRANSIENT_LOCAL表示消息会保存在本地，新订阅者可以收到所有历史消息
3. RELIABLE确保消息传输可靠，不会丢失
注意：depth参数在KEEP_ALL时被忽略，因为不需要指定深度。

# Q14. 【调试题】(DDS和FastDDS) 你发现 pub_node 和 sub_node 在同一台机器能通信，但在两台不同机器上无法通信。已知网络连通，DDS 实现为 Fast DDS。请列出两个可能的配置问题及解决方法。

答：对DDS和FastDDS并不了解

A14:

DDS (Data Distribution Service) 是一个用于实时系统的通信中间件标准，ROS 2 使用 DDS 作为底层通信机制。Fast DDS 是 DDS 的一个具体实现（由eProsima开发）。

为什么 ROS 2 使用 DDS：

1. DDS 提供了**高级通信功能**，如 **QoS 策略，可以精确控制消息传递**
2. DDS 是为**实时系统设计**的，适合机器人应用
DDS 的核心概念：

1. Domain：逻辑通信空间，节点必须在同一域
2. Participant：代表一个节点
3. Topic：数据分类，如'novel'
4. Publisher：发布消息的节点
5. Subscriber：订阅消息的节点
6. QoS：控制通信质量的策略

Fast DDS 问题：
如果在两台不同机器上无法通信，可能的原因：

1. 网络配置：两台机器的防火墙或网络设置阻止了通信
2. DDS 配置：Fast DDS 的 IP 地址配置不正确
解决方法：

1. 检查网络连通性（如ping）
2. 设置 Fast DDS 的 IP 地址（在~/.ros2/中配置）
3. 确保两台机器使用相同的域（默认域是0）

一、什么是 Domain（域）？
Domain 是 DDS 中的一个逻辑隔离单元，用于将通信“分组”。

1. 每个 Domain 用一个 整数 ID 标识（默认是 0）
2. 只有在同一 Domain ID 内的节点才能互相发现和通信
3. 不同 Domain 的节点 完全隔离，即使在同一台机器上也收不到彼此的消息

二、为什么不同 IP 的机器能通信？关键在 DDS 的“发现机制”
DDS 使用“自动发现协议”跨网络找到彼此，但前提是它们在同一个 **Domain**！
 DDS 发现过程（简化）：
启动节点时
节点向 预定义的多播地址（如 239.255.0.1:7400）发送“我是谁”的消息
消息中包含：Domain ID、节点名、Topic 名、QoS 等信息
其他节点监听多播地址
如果 Domain ID 相同 → 继续握手，建立点对点连接
如果 Domain ID 不同 → 忽略该消息（逻辑隔离）
建立直接连接
**一旦发现彼此，后续消息通过 单播（Unicast） 直接传输（不再走多播）**
即使 IP 不同，只要网络连通，就能通信

Domain（域）是 DDS（Data Distribution Service）规范中定义的一个逻辑通信隔离单元，由一个非负整数（Domain ID）标识。它不是“内部实现细节”，而是 DDS 核心通信模型的显式、标准化组成部分**，用于在运行时将参与通信的实体（如 Publisher 和 Subscriber）划分为互不干扰的逻辑组。所有使用相同 Domain ID 的 DDS 实体才能相互发现和交换数据，无论它们位于同一进程、同一主机还是不同网络节点。**

# Q15. 【思想题】(DDS与机器人应用) 为什么 ROS 2 选择 DDS 作为底层通信中间件？QoS 机制如何体现“一次编写，到处部署”的理念？请结合自动驾驶和工业机器人两个场景说明。
答：DDS可靠且QoS策略灵活,符合现在机器人工业的需求.
这两道关于DDS和中间件还有DDS分发机制以及分发机制可能导致的问题不是很清楚请详细解释病句利用代码说明如何改正出现的错误

A15:
DDS（Data Distribution Service）是ROS 2的底层通信机制，**其核心优势在于可靠性和QoS策略的灵活性**，这使它非常适合机器人应用：

为什么DDS适合机器人应用：

1. 可靠性：机器人控制需要可靠的消息传递（如运动控制指令），DDS的RELIABLE QoS策略可以保证消息不丢失。
2. 实时性：对于传感器数据（如摄像头、激光雷达），DDS的BEST_EFFORT策略可以提供低延迟传输。
3. QoS灵活：ROS 2通过QoS策略让开发者可以为不同类型的通信（控制、传感器、日志）设置不同的策略，例如：
    1. 控制指令：RELIABLE + KEEP_LAST, depth=1
    2. 传感器数据：BEST_EFFORT + KEEP_LAST, depth=1
    3. 初始状态：TRANSIENT_LOCAL + RELIABLE
示例：

```Python
# 控制指令发布
qos_control = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_LAST,
    depth=1
)
self.control_pub = self.create_publisher(Twist, 'control', qos_control)

# 传感器数据发布
qos_sensor = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=1
)
self.sensor_pub = self.create_publisher(LaserScan, 'sensor', qos_sensor)
```
这样，控制指令会可靠传输，而传感器数据会低延迟传输，两者互不影响。
这种细粒度的控制是ROS 2相比ROS 1的显著优势，也是DDS成为ROS 2核心的原因。

