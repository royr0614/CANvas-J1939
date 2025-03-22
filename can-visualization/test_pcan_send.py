import can
import time
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PCANTest")

def main():
    try:
        # Initialize the bus
        logger.info("Initializing PCAN_USBBUS1")
        bus = can.interface.Bus(interface='pcan', channel='PCAN_USBBUS1', bitrate=500000)
        
        # Try a simple standard ID message first
        logger.info("Sending standard ID test message")
        std_msg = can.Message(
            arbitration_id=0x100,
            data=[0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08],
            is_extended_id=False
        )
        bus.send(std_msg)
        logger.info("Standard ID message sent successfully")
        
        # Wait a moment
        time.sleep(1)
        
        # J1939 EEC1 message (extended ID)
        logger.info("Sending J1939 EEC1 message")
        eec1_msg = can.Message(
            arbitration_id=0x0CF00400,  # The correct J1939 ID for EEC1
            data=[0, 0, 0, 0x80, 0x7D, 0, 0, 0],  # Engine Speed 4015.9375 RPM
            is_extended_id=True
        )
        bus.send(eec1_msg)
        logger.info("J1939 EEC1 message sent successfully")
        
        # Wait a moment
        time.sleep(1)
        
        # Try with the ID from your application
        logger.info("Sending with application ID")
        app_msg = can.Message(
            arbitration_id=0xCF004FE,  # The ID from your application
            data=[0, 0, 0, 0x80, 0x7D, 0, 0, 0],
            is_extended_id=True
        )
        bus.send(app_msg)
        logger.info("Application ID message sent successfully")
        
        # Shutdown the bus
        bus.shutdown()
        logger.info("PCAN interface shutdown")
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()