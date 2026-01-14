from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'fishbot_description'

data_files_urdf = []
for root, dirs, files in os.walk('urdf/fishbot'):
    install_dir = os.path.join('share', package_name, root)
    file_paths = [os.path.join(root, file) for file in files]
    if file_paths:
        data_files_urdf.append((install_dir, file_paths))
        
data_files_world = []
for root, dirs, files in os.walk('world'):
    install_dir = os.path.join('share', package_name, root)
    file_paths = [os.path.join(root, file) for file in files]
    if file_paths:
        data_files_world.append((install_dir, file_paths))

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name+ "/launch", glob('launch/*.launch.py')),
        ('share/' + package_name+ "/rviz_config", glob('rviz_config/*')),
    ]+data_files_urdf +data_files_world,
    
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ros',
    maintainer_email='706376924@qq.com',
    description='TODO: Package description',
    license='Apach-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        ],
    },
)
