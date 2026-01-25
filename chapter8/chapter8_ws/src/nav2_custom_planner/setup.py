from setuptools import find_packages, setup

package_name = 'nav2_custom_planner'

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
        'console_scripts': [
        ],
        'nav2_core.global_planner': [
        'nav2_custom_planner = nav2_custom_planner.nav2_custom_planner:nav2_custom_planner',
    ],
    },
)
