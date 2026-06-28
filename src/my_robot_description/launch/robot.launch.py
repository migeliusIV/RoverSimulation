import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    pkg_share = get_package_share_directory('my_robot_description')
    
    # Пути к файлам
    xacro_file = os.path.join(pkg_share, 'urdf', 'robot.urdf.xacro')
    world_file = os.path.join(pkg_share, 'worlds', 'warehouse.sdf') #'demo.world'
    
    # Обработка Xacro в URDF
    robot_description = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)    
    
    # Robot State Publisher (публикует TF)
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description,
                     'use_sim_time': True,
                     'frame_prefix': ''
                    }],
        output='screen'
    )
    
    # Запуск Gazebo с миром
    # Запуск Gazebo с нужными плагинами
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ]),
        launch_arguments={
            'gz_args': [
                '-r -v 4 ',
                world_file,
                #' -s',  # Запуск в headless-режиме (без GUI, если нужно)
            ],
            'on_exit_shutdown': 'true'
        }.items()
    )
    
    # Спавн робота в Gazebo
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'my_robot',
            '-topic', 'robot_description',
            '-x', '10',
            '-y', '2',
            '-z', '0.5'
        ],
        output='screen'
    )
    
    # Мост между Gazebo и ROS 2 (для сенсоров)
    gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',  # Измените [ на @
            '/camera/image_raw@sensor_msgs/msg/Image@gz.msgs.Image',
            '/imu/data@sensor_msgs/msg/Imu@gz.msgs.IMU',
        ],
        remappings=[
            ('/scan', '/scan'),
        ],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    # Статический трансформер для лидара
    lidar_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'my_robot/base_link/lidar'],
        output='screen'
    )

    return LaunchDescription([
        robot_state_publisher,
        gazebo,
        spawn_robot,
        gz_bridge,
        lidar_tf,
    ])