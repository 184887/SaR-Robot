"""
This node locates Aruco AR markers in images and publishes their ids and poses.

Subscriptions:
   /camera/image_raw (sensor_msgs.msg.Image)
   /camera/camera_info (sensor_msgs.msg.CameraInfo)
   /camera/camera_info (sensor_msgs.msg.CameraInfo)

Published Topics:
    /aruco_poses (geometry_msgs.msg.PoseArray)
       Pose of all detected markers (suitable for rviz visualization)

    /aruco_markers (ros2_aruco_interfaces.msg.ArucoMarkers)
       Provides an array of all poses along with the corresponding
       marker ids.

Parameters:
    marker_size - size of the markers in meters (default .0625)
    aruco_dictionary_id - dictionary that was used to generate markers
                          (default DICT_5X5_250)
    image_topic - image topic to subscribe to (default /camera/image_raw)
    camera_info_topic - camera info topic to subscribe to
                         (default /camera/camera_info)

Author: Nathan Sprague
Version: 10/26/2020

"""

import rclpy
import rclpy.node
from rclpy.qos import qos_profile_sensor_data
from cv_bridge import CvBridge
import numpy as np
import cv2
from ros2_aruco import transformations

from sensor_msgs.msg import CameraInfo
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseArray, Pose
from ros2_aruco_interfaces.msg import ArucoMarkers


class ArucoNode(rclpy.node.Node):

    def __init__(self):
        super().__init__('aruco_node')

        # Declare and read parameters
        self.declare_parameter("marker_size", 0.05)
        self.declare_parameter("aruco_dictionary_id", "DICT_5X5_250")
        self.declare_parameter("image_topic", "/camera/color/image_raw")
        self.declare_parameter("camera_info_topic", "/camera/color/camera_info")
        self.declare_parameter("camera_frame", None)

        self.marker_size = self.get_parameter("marker_size").get_parameter_value().double_value
        dictionary_id_name = self.get_parameter(
            "aruco_dictionary_id").get_parameter_value().string_value
        image_topic = self.get_parameter("image_topic").get_parameter_value().string_value
        info_topic = self.get_parameter("camera_info_topic").get_parameter_value().string_value
        self.camera_frame = self.get_parameter("camera_frame").get_parameter_value().string_value

        # Make sure we have a valid dictionary id:
        try:
            dictionary_id = cv2.aruco.__getattribute__(dictionary_id_name)
            if type(dictionary_id) != type(cv2.aruco.DICT_5X5_100):
                raise AttributeError
        except AttributeError:
            self.get_logger().error("bad aruco_dictionary_id: {}".format(dictionary_id_name))
            options = "\n".join([s for s in dir(cv2.aruco) if s.startswith("DICT")])
            self.get_logger().error("valid options: {}".format(options))

        # Set up subscriptions
        self.info_sub = self.create_subscription(CameraInfo,
                                                 info_topic,
                                                 self.info_callback,
                                                 qos_profile_sensor_data)

        self.create_subscription(Image, image_topic,
                                 self.image_callback, qos_profile_sensor_data)

        # Set up publishers
        self.poses_pub = self.create_publisher(PoseArray, 'aruco_poses', 10)
        self.markers_pub = self.create_publisher(ArucoMarkers, 'aruco_markers', 10)

        # Set up fields for camera parameters
        self.info_msg = None
        self.intrinsic_mat = None
        self.distortion = None

        # self.aruco_dictionary = cv2.aruco.Dictionary_get(dictionary_id)
        self.aruco_dictionary = cv2.aruco.getPredefinedDictionary(dictionary_id)
        # self.aruco_parameters = cv2.aruco.DetectorParameters_create()
        self.aruco_parameters = cv2.aruco.DetectorParameters()
        self.bridge = CvBridge()
        self.aruco_detector = cv2.aruco.ArucoDetector(self.aruco_dictionary, self.aruco_parameters)

    def my_estimatePoseSingleMarkers(self, corners, marker_size, mtx, distortion):
        '''
        This will estimate the rvec and tvec for each of the marker corners detected by:
        corners, ids, rejectedImgPoints = detector.detectMarkers(image)
        corners - is an array of detected corners for each detected marker in the image
        marker_size - is the size of the detected markers
        mtx - is the camera matrix
        distortion - is the camera distortion matrix
        RETURN list of rvecs, tvecs, and trash (so that it corresponds to the old estimatePoseSingleMarkers())
        '''
        marker_points = np.array([[-marker_size / 2, marker_size / 2, 0],
                                [marker_size / 2, marker_size / 2, 0],
                                [marker_size / 2, -marker_size / 2, 0],
                                [-marker_size / 2, -marker_size / 2, 0]], dtype=np.float32)
        trash = []
        rvecs = []
        tvecs = []
        
        for c in corners:
            nada, R, t = cv2.solvePnP(marker_points, c, mtx, distortion, False, cv2.SOLVEPNP_IPPE_SQUARE)
            rvecs.append(R)
            tvecs.append(t)
            trash.append(nada)
        return rvecs, tvecs, trash

    def info_callback(self, info_msg):
        self.info_msg = info_msg
        self.intrinsic_mat = np.reshape(np.array(self.info_msg.k), (3, 3))
        self.distortion = np.array(self.info_msg.d)
        # Assume that camera parameters will remain the same...
        self.destroy_subscription(self.info_sub)

    def image_callback(self, img_msg):

        if self.info_msg is None:
            self.get_logger().warn("No camera info has been received!")
            return

        cv_image = self.bridge.imgmsg_to_cv2(img_msg)
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)

        h, w = cv_image.shape[:2]
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(self.intrinsic_mat, self.distortion, (w, h), 1, (w, h))

        dst = cv2.undistort(cv_image, self.intrinsic_mat, self.distortion, None, newcameramtx)
        # crop the image
        x, y, w, h = roi
        dst = dst[y:y + h, x:x + w]


        cv2.imshow('raw',cv_image)
        # cv2.imshow('undistort', dst)
        
        markerCorners, markerIds, rejectedCandidates = self.aruco_detector.detectMarkers(dst)
        if not markerIds is None:

            rvecs, tvecs, trash = self.my_estimatePoseSingleMarkers(markerCorners, 5.3, newcameramtx, self.distortion)
            #cv::drawFrameAxes(outputImage, cameraMatrix, distCoeffs, rvec, tvec, 0.1);
            for idx in range(len(markerIds)):

                cv2.drawFrameAxes(dst,self.intrinsic_mat,self.distortion,rvecs[idx],tvecs[idx],5)
                print('marker id:%d, pos_x = %f,pos_y = %f, pos_z = %f' % (markerIds[idx],tvecs[idx][0],tvecs[idx][1],tvecs[idx][2]))

        cv2.aruco.drawDetectedMarkers(dst, markerCorners, markerIds)
        # print(markerIds)
        cv2.imshow('detect', dst)
        cv2.waitKey(1)
        


def main():
    rclpy.init()
    node = ArucoNode()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()