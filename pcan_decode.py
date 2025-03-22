import can
import time
import threading
import struct
import random

# Define signal formats from the provided DBC-like definitions
class MessageDefinition:
    def __init__(self, id, name, length):
        self.id = id
        self.name = name
        self.length = length
        self.signals = []

class SignalDefinition:
    def __init__(self, name, start_bit, length, byte_order, value_type, factor, offset, min_val, max_val, unit):
        self.name = name
        self.start_bit = start_bit
        self.length = length
        self.byte_order = byte_order  # 1: little endian (Intel), 0: big endian (Motorola)
        self.value_type = value_type  # '+': unsigned, '-': signed
        self.factor = factor
        self.offset = offset
        self.min_val = min_val
        self.max_val = max_val
        self.unit = unit

def sender(exit_event):
    """Function to send test messages on PCAN_USBBUS1"""
    try:
        # Initialize the sender bus
        sender_bus = can.interface.Bus(bustype='pcan', channel='PCAN_USBBUS1', bitrate=500000)
        print("Sender initialized on PCAN_USBBUS1")
        
        # Create message definitions from the provided specifications
        messages = create_message_definitions()
        
        while not exit_event.is_set():
            # Send all defined messages
            for msg_def in messages:
                # Create random values for each signal
                signal_values = {}
                for signal in msg_def.signals:
                    # Generate a random value within the specified range
                    raw_value = random.uniform(signal.min_val, signal.max_val)
                    # Scale to actual value
                    signal_values[signal.name] = raw_value
                
                # Pack the signals into a CAN message
                data = create_message_data(msg_def, signal_values)
                
                # Create and send the message
                message = can.Message(
                    arbitration_id=msg_def.id,
                    data=data,
                    is_extended_id=True  # Using extended IDs for J1939
                )
                
                sender_bus.send(message)
                print(f"Sent message: ID=0x{msg_def.id:X}, Name={msg_def.name}")
                print(f"  Values: {signal_values}")
                
                # Wait a bit before the next message
                time.sleep(0.5)
            
            # Wait between cycles
            time.sleep(1)
            
    except Exception as e:
        print(f"Sender error: {e}")
    finally:
        if 'sender_bus' in locals():
            sender_bus.shutdown()
            print("Sender shutdown")

def receiver(exit_event):
    """Function to receive and decode messages on PCAN_USBBUS2"""
    try:
        # Initialize the receiver bus
        receiver_bus = can.interface.Bus(bustype='pcan', channel='PCAN_USBBUS2', bitrate=500000)
        print("Receiver initialized on PCAN_USBBUS2")
        
        # Create message definitions
        messages = create_message_definitions()
        message_dict = {msg.id: msg for msg in messages}
        
        while not exit_event.is_set():
            # Wait for a message (with timeout)
            message = receiver_bus.recv(1.0)  # 1 second timeout
            
            if message is not None:
                # Decode the message
                decode_message(message, message_dict)
            
    except Exception as e:
        print(f"Receiver error: {e}")
    finally:
        if 'receiver_bus' in locals():
            receiver_bus.shutdown()
            print("Receiver shutdown")

def create_message_definitions():
    """Create message and signal definitions from the provided specifications"""
    messages = []
    
    
    
    # AccelerationSensor
    msg2 = MessageDefinition(0x88FF88FE, "AccelerationSensor", 7)
    msg2.signals.append(SignalDefinition("SpprtVrblTrnsRpttnRtFrAcclrtnSns", 54, 2, 1, '+', 1, 0, 0, 3, ""))
    msg2.signals.append(SignalDefinition("VrtclAcclrtnExRngeFigureOfMerit", 52, 2, 1, '+', 1, 0, 0, 3, ""))
    msg2.signals.append(SignalDefinition("LngtdnlAcclrtnExRngFgureOfMerit", 50, 2, 1, '+', 1, 0, 0, 3, ""))
    msg2.signals.append(SignalDefinition("LtrlAcclrtnExRangeFigureOfMerit", 48, 2, 1, '+', 1, 0, 0, 3, ""))
    msg2.signals.append(SignalDefinition("VerticalAccelerationExRange", 32, 16, 1, '+', 0.01, -320, -320, 322.55, "m/s/s"))
    msg2.signals.append(SignalDefinition("LateralAccelerationExRange", 0, 16, 1, '+', 0.01, -320, -320, 322.55, "m/s/s"))
    msg2.signals.append(SignalDefinition("LongitudinalAccelerationExRange", 16, 16, 1, '+', 0.01, -320, -320, 322.55, "m/s/s"))
    messages.append(msg2)
    
    
    return messages

def encode_signal(signal, value, data_array):
    """Encode a signal value into the data bytes"""
    # Convert the physical value to raw value
    raw_value = int((value - signal.offset) / signal.factor)
    
    # Get starting byte and bit
    start_byte = signal.start_bit // 8
    start_bit = signal.start_bit % 8
    
    # For multi-byte signals using little endian (Intel) byte order
    if signal.byte_order == 1:  # Little endian
        byte_pos = start_byte
        bits_remaining = signal.length
        bit_pos = start_bit
        
        while bits_remaining > 0:
            # Ensure we don't exceed the array length
            if byte_pos >= len(data_array):
                break
                
            # How many bits to set in this byte
            bits_in_this_byte = min(8 - bit_pos, bits_remaining)
            
            # Create mask for these bits
            mask = ((1 << bits_in_this_byte) - 1) << bit_pos
            
            # Extract corresponding bits from raw_value
            value_bits = (raw_value >> (signal.length - bits_remaining)) & ((1 << bits_in_this_byte) - 1)
            
            # Update the byte
            data_array[byte_pos] = (data_array[byte_pos] & ~mask) | (value_bits << bit_pos)
            
            bits_remaining -= bits_in_this_byte
            byte_pos += 1
            bit_pos = 0
    else:
        # BIG ENDIAN 
        # TODO
        pass

def create_message_data(msg_def, signal_values):
    """Create message data bytes from signal values"""
    # Create an array of zeros
    data = bytearray(max(8, msg_def.length))
    
    # Encode each signal
    for signal in msg_def.signals:
        if signal.name in signal_values:
            encode_signal(signal, signal_values[signal.name], data)
    
    return data

def decode_signal(signal, data_array):
    """Decode a signal value from the data bytes"""
    # Get starting byte and bit
    start_byte = signal.start_bit // 8
    start_bit = signal.start_bit % 8
    
    # Extract raw value based on byte order
    raw_value = 0
    
    if signal.byte_order == 1:  # Little endian (Intel)
        byte_pos = start_byte
        bits_remaining = signal.length
        bit_pos = start_bit
        
        while bits_remaining > 0 and byte_pos < len(data_array):
            # How many bits to get from this byte
            bits_in_this_byte = min(8 - bit_pos, bits_remaining)
            
            # Create mask for these bits
            mask = ((1 << bits_in_this_byte) - 1) << bit_pos
            
            # Extract bits
            value_bits = (data_array[byte_pos] & mask) >> bit_pos
            
            # Add to raw value
            raw_value |= value_bits << (signal.length - bits_remaining)
            
            bits_remaining -= bits_in_this_byte
            byte_pos += 1
            bit_pos = 0
    else:
        # Big endian - not implemented in this simplified example
        pass
    
    # Convert raw to physical value
    physical_value = (raw_value * signal.factor) + signal.offset
    
    return physical_value

def decode_message(msg, message_dict):
    """Decode a CAN message based on message definitions"""
    if msg.arbitration_id in message_dict:
        msg_def = message_dict[msg.arbitration_id]
        
        print(f"\nReceived message: ID=0x{msg.arbitration_id:X}, Name={msg_def.name}")
        print(f"Data: {' '.join(f'{b:02X}' for b in msg.data)}")
        print("Decoded signals:")
        
        # Decode each signal
        for signal in msg_def.signals:
            # Only decode signals that fit within the received data
            if (signal.start_bit + signal.length) <= (len(msg.data) * 8):
                value = decode_signal(signal, msg.data)
                unit_str = f" {signal.unit}" if signal.unit else ""
                print(f"  {signal.name}: {value}{unit_str}")
    else:
        print(f"\nReceived unknown message: ID=0x{msg.arbitration_id:X}")
        print(f"Data: {' '.join(f'{b:02X}' for b in msg.data)}")
    
    print("-" * 40)

def main():
    # Create an event for signaling threads to exit
    exit_event = threading.Event()
    
    try:
        # Create sender and receiver threads
        sender_thread = threading.Thread(target=sender, args=(exit_event,))
        receiver_thread = threading.Thread(target=receiver, args=(exit_event,))
        
        # Start the threads
        sender_thread.start()
        receiver_thread.start()
        
        print("CAN message test program running. Press Ctrl+C to exit.")
        
        # Keep the main thread alive
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nExiting program...")
        
        # Signal threads to exit
        exit_event.set()
        
        # Wait for threads to finish
        sender_thread.join(timeout=2.0)
        receiver_thread.join(timeout=2.0)
        
        print("Program terminated")

if __name__ == "__main__":
    main()