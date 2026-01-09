from setuptools import find_packages, setup

package_name = 'status_display'

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
    maintainer_email='ros@todo.todo',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'hello_qt = status_display.hello_Qt:main',
            'sys_status_display = status_display.sys_status_display:main',
            'sys_status_display_revised = status_display.sys_status_display_revised:main',
        ],
    },
)
