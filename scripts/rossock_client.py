#!/usr/bin/env python

import rospy

from twisted.internet import reactor

from sensor_msgs.msg import PointCloud2
from tf2_msgs.msg import TFMessage

from rossock.managers.rossock_core import Message, Topic
from rossock.managers.rosbridge_connector import RosBridgeConnector
from rospy_message_converter import message_converter

class Main():
    def __init__(self):

        host = "127.0.0.1"
        port = 9090

        self._twisted_rate = 1 / float(20) #20hz
        self._ros_client = RosBridgeConnector(host, port)
        self._velodyne_pub = rospy.Publisher('/velodyne_points', PointCloud2, queue_size=100)
        self._tf_pub = rospy.Publisher('/tf', TFMessage, queue_size=10)

        self.init_ros_node()

    def velodyne_cb(self, data):
        result = message_converter.convert_dictionary_to_ros_message('sensor_msgs/PointCloud2', data)
        self._velodyne_pub.publish(result)

    def tf_cb(self, data):
        result = message_converter.convert_dictionary_to_ros_message('tf2_msgs/TFMessage', data)
        self._tf_pub.publish(result)

    def run_subscriber_example(self):
        velodyne_sub = Topic(self._ros_client, '/velodyne_points', 'sensor_msgs/PointCloud2')
        velodyne_sub.subscribe(self.velodyne_cb)

        tf_sub = Topic(self._ros_client, '/tf', 'tf2_msgs/TFMessage')
        tf_sub.subscribe(self.tf_cb)

    def init_ros_node(self):
        rospy.init_node("velodyne_points_republisher", anonymous=True);

if __name__ == "__main__":

    app = Main()
    app.run_subscriber_example()

    rospy.on_shutdown(app._ros_client.terminate)

    try:
        app._ros_client.run_forever()
    except:
        pass

    app._ros_client.terminate()
