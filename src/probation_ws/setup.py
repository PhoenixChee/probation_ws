from setuptools import setup
import os
from glob import glob

package_name = 'probation_ws'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), 
         glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='auv_developer',
    maintainer_email='developer@example.com',
    description='AUV Gate Navigation Package for Probation Task',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'auv_controller = probation_ws.auv_controller:main',
            'subscriber = probation_ws.subscriber:main',
            'publisher = probation_ws.publisher:main',
            'client = probation_ws.client:main',
            'service = probation_ws.service:main',
            'system_tester = probation_ws.system_tester:main',
        ],
    },
)