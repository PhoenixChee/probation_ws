#!/usr/bin/env python3#!/usr/bin/env python3



from launch import LaunchDescriptionfrom launch import LaunchDescription

from launch_ros.actions import Nodefrom launch_ros.actions import Node

from launch.actions import DeclareLaunchArgument, LogInfofrom launch.actions import DeclareLaunchArgument, LogInfo

from launch.substitutions import LaunchConfigurationfrom launch.substitutions import LaunchConfiguration





def generate_launch_description():def generate_launch_description():

    return LaunchDescription([    return LaunchDescription([

        # Declare launch arguments        # Declare launch arguments

        DeclareLaunchArgument(        DeclareLaunchArgument(

            'log_level',            'log_level',

            default_value='info',            default_value='info',

            description='Log level for the AUV controller'            description='Log level for the AUV controller'

        ),        ),

                

        # Log startup message        # Log startup message

        LogInfo(msg='Starting AUV Gate Navigation System...'),        LogInfo(msg='Starting AUV Gate Navigation System...'),

                

        # Main AUV Controller Node        # Main AUV Controller Node

        Node(        Node(

            package='probation_ws',            package='probation_ws',

            executable='auv_controller',            executable='auv_controller',

            name='auv_controller',            name='auv_controller',

            output='screen',            output='screen',

            parameters=[            parameters=[

                {'use_sim_time': True}                {'use_sim_time': True}

            ],            ],

            arguments=['--ros-args', '--log-level', LaunchConfiguration('log_level')],            arguments=['--ros-args', '--log-level', LaunchConfiguration('log_level')],

            remappings=[            remappings=[

                # Add any topic remappings if needed                # Add any topic remappings if needed

            ]            ]

        ),        ),

                

        # Individual service/client nodes (if you want to run them separately)        # Individual service/client nodes (if you want to run them separately)

        # Uncomment these if you want to test individual components        # Uncomment these if you want to test individual components

                

        # Node(        # Node(

        #     package='probation_ws',        #     package='probation_ws',

        #     executable='subscriber',        #     executable='subscriber',

        #     name='bounding_box_subscriber',        #     name='bounding_box_subscriber',

        #     output='screen'        #     output='screen'

        # ),        # ),

                

        # Node(        # Node(

        #     package='probation_ws',        #     package='probation_ws',

        #     executable='client',        #     executable='client',

        #     name='mavros_client',        #     name='mavros_client',

        #     output='screen'        #     output='screen'

        # ),        # ),

                

        # Node(        # Node(

        #     package='probation_ws',        #     package='probation_ws',

        #     executable='publisher',        #     executable='publisher',

        #     name='velocity_publisher',        #     name='velocity_publisher',

        #     output='screen'        #     output='screen'

        # ),        # ),

    ])    ])