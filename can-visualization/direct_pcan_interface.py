import can
import threading
import time
import logging

class DirectPCANInterface:
    """
    Direct interface to PCAN hardware mimicking the approach in decode_pcan.py
    
    This class provides a simpler, more direct interface to the PCAN hardware
    with fixed channel assignments:
    - PCAN_USBBUS1: Used as sender
    - PCAN_USBBUS2: Used as receiver
    """
    def __init__(self):
        self.running = False
        self.sender_bus = None
        self.receiver_bus = None
        self.receive_callback = None
        self.logger = logging.getLogger("DirectPCANInterface")
        
    def set_receive_callback(self, callback):
        """Set callback for received messages"""
        self.receive_callback = callback
        self.logger.debug("Receive callback set")
        
    def start(self):
        """Start the interface with direct hardware connections"""
        try:
            self.logger.info("Initializing PCAN hardware interfaces")
            
            # Initialize sender on PCAN_USBBUS1
            self.sender_bus = can.interface.Bus(
                interface='pcan', 
                channel='PCAN_USBBUS1', 
                bitrate=500000
            )
            self.logger.info("Sender bus initialized on PCAN_USBBUS1")
            
            # Initialize receiver on PCAN_USBBUS2
            self.receiver_bus = can.interface.Bus(
                interface='pcan', 
                channel='PCAN_USBBUS2', 
                bitrate=500000
            )
            self.logger.info("Receiver bus initialized on PCAN_USBBUS2")
            
            # Test hardware connectivity by sending a message
            test_msg = can.Message(arbitration_id=0x000, data=[0], is_extended_id=False)
            self.sender_bus.send(test_msg)
            self.logger.info("Hardware connectivity verified")
            
            # Start receiver thread
            self.running = True
            self.receive_thread = threading.Thread(
                target=self._receive_thread, 
                daemon=True
            )
            self.receive_thread.start()
            self.logger.info("Receiver thread started")
            
            return True
            
        except Exception as e:
            self.logger.error(f"PCAN hardware error: {e}")
            # Clean up resources on error
            self._cleanup()
            raise RuntimeError(f"Failed to initialize PCAN hardware: {e}")
    
    def _receive_thread(self):
        """Thread function to receive messages"""
        self.logger.info("Receiver thread running")
    
        count = 0
        while self.running and self.receiver_bus:
            try:
                # Wait for a message with timeout
                count += 1
                if count % 10 == 0:
                    self.logger.info(f"DirectPCAN waiting for message (count={count})")
                
                message = self.receiver_bus.recv(1.0)  # 1 second timeout
            
                if message is not None:
                    self.logger.info(f"DirectPCAN received message: ID=0x{message.arbitration_id:X}, data={[hex(b) for b in message.data]}")
                    if self.receive_callback:
                        # Call the callback with the message and interface name
                        self.receive_callback(message, "receiver")
                    else:
                        self.logger.warning("No receive callback set")
                else:
                    self.logger.debug("No message received (timeout)")
            except Exception as e:
                self.logger.error(f"Receiver error: {e}")
                time.sleep(0.1)  # Prevent CPU overload on error
    
        self.logger.info("Receiver thread stopped")
    
    def send(self, message):
        """Send a message on the sender bus"""
        if self.sender_bus and self.running:
            try:
                self.sender_bus.send(message)
                return True
            except Exception as e:
                self.logger.error(f"Sender error: {e}")
        return False
    
    def stop(self):
        """Stop the interface"""
        self.logger.info("Stopping PCAN interface")
        self.running = False
        self._cleanup()
    
    def _cleanup(self):
        """Clean up resources"""
        # Wait for thread to finish
        if hasattr(self, 'receive_thread') and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=2.0)
        
        # Shutdown buses
        if self.sender_bus:
            try:
                self.sender_bus.shutdown()
                self.logger.info("Sender bus shutdown")
            except Exception as e:
                self.logger.error(f"Error shutting down sender bus: {e}")
                
        if self.receiver_bus:
            try:
                self.receiver_bus.shutdown()
                self.logger.info("Receiver bus shutdown")
            except Exception as e:
                self.logger.error(f"Error shutting down receiver bus: {e}")
            
        self.sender_bus = None
        self.receiver_bus = None


class DirectPCANMessageProcessor:
    """
    Message processor for the DirectPCANInterface that connects to the visualization components
    """
    def __init__(self, pcan_interface, dbc_parser):
        self.pcan_interface = pcan_interface
        self.dbc_parser = dbc_parser
        self.callbacks = []
        self.logger = logging.getLogger("DirectPCANMessageProcessor")
        
        # Set the receive callback
        self.pcan_interface.set_receive_callback(self.process_message)
    
    def process_message(self, msg, interface_name):
        """Process a received CAN message"""
        try:
            self.logger.info(f"Processing message ID=0x{msg.arbitration_id:X} from {interface_name}")
        
            # Decode the message using DBC
            decoded_data = self.dbc_parser.decode_message(msg.arbitration_id, msg.data)
        
            if decoded_data:
                # Get message information
                message = self.dbc_parser.get_message_by_id(msg.arbitration_id)
                message_name = message.name if message else f"Unknown_0x{msg.arbitration_id:X}"
            
                self.logger.info(f"Decoded message {message_name} with values {decoded_data}")
            
                # Notify all callbacks
                for callback in self.callbacks:
                    callback(msg.arbitration_id, message_name, decoded_data, interface_name)
            else:
                # Log unknown message
                data_hex = ' '.join(f'{b:02X}' for b in msg.data)
                self.logger.warning(f"Undecodable message: ID=0x{msg.arbitration_id:X}, Data={data_hex}")
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    def send_message(self, frame_id, signal_values):
        """Create and send a CAN message"""
        try:
            data = self.dbc_parser.encode_message(frame_id, signal_values)
            
            if data:
                # Create CAN message
                message = can.Message(
                    arbitration_id=frame_id,
                    data=data,
                    is_extended_id=(frame_id > 0x7FF)
                )
                
                # Send the message
                return self.pcan_interface.send(message)
            else:
                self.logger.warning(f"Could not encode message with ID 0x{frame_id:X}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False
    
    def add_callback(self, callback):
        """Add a callback for decoded messages"""
        self.callbacks.append(callback)
        
    def remove_callback(self, callback):
        """Remove a callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)


