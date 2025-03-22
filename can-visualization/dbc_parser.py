import cantools
import logging
from collections import defaultdict

class DBCParser:
    """Handles parsing and management of DBC files"""
    def __init__(self, dbc_file_path=None):
        self.db = None
        self.message_by_id = {}
        self.signals_by_message = defaultdict(list)
        self.logger = logging.getLogger("DBCParser")
        
        if dbc_file_path:
            self.load_dbc(dbc_file_path)
    
    def load_dbc(self, dbc_file_path):
        """Load and parse a DBC file"""
        try:
            self.logger.info(f"Loading DBC file: {dbc_file_path}")
            self.db = cantools.database.load_file(dbc_file_path)
            
            # Create lookup tables for faster access
            self.message_by_id = {}
            self.signals_by_message = defaultdict(list)
            
            for message in self.db.messages:
                # Store both standard and extended format of ID for maximum compatibility
                # This helps with inconsistent ID handling in some CAN interfaces
                self.message_by_id[message.frame_id] = message
                
                # Also store signals by message for easy access
                for signal in message.signals:
                    self.signals_by_message[message.frame_id].append(signal)
            
            self.logger.info(f"Loaded {len(self.db.messages)} messages from DBC file")
            return True
        except Exception as e:
            self.logger.error(f"Error loading DBC file: {e}")
            return False
    
    def get_message_by_id(self, frame_id):
        """Get message definition by frame ID"""
        # Try direct lookup
        if frame_id in self.message_by_id:
            return self.message_by_id[frame_id]
        
        # Try alternative formats if direct lookup fails
        # This handles differences in how some CAN interfaces represent extended IDs
        alternative_ids = [
            frame_id & 0x1FFFFFFF,  # 29-bit ID mask for J1939
            frame_id & 0x0FFFFFFF,  # Check without the first nibble
            frame_id & 0x00FFFFFF,  # Check without the first byte
        ]
        
        for alt_id in alternative_ids:
            if alt_id in self.message_by_id:
                return self.message_by_id[alt_id]
        
        return None
    
    def get_signals_for_message(self, frame_id):
        """Get all signals for a specific message ID"""
        message = self.get_message_by_id(frame_id)
        if message:
            return message.signals
        return []
    
    def get_all_message_ids(self):
        """Get list of all message IDs"""
        return list(self.message_by_id.keys())
    
    def decode_message(self, frame_id, data):
        """Decode message data using the DBC definitions"""
        message = self.get_message_by_id(frame_id)
        if message:
            try:
                return self.db.decode_message(frame_id, data)
            except Exception as e:
                self.logger.error(f"Error decoding message ID 0x{frame_id:X}: {e}")
        return None
    
    def encode_message(self, frame_id, data_dict):
        """Encode message data using the DBC definitions"""
        message = self.get_message_by_id(frame_id)
        if message:
            try:
                return self.db.encode_message(frame_id, data_dict)
            except Exception as e:
                self.logger.error(f"Error encoding message ID 0x{frame_id:X}: {e}")
        return None