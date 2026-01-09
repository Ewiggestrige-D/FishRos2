import threading #pyhton中用于多线程调用的库
import requests

class Download:
    def download(self,url,callback_word_count):
        print(f'线程：{threading.get_ident()},开始下载：{url}')
        response = requests.get(url)
        response.encoding = 'utf-8'
        callback_word_count(url,response.text) #调用回调函数
    
    def start_download(self,url,callback_word_count):
         # self.download(url,callback_word_count) 
         # 此处直接使用下载函数，就变成了单线程调用
         thread = threading.Thread(target=self.download,args=(url,callback_word_count)) #导入的 threading 模块中的 Thread 类的实例化
         thread.start() # thread 是 threading.Thread 类创建的一个对象（实例），而 start() 是这个类自带的方法，

    
def Word_Count(url,result):
    """
    word_count 的 Docstring
    普通函数，用于回调
     
    :param url: 说明
    :param result: 说明
    """
    print(f"{url}:{len(result)}->{result[:8]}")
    
def main():
    download = Download()
    download.start_download('http://127.0.0.1:8000/episode1.txt',Word_Count) # 函数可以作为参数传递！
                                           # 在 Python 中，函数名就是指向函数对象的变量，可以像整数、字符串一样被赋值、传参、返回。
    download.start_download('http://127.0.0.1:8000/episode2.txt',Word_Count) # ← Word_Count 是函数对象 Word_Count 被当作普通参数传递给 start_download，最终在下载完成后被调用：
                                           # → 把 Word_Count 这个函数对象的引用（不是调用结果！）传给 start_download 的第二个参数 callback_word_count。
    download.start_download('http://127.0.0.1:8000/episode3.txt',Word_Count) # callback_word_count(url, response.text)  # ← 实际调用 Word_Count(url, text)
    
    # 在terminal中使用pyhton3 -m http.server的指令
"""
为什么回调函数这个设计很强大？
1. 解耦（Decoupling）
Download 类不需要知道回调函数具体做什么
可以传入 Word_Count、SaveToFile、PrintLength 等任意函数
2. 灵活性
Python
编辑
# 不同用途，同一 Download 类
download.start_download(url, Word_Count)      # 统计字数
download.start_download(url, Save_To_File)    # 保存文件
download.start_download(url, Analyze_Content) # 分析内容
3. 符合“好莱坞原则”
“Don't call us, we'll call you.”

（别调用我们，我们会调用你）

Download 控制下载流程，但在适当时机回调你提供的函数。

"""

"""
在ros2框架下运行这个文件需要那些步骤
1. 将py文件以面向对象的方式编写，留下main函数调用
2. 将py文件导入到setup.py 中，声明可执行脚本的映射，做好main函数的映射
3. 在环境中colcon build，在pkg中编译包的内容
4. 使用source install/setup.bash命令 修改环境变量
4. 使用ros2 run demo_pkg_python(pkg名称) （中间需要空格） learn_thread(映射之后的可执行名)来运行py文件中的main函数
"""