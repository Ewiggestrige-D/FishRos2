from demo_pkg_python.person_node import PersonNode

class WriterNode(PersonNode):
    def __init__(self,name_value:str,age_value:int, book_name:str)->None:
        super().__init__(name_value, age_value) #继承父类的属性
        print('WriterNode __init__方法被调用了')
        self.book = book_name
        
        

def main():
    node = WriterNode('Louis',27,'Ros2 guidance')
    node.eat('chicken tender')
    
