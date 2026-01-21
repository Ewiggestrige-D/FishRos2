# 文件: autopatrol_robot/utils/pose_utils.py

from geometry_msgs.msg import PoseStamped
from tf_transformations import quaternion_from_euler

def get_pose_stamped(x: float, y: float, yaw: float, frame_id: str = 'map') -> PoseStamped:
    """
    Create a PoseStamped message from x, y, yaw (in radians).
    
    Args:
        x: X position in meters
        y: Y position in meters
        yaw: Yaw angle in radians (around Z-axis)
        frame_id: Coordinate frame (default: 'map')
    
    Returns:
        PoseStamped message ready for Nav2
    """
    pose = PoseStamped()
    pose.header.frame_id = frame_id
    pose.pose.position.x = x
    pose.pose.position.y = y
    
    q = quaternion_from_euler(0.0, 0.0, yaw)
    pose.pose.orientation.x = q[0]
    pose.pose.orientation.y = q[1]
    pose.pose.orientation.z = q[2]
    pose.pose.orientation.w = q[3]
    
    return pose