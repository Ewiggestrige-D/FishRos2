from setuptools import find_packages, setup

package_name = 'demo_pkg_python'

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
            'python_node = demo_pkg_python.python_node:main',
            'person_node = demo_pkg_python.person_node:main',
            'writer_node = demo_pkg_python.writer_node:main',
            'learn_thread = demo_pkg_python.learn_thread:main',
        ],
    },
)
