"""
Fish Bot2 7.5.3 添加语音播报功能
核心需求：1. 根据定义的消息接口srv/SpeechText.srv 获取需要朗读的文本
2. 在朗读完成后返回一个bool值表示朗读是否成功完成
3. 当前是同步阻塞（wait()），明确说明“服务调用会阻塞直到播报完成”
4. result=False 表示“播放失败或中断”，而非“未播放”
"""
import rclpy
from rclpy.node import Node

from autopatrol_interfaces.srv import SpeechText
import espeakng

class Speaker(Node):
    def __init__(self, node_name='speaker'):
        super().__init__(node_name)
        self.get_logger().info(f'{node_name}手枪腿,启动')
        self.speech_service_ = self.create_service(SpeechText,'speech_text',self.speech_text_callback)
        self.speaker_ = espeakng.Speaker()
        self.speaker_.voice="zh"
        
        

    def speech_text_callback(self,request,response):
        try:
            self.get_logger().info(f'朗读文本: "{request.text}"')
            self.speaker_.say(request.text)
            self.speaker_.wait()
            response.result = True
            self.get_logger().info('朗读完成')
        except Exception as e:
            self.get_logger().error(f'语音播报失败: {e}')
            response.result = False
        return response
    

def main():
    rclpy.init()
    node = Speaker()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
    
if __name__ == '__main__':
    main()