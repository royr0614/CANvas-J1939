import can
import logging
from PyQt5.QtCore import QObject, pyqtSignal

class MessageProcessor(QObject):
    """
    Processes CAN messages using DBC definitions and emits signals for UI updates
    """
    # Define signals for UI updates
    message_decoded = pyqtSignal(int, str, dict, str)  # frame_id, name, signals, interface
    unknown_message = pyqtSignal(int, str, str)  # frame_id, data_hex, interface
    
    def __init__(self, can_interface, dbc_parser):
        super().__init__()
        self.can_interface = can_interface
        self.dbc_parser = dbc_parser
        self.logger = logging.getLogger("MessageProcessor")
        
        # Set up callbacks for all receiver interfaces
        for name, config in can_interface.interfaces.items():
            if config['role'] in ['receiver', 'both']:
                can_interface.set_receive_callback(name, self.process_message)
    
    def process_message(self, msg, interface_name):
        """
        Process a received CAN message from a specific interface
        
        Args:
            msg: can.Message object
            interface_name: Name of the interface that received the message
        """
        try:
            # Get frame ID for logging
            frame_id_str = f"0x{msg.arbitration_id:X}"
            self.logger.debug(f"Processing message {frame_id_str} from {interface_name}")
            
            # Try to decode the message using DBC
            decoded_data = self.dbc_parser.decode_message(msg.arbitration_id, msg.data)
            
            if decoded_data:
                # Get message definition for additional info
                message = self.dbc_parser.get_message_by_id(msg.arbitration_id)
                message_name = message.name if message else "Unknown"
                
                # Emit signal with decoded data
                self.message_decoded.emit(
                    msg.arbitration_id,
                    message_name,
                    decoded_data,
                    interface_name
                )
                self.logger.debug(f"Decoded message {frame_id_str}: {message_name}")
            else:
                # Unknown or undecodable message
                data_hex = ' '.join(f'{b:02X}' for b in msg.data)
                self.unknown_message.emit(
                    msg.arbitration_id,
                    data_hex,
                    interface_name
                )
                self.logger.debug(f"Unknown message {frame_id_str}: {data_hex}")
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    def create_and_send_message(self, sender_interface, frame_id, signal_values):
        """
        Create and send a CAN message on the sender interface
        
        Args:
            sender_interface: Name of the sender interface
            frame_id: CAN message frame ID
            signal_values: Dictionary of signal names and values
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            # Encode the message using DBC
            data = self.dbc_parser.encode_message(frame_id, signal_values)
            
            if data:
                # Get message definition
                message = self.dbc_parser.get_message_by_id(frame_id)
                is_extended = True if frame_id > 0x7FF else False
                
                # Create CAN message
                can_msg = can.Message(
                    arbitration_id=frame_id,
                    data=data,
                    is_extended_id=is_extended
                )
                
                # Send on the specified interface
                result = self.can_interface.send(sender_interface, can_msg)
                
                # Log result
                if result:
                    self.logger.info(f"Sent message 0x{frame_id:X} on {sender_interface}")
                else:
                    self.logger.warning(f"Failed to send message 0x{frame_id:X}")
                
                return result
            else:
                self.logger.warning(f"Failed to encode message 0x{frame_id:X}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating/sending message 0x{frame_id:X}: {e}")
            return False