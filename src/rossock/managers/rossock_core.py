import json
import logging
import threading

# Python 2/3 compatibility import list
try:
    from collections import UserDict
except ImportError:
    from UserDict import UserDict


"""
Author: Alec Gurman
Rework: Roslibpy
"""

class Message(UserDict):
    """Message objects used for publishing and subscribing to/from topics.
    A message is fundamentally a dictionary and behaves as one."""

    def __init__(self, values=None):
        self.data = {}
        if values is not None:
            self.update(values)

class Topic(object):
    """Publish and/or subscribe to a topic in ROS.
    Args:
        ros (:class:`.Ros`): Instance of the ROS connection.
        name (:obj:`str`): Topic name, e.g. ``/cmd_vel``.
        message_type (:obj:`str`): Message type, e.g. ``std_msgs/String``.
        compression (:obj:`str`): Type of compression to use, e.g. `png`. Defaults to `None`.
        throttle_rate (:obj:`int`): Rate (in ms between messages) at which to throttle the topics.
        queue_size (:obj:`int`): Queue size created at bridge side for re-publishing webtopics.
        latch (:obj:`bool`): True to latch the topic when publishing, False otherwise.
        queue_length (:obj:`int`): Queue length at bridge side used when subscribing.
    """

    SUPPORTED_COMPRESSION_TYPES = ('png', 'none')

    def __init__(self, rosbridge, name, message_type, compression=None, latch=False, throttle_rate=0,
                 queue_size=100, queue_length=0):
        self.rosbridge = rosbridge
        self.name = name
        self.message_type = message_type
        self.compression = compression
        self.latch = latch
        self.throttle_rate = throttle_rate
        self.queue_size = queue_size
        self.queue_length = queue_length

        self._subscribe_id = None
        self._advertise_id = None

        if self.compression is None:
            self.compression = 'none'

        if self.compression not in self.SUPPORTED_COMPRESSION_TYPES:
            raise ValueError(
                'Unsupported compression type. Must be one of: ' + str(self.SUPPORTED_COMPRESSION_TYPES))

    @property
    def is_advertised(self):
        """Indicate if the topic is currently advertised or not.
        Returns:
            bool: True if advertised as publisher of this topic, False otherwise.
        """
        return self._advertise_id is not None

    @property
    def is_subscribed(self):
        """Indicate if the topic is currently subscribed or not.
        Returns:
            bool: True if subscribed to this topic, False otherwise.
        """
        return self._subscribe_id is not None

    def subscribe(self, callback):
        """Register a subscription to the topic.
        Every time a message is published for the given topic,
        the callback will be called with the message object.
        Args:
            callback: Function to be called when messages of this topic are published.
        """
        # Avoid duplicate subscription
        if self._subscribe_id:
            return

        self._subscribe_id = 'subscribe:%s:%d' % (
            self.name, self.rosbridge.id_counter)

        self.rosbridge.on(self.name, callback)
        self.rosbridge.send_on_ready(Message({
            'op': 'subscribe',
            'id': self._subscribe_id,
            'type': self.message_type,
            'topic': self.name,
            'compression': self.compression,
            'throttle_rate': self.throttle_rate,
            'queue_length': self.queue_length
        }))

    def unsubscribe(self):
        """Unregister from a subscribed the topic."""
        if not self._subscribe_id:
            return

        self.rosbridge.off(self.name)
        self.rosbridge.send_on_ready(Message({
            'op': 'unsubscribe',
            'id': self._subscribe_id,
            'topic': self.name
        }))
        self._subscribe_id = None

    def publish(self, message):
        """Publish a message to the topic.
        Args:
            message (:class:`.Message`): ROS Bridge Message to publish.
        """
        if not self.is_advertised:
            self.advertise()

        self.rosbridge.send_on_ready(Message({
            'op': 'publish',
            'id': 'publish:%s:%d' % (self.name, self.rosbridge.id_counter),
            'topic': self.name,
            'msg': dict(message),
            'latch': self.latch
        }))

    def advertise(self):
        """Register as a publisher for the topic."""
        if self.is_advertised:
            return

        self._advertise_id = 'advertise:%s:%d' % (
            self.name, self.rosbridge.id_counter)

        self.rosbridge.send_on_ready(Message({
            'op': 'advertise',
            'id': self._advertise_id,
            'type': self.message_type,
            'topic': self.name,
            'latch': self.latch,
            'queue_size': self.queue_size
        }))

        # TODO: Set _advertise_id=None on disconnect (if not reconnecting)

    def unadvertise(self):
        """Unregister as a publisher for the topic."""
        if not self.is_advertised:
            return

        self.rosbridge.send_on_ready(Message({
            'op': 'unadvertise',
            'id': self._advertise_id,
            'topic': self.name,
        }))

        self._advertise_id = None

if __name__ == '__main__':

    from managers.rosbridge_connector import RosBridgeConnector

    ros_client = RosBridgeConnector('127.0.0.1', 9090)

    def subscriber_callback(data):
        print data

    def run_subscriber_example():
        listener = Topic(ros_client, '/velodyne_points', 'sensor_msgs/PointCloud2')
        listener.subscribe(subscriber_callback)

    run_server_example()
    ros_client.run_forever()
