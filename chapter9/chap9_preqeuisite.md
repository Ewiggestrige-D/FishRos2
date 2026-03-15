#  Fishbot 安装过程
## 安装虚拟环境
`bash
sudo apt install python3-venv`

## 安装Arduino开发平台
vascode中安装platformio ide

文件安装在/home/isaac/.platformio 文件夹下
/home/isaac/.platformio/penv就是vscode中的环境

cd到/home/isaac/.platformio/penv之后 使用
`zsh
. bin/activate
`
来激活虚拟环境

在虚拟环境中安装 pip install platformio

完成之后在chaptter9 中创建一个文件夹
cd进入文件夹之后使用pio project init 命令初始化，注意此时应该在虚拟环境中