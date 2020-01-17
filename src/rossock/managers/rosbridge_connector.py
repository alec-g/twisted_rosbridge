import logging
import threading

from rossock.managers.rossock_core import Message
from rossock.comms.websocket_comms import WebSocketClientFactory as RosBridgeClientFactory
from rossock import misc

class RosBridgeConnector(object):
    """Connection manager to RosBridge server."""

    def __init__(self, host, port=None, is_secure=False):
        self._id_counter = 0
        url = RosBridgeClientFactory.create_url(host, port, is_secure)
        self.factory = RosBridgeClientFactory(url)
        self.is_connecting = False
        self.connect()

    @property
    def id_counter(self):
        """Generate an auto-incremental ID starting from 1.
        Returns:
            int: An auto-incremented ID.
        """
        self._id_counter += 1
        return self._id_counter

    @property
    def is_connected(self):
        """Indicate if the ROS connection is open or not.
        Returns:
            bool: True if connected to ROS, False otherwise.
        """
        return self.factory.is_connected

    def connect(self):
        """Connect to ROS master."""
        misc.formatted_print('RosBridgeConnector\t|\tStarting connection to ros master.')
        # Don't try to reconnect if already connected.
        if self.is_connected or self.is_connecting:
            return

        self.is_connecting = True

        def _unset_connecting_flag(*args):
            self.is_connecting = False

        self.factory.on_ready(_unset_connecting_flag)
        self.factory.connect()

    def close(self):
        """Disconnect from ROS master."""
        if self.is_connected:
            def _wrapper_callback(proto):
                proto.send_close()
                return proto

            self.factory.on_ready(_wrapper_callback)

    def run(self, timeout=None):
        """Kick-starts a non-blocking event loop.
        Args:
            timeout: Timeout to wait until connection is ready.
        """
        self.factory.manager.run()

        wait_connect = threading.Event()
        self.factory.on_ready(lambda _: wait_connect.set())

        if not wait_connect.wait(timeout):
            raise Exception('Failed to connect to ROS')

    def run_forever(self):
        """Kick-starts a blocking loop to wait for events.
        Depending on the implementations, and the client applications,
        running this might be required or not.
        """
        self.factory.manager.run_forever()

    def run_event_loop(self):
        self.run_forever()

    def call_in_thread(self, callback):
        """Call the given function in a thread.
        The threading implementation is deferred to the factory.
        Args:
            callback (:obj:`callable`): Callable function to be invoked.
        """
        self.factory.manager.call_in_thread(callback)

    def call_later(self, delay, callback):
        """Call the given function after a certain period of time has passed.
        Args:
            delay (:obj:`int`): Number of seconds to wait before invoking the callback.
            callback (:obj:`callable`): Callable function to be invoked when ROS connection is ready.
        """
        self.factory.manager.call_later(delay, callback)

    def terminate(self):
        """Signals the termination of the main event loop."""
        if self.is_connected:
            self.close()

        self.factory.manager.terminate()

    def on(self, event_name, callback):
        """Add a callback to an arbitrary named event.
        Args:
            event_name (:obj:`str`): Name of the event to which to subscribe.
            callback: Callable function to be executed when the event is triggered.
        """
        self.factory.on(event_name, callback)

    def off(self, event_name, callback=None):
        """Remove a callback from an arbitrary named event.
        Args:
            event_name (:obj:`str`): Name of the event from which to unsubscribe.
            callback: Callable function. If ``None``, all callbacks of the event
                will be removed.
        """
        if callback:
            self.factory.off(event_name, callback)
        else:
            self.factory.remove_all_listeners(event_name)

    def emit(self, event_name, *args):
        """Trigger a named event."""
        self.factory.emit(event_name, *args)

    def on_ready(self, callback, run_in_thread=True):
        """Add a callback to be executed when the connection is established.
        If a connection to ROS is already available, the callback is executed immediately.
        Args:
            callback: Callable function to be invoked when ROS connection is ready.
            run_in_thread (:obj:`bool`): True to run the callback in a separate thread, False otherwise.
        """
        def _wrapper_callback(proto):
            if run_in_thread:
                self.factory.manager.call_in_thread(callback)
            else:
                callback()

            return proto

        self.factory.on_ready(_wrapper_callback)

    def send_on_ready(self, message):
        """Send message to the ROS Master once the connection is established.
        If a connection to ROS is already available, the message is sent immediately.
        Args:
            message (:class:`.Message`): ROS Bridge Message to send.
        """
        def _send_internal(proto):
            proto.send_ros_message(message)
            return proto

        self.factory.on_ready(_send_internal)
