import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def launch_setup(context):
    # Her er world en vanlig streng, f.eks. '3'
    world = LaunchConfiguration('world').perform(context)

    #   - mappa: get_package_share_directory('multi_robot_challenge_23') + 'launch'
    #   - bruk os.path.join, og f-streng for filnavnet
    pakke_mappe = get_package_share_directory('multi_robot_challenge_23')
    filnavn = f'rescue_robots_w{world}.launch.py'
    launch_fil = os.path.join(pakke_mappe, 'launch', filnavn)


    verden = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(launch_fil)
    )

    return [verden]

    


def generate_launch_description():
    return LaunchDescription([
        # DeclareLaunchArgument for 'world', default_value='1'
        DeclareLaunchArgument('world', default_value='1'),
        OpaqueFunction(function=launch_setup),
       
    ])