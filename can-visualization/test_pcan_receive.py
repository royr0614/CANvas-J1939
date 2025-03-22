import can
import logging
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PCANReceiveTest")

def main():
    try:
        # Initialize the bus for receiving
        logger.info("Initializing PCAN_USBBUS2 for receiving")
        bus = can.interface.Bus(interface='pcan', channel='PCAN_USBBUS2', bitrate=500000)
        
        # Receive messages for 30 seconds
        logger.info("Waiting for messages (30 second timeout)...")
        end_time = time.time() + 30
        
        message_count = 0
        while time.time() < end_time:
            # Try to receive a message with a 1 second timeout
            message = bus.recv(1.0)
            
            if message is not None:
                message_count += 1
                logger.info(f"Received message #{message_count}: ID=0x{message.arbitration_id:X}, data={[hex(b) for b in message.data]}")
            else:
                logger.debug("No message received (timeout)")
        
        if message_count == 0:
            logger.warning("No messages were received in the 30 second window")
        else:
            logger.info(f"Received {message_count} messages successfully")
        
        # Shutdown the bus
        bus.shutdown()
        logger.info("PCAN interface shutdown")
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()