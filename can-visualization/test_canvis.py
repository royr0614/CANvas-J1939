#!/usr/bin/env python3
"""
Test script for CAN visualization system
This script allows testing the system in simulation mode with a specified DBC file
"""

import sys
import os
import argparse
import logging
import time
from PyQt5.QtWidgets import QApplication

# Set up command line arguments
parser = argparse.ArgumentParser(description='Test CAN Data Visualization')
parser.add_argument('--dbc', required=True, help='Path to DBC file for testing')
parser.add_argument('--log', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                   default='INFO', help='Logging level')
args = parser.parse_args()

# Configure logging
logging.basicConfig(
    level=getattr(logging, args.log),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Test")

# Check if DBC file exists
if not os.path.isfile(args.dbc):
    logger.error(f"DBC file not found: {args.dbc}")
    sys.exit(1)

# Add --simulation flag programmatically to sys.argv
if '--simulation' not in sys.argv:
    sys.argv.append('--simulation')

# Import the main application
try:
    from main_app import CANVisApp
    logger.info("Successfully imported the main application")
except ImportError as e:
    logger.error(f"Failed to import the main application: {e}")
    logger.error("Make sure all required modules are installed and in the Python path")
    sys.exit(1)

def main():
    """Run the test"""
    # Start Qt application
    app = QApplication(sys.argv)
    
    # Create main window
    logger.info("Creating main application window")
    window = CANVisApp()
    
    # Give the UI time to initialize
    logger.info("Waiting for UI initialization...")
    time.sleep(1)
    
    # Start CAN in simulation mode
    logger.info("Starting CAN simulation")
    window.start_can()
    
    # Run the application
    logger.info("Test setup complete - running application")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()