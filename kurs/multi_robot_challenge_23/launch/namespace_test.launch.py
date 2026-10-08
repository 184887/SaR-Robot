import launch
import launch_ros

def generate_launch_description():
    robot_handler_tb3_0 = launch_ros.actions.Node(
        package='multi_robot_challenge_23',
        executable='robot_handler',
        namespace='tb3_0',
        name='robot_handler'
    )

    robot_handler_tb3_1 = launch_ros.actions.Node(
        package='multi_robot_challenge_23',
        executable='robot_handler',
        namespace='tb3_1',
        name='robot_handler'
    )

    leader = launch_ros.actions.Node(
        package='multi_robot_challenge_23',
        executable='leader',
        name='leader'
    )

    return launch.LaunchDescription([
        robot_handler_tb3_0,
        robot_handler_tb3_1,
        leader,
    ])