from setuptools import find_packages, setup

package_name = 'motion_control_system'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
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
         'motion_control_system.MotionController': [
        'spin_controller = motion_control_system.spin_motion_controller:SpinMotionController',
    ], # pluginlib 的 entry point group 名必须是基类的完整标识符：motion_control_system.MotionController
        'console_scripts': [
            'test_plugin = motion_control_system.test_plugin:main',
        ],
    },
)
