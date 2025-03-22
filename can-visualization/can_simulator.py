import can
import time
import threading
import random
import logging
from collections import defaultdict

class TrendGenerator:
    """Generates realistic trend-based values for simulation"""
    def __init__(self, min_val, max_val, volatility=0.1):
        self.current = random.uniform(min_val, max_val)
        self.min_val = min_val
        self.max_val = max_val
        self.volatility = volatility
    
    def next_value(self):
        """Generate next value in trend"""
        # Create a realistic trend with random walk
        change = random.normalvariate(0, self.volatility)
        self.current += change
        # Keep within bounds
        self.current = max(self.min_val, min(self.max_val, self.current))
        return self.current

class DualCANSimulator:
    """Simulates sender and receiver CAN buses for testing"""
    def __init__(self, dbc_parser):
        self.dbc = dbc_parser
        self.running = False
        self.sender_callbacks = []
        self.receiver_callbacks = []
        self.logger = logging.getLogger("CANSimulator")
        
        # Get message definitions from DBC
        self.message_ids = dbc_parser.get_all_message_ids()
        if not self.message_ids:
            self.logger.warning("No message definitions found in DBC!")
        
        # Set up signal generators for realistic trends
        self.signal_generators = {}
        self.setup_signal_generators()
        
        # Configure message frequencies (real-world behavior)
        self.message_frequencies = {}
        self.message_last_sent = {}
        self.setup_message_frequencies()
    
    def setup_signal_generators(self):
        """Set up trend generators for each signal"""
        for msg_id in self.message_ids:
            message = self.dbc.get_message_by_id(msg_id)
            if not message:
                continue
                
            for signal in message.signals:
                # Set default min/max if not specified
                min_val = signal.minimum if signal.minimum is not None else 0
                max_val = signal.maximum if signal.maximum is not None else 100
                
                # Adjust min/max for common types
                if 'temp' in signal.name.lower():
                    # Temperature typically 0-100°C
                    min_val = max(min_val, 0)
                    max_val = min(max_val, 100)
                elif 'rpm' in signal.name.lower():
                    # Engine RPM typically 0-8000
                    min_val = max(min_val, 0)
                    max_val = min(max_val, 8000)
                
                # Create trend generator
                volatility = (max_val - min_val) * 0.01  # 1% of range
                key = f"{msg_id}_{signal.name}"
                self.signal_generators[key] = TrendGenerator(min_val, max_val, volatility)
    
    def setup_message_frequencies(self):
        """Set realistic frequencies for different message types"""
        for msg_id in self.message_ids:
            message = self.dbc.get_message_by_id(msg_id)
            if not message:
                continue
            
            # Set frequency based on message name/content (common patterns)
            if 'engine' in message.name.lower():
                # Engine data typically 10-100ms
                self.message_frequencies[msg_id] = 0.01  # 10ms
            elif 'temperature' in message.name.lower():
                # Temperature data typically 500-1000ms
                self.message_frequencies[msg_id] = 0.5  # 500ms
            elif 'status' in message.name.lower():
                # Status messages typically 1000ms
                self.message_frequencies[msg_id] = 1.0  # 1000ms
            else:
                # Default to 100ms for other messages
                self.message_frequencies[msg_id] = 0.1  # 100ms
            
            # Initialize last sent time
            self.message_last_sent[msg_id] = 0
    
    def start(self):
        """Start the simulation"""
        if self.running:
            return
            
        self.running = True
        self.logger.info("Starting CAN simulator")
        
        # Start the simulation thread
        self.simulation_thread = threading.Thread(
            target=self._simulation_loop,
            daemon=True
        )
        self.simulation_thread.start()
    
    def stop(self):
        """Stop the simulation"""
        self.running = False
        self.logger.info("Stopping CAN simulator")
    
    def _simulation_loop(self):
        """Main simulation loop"""
        last_cycle_time = time.time()
        
        while self.running:
            current_time = time.time()
            
            # Process each message that's due to be sent
            for msg_id in self.message_ids:
                # Check if it's time to send this message
                if (current_time - self.message_last_sent.get(msg_id, 0) >= 
                    self.message_frequencies.get(msg_id, 0.1)):
                    
                    # Send the message
                    self._send_simulated_message(msg_id)
                    # Update last sent time
                    self.message_last_sent[msg_id] = current_time
            
            # Sleep to maintain consistent cycle time
            elapsed = time.time() - last_cycle_time
            sleep_time = max(0.001, 0.01 - elapsed)  # Ensure at least 1ms sleep
            time.sleep(sleep_time)
            last_cycle_time = time.time()
    
    def _send_simulated_message(self, msg_id):
        """Create and send a simulated message"""
        # Get message definition
        message = self.dbc.get_message_by_id(msg_id)
        if not message:
            return
        
        # Create a dictionary of signal values
        signal_values = {}
        for signal in message.signals:
            key = f"{msg_id}_{signal.name}"
            if key in self.signal_generators:
                signal_values[signal.name] = self.signal_generators[key].next_value()
            else:
                # Fallback to random value if no generator exists
                min_val = signal.minimum if signal.minimum is not None else 0
                max_val = signal.maximum if signal.maximum is not None else 100
                signal_values[signal.name] = random.uniform(min_val, max_val)
        
        try:
            # Encode the message
            data = self.dbc.encode_message(msg_id, signal_values)
            
            # Create CAN message
            can_msg = can.Message(
                arbitration_id=msg_id,
                data=data,
                is_extended_id=(msg_id > 0x7FF)
            )
            
            # Notify sender callbacks
            for callback in self.sender_callbacks:
                callback(can_msg, "sender")
            
            # Small delay to simulate transmission time
            time.sleep(0.001)
            
            # Notify receiver callbacks
            for callback in self.receiver_callbacks:
                callback(can_msg, "receiver")
            
        except Exception as e:
            self.logger.error(f"Error simulating message 0x{msg_id:X}: {e}")
    
    def add_sender_callback(self, callback):
        """Add callback for sender-side messages"""
        self.sender_callbacks.append(callback)
    
    def add_receiver_callback(self, callback):
        """Add callback for receiver-side messages"""
        self.receiver_callbacks.append(callback)