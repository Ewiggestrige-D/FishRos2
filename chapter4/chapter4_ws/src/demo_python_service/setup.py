from setuptools import find_packages, setup
from glob import glob

package_name = 'demo_python_service'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + "/resource", ['resource/default.jpg','resource/Trump.png']),
        ('share/' + package_name+ "/launch", glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ros',
    maintainer_email='706376924@qq.com',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'face_detect_opencv = demo_python_service.learn_face_detect:main',
            'face_detect_yolo = demo_python_service.face_detect_yolo:main',
            'face_detect_node = demo_python_service.face_detect_node:main',
            'face_detect_client_node = demo_python_service.face_detect_client_node:main',
            'face_detect_client_qwen = demo_python_service.face_detect_client_qwen:main',
            'turtle_control_service = demo_python_service.turtle_control_service:main',
            'turtle_patrol_client = demo_python_service.turtle_patrol_client:main',
            'face_detect_param = demo_python_service.face_detect_param:main',
            'face_detect_param_client = demo_python_service.face_detect_param_client:main',
            'face_detect_param_client_qwen = demo_python_service.face_detect_param_client_qwen:main',
            'turtle_control_param = demo_python_service.turtle_control_param:main',
            'turtle_patrol_param_client = demo_python_service.turtle_patrol_param_client:main',
        ],
    },
)
