# Fishbot实战教学OS安装及环境依赖配置
## Chapter 1 
1. 下载安装 **Ubuntu 22.04.5 LTS (Jammy Jellyfish)**
> [Ubuntu 22.04.5 LTS (Jammy Jellyfish)](https://releases.ubuntu.com/jammy/)
> [Ubuntu 22.04.5 LTS-Desktop image-ISO](https://releases.ubuntu.com/jammy/ubuntu-22.04.5-desktop-amd64.iso)
> [Kubuntu 22.04 LTS Released](https://cdimage.ubuntu.com/kubuntu/releases/22.04/release/)
> [Kubuntu-22.04.5-desktop-amd64.iso](https://cdimage.ubuntu.com/kubuntu/releases/22.04/release/kubuntu-22.04.5-desktop-amd64.iso)


2. 使用FishRos 一键安装指令换源并安装**ROS**
```zsh
wget http://fishros.com/install -O fishros && . fishros
```
其中换源时选择仅更换国内源，推荐使用中科大(USTC)源镜像。
选择对应Ubuntu22.04版本的**ROS2-humble 完整桌面版本**。
下载完成后
```zsh
source ~/.zshrc
ros2
rviz2
```
测试是否能够正常打开ros2 和 rviz2


3. 使用apt命令更新软件包
```zsh
sudo apt update && sudo apt upgrade -y
```
```zsh
whereis python3  
```
确认环境变量指向正确的python位置

4. 使用deb安装包下载VS code插件
访问[VS codex下载](https://code.visualstudio.com/Download)网页,将deb安装包下载到本地文件夹，并进入文件夹，使用**dpkg**命令安装
```zsh
cd /home/$usr/vscode
sudo dpkg -i code_1.110.0-1772587980_amd64.deb
```
5. 在VS code中添加插件
根据之后课程需要，需要安装以下插件
    1.语言与皮肤类 (3)
       - Chinese (Simplified) (简体中文) Language Pack for Visual Studio Code
       - One Dark Pro
       - Vscode Great Icons
    2. Python类 (7)
       - python
       - pylance
       - python debugger
       - python Enviroments
       - python Indent
       - code Runner
       - autoDocstring   
    3. git类 (1)
       - Git Graph 
    4. Markdown & PDF (4)
       - Markdown Preview Enhanced
       - Markdown All in One
       - Markdown PDF 
       - vscode-pdf
    5. C++/CMake (3)
       - C/C++
       - C/C++ DevTools
       - CMake Tools  
    6. Arduino (2)
       - PlatformIO IDE
       - Serial Monitor
    7. Robot Model (2)   
       - URDF
       - Robot Developer Extensions for URDF
    8. XML (3)
       - XML
       - XML Tools
       - Pretty XML   
    9. Container (2)
       - Container Tools
       - Dev Containers 

## Chapter 2
1. 多功能包的最佳实践WorkSpace
在文件夹下创建workspace文件夹，并使用ros2 创建功能包
```zsh
mkdir -p ChapterX/chapN_ws/src
cd ~/{$FILE_NAME}/ChapterX/chapN_ws/src
ros2 pkg crate {$PKG_NAME} \\
--build-type ament_python \\
--dependencies rclpy \\
--license Apache-2.0 \\
--description "DESCRIPTION"
```
在编译时，一定要在chapN_ws文件下编译
```zsh
cd ~/{$FILE_NAME}/ChapterX/chapN_ws
colcon build   # 编译
source install/setup.zsh  # 激活环境变量
```

2. git文件保存
在 ~/{$FILE_NAME} 下创建.gitignore文件，忽略编译文件夹来保证每次上传的仅为工作文件
```text
# .gitignore
build/
install/
log/
```

## Chapter3