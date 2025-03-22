import can
import threading
import time
import logging

class CANInterface:
    """Handles communication with multiple CAN hardware interfaces"""
    def __init__(self):
        self.interfaces = {}  # Dictionary to store multiple interfaces
        self.running = False
        self.receive_threads = {}
        self.logger = logging.getLogger("CANInterface")
        
    def add_interface(self, name, interface_type='pcan', channel='PCAN_USBBUS1', 
                     bitrate=500000, role='both'):
        """Add a CAN interface with a specific role (sender/receiver/both)"""
        self.interfaces[name] = {
            'type': interface_type,
            'channel': channel,
            'bitrate': bitrate,
            'role': role,  # 'sender', 'receiver', or 'both'
            'bus': None,   # Will be initialized when started
            'receive_callback': None
        }
        self.logger.info(f"Added interface {name} on {channel} with role {role}")
    
    def set_receive_callback(self, interface_name, callback):
        """Set callback function for received messages on specific interface"""
        if interface_name in self.interfaces:
            self.interfaces[interface_name]['receive_callback'] = callback
            self.logger.debug(f"Set receive callback for {interface_name}")
    
    def start(self):
        """Initialize and start all interfaces"""
        self.running = True
        for name, config in self.interfaces.items():
            try:
                # Initialize the CAN bus interface
                bus = can.interface.Bus(
                    interface=config['type'],
                    channel=config['channel'],
                    bitrate=config['bitrate']
                )
                self.interfaces[name]['bus'] = bus
                self.logger.info(f"Interface {name} initialized on {config['channel']}")
                
                # Start receiver thread if this interface is a receiver or both
                if config['role'] in ['receiver', 'both']:
                    thread = threading.Thread(
                        target=self._receive_thread,
                        args=(name,),
                        daemon=True
                    )
                    thread.start()
                    self.receive_threads[name] = thread
                    self.logger.info(f"Started receive thread for {name}")
                    
            except Exception as e:
                self.logger.error(f"Error initializing interface {name}: {e}")
    
    def _receive_thread(self, interface_name):
        """Thread function to receive messages from a specific interface"""
        config = self.interfaces[interface_name]
        bus = config['bus']
        callback = config['receive_callback']
        
        while self.running and bus is not None:
            try:
                # Wait for a message with timeout
                message = bus.recv(1.0)
                if message is not None and callback is not None:
                    # Call the callback with the message and interface name
                    callback(message, interface_name)
            except Exception as e:
                self.logger.error(f"Error receiving from {interface_name}: {e}")
                time.sleep(0.1)  # Prevent CPU overload on error
    
    def send(self, interface_name, message):
        """Send a message on a specific interface"""
        if (interface_name in self.interfaces and 
            self.interfaces[interface_name]['bus'] is not None and
            self.interfaces[interface_name]['role'] in ['sender', 'both']):
            try:
                self.interfaces[interface_name]['bus'].send(message)
                return True
            except Exception as e:
                self.logger.error(f"Error sending on {interface_name}: {e}")
        return False
    
    def stop(self):
        """Stop all interfaces"""
        self.running = False
        # Wait for threads to finish
        for name, thread in self.receive_threads.items():
            thread.join(timeout=2.0)
        # Shutdown bus interfaces
        for name, config in self.interfaces.items():
            if config['bus'] is not None:
                config['bus'].shutdown()
        self.logger.info("All CAN interfaces stopped")