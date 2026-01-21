from setuptools import find_packages, setup

package_name = 'autopatrol_robot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name+"/config", ['config/patrol_config.yaml']),
        ('share/' + package_name+"/utils", ['utils/pose_utils.py']),
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
            "patrol_node = autopatrol_robot.patrol_node:main",
            "patrol_node_optimized = autopatrol_robot.patrol_node:main",
        ],
    },
)
